import os
from dotenv import load_dotenv
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.llms.gemini import Gemini
from llama_index.core import StorageContext, VectorStoreIndex, Settings, Document
import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.chat_engine import CondenseQuestionChatEngine
from llama_index.core.node_parser import SentenceSplitter
import fitz
from typing import List
from system_prompt import SYSTEM_PROMPT
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.query_engine import RouterQueryEngine
import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

load_dotenv()
api_key = os.getenv("GEMINI_API")
os.environ["GOOGLE_API_KEY"] = str(api_key)

Settings.embed_model = GeminiEmbedding(model_name="models/text-embedding-004")
Settings.llm = Gemini(model_name="models/gemini-2.0-flash")

class Chatbot:
    def __init__(self) -> None:
        self.reset()
        self.chunk_size=800
        self.chunk_overlap=120
        self.documents = []
        self.nodes = []
        self.index = None
        self.chat_engine = None
        self.client = None

    def upload_pdfs(self, files: List):
        for file in files:
            filename = getattr(file, "name", "unknown.pdf")
            try:
                file.seek(0)
                doc = fitz.open(stream=file.read(), filetype="pdf")
            except Exception as e:
                print(f"❌ Could not open {filename}: {e}")
                continue

            for page_num, page in enumerate(doc.pages(), start=1):
                text = page.get_text().strip()

                # ✅ Fallback to OCR if no text found
                if not text or len(text.strip()) < 10:
                    print(f"🖼️ Running OCR on page {page_num} of {filename}...")
                    try:
                        pix = page.get_pixmap(dpi=300)
                        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                        text = pytesseract.image_to_string(img)
                    except Exception as ocr_error:
                        print(f"⚠️ OCR failed on page {page_num} of {filename}: {ocr_error}")
                        continue

                if text.strip():
                    document = Document(
                        text=text.strip(),
                        metadata={
                            "filename": filename,
                            "page": page_num
                        }
                    )
                    self.documents.append(document)

        self.chunking()
        return f"✅ Uploaded {len(self.documents)} pages from {len(files)} files."
    
    def chunking(self):
        splitter = SentenceSplitter(chunk_size=800, chunk_overlap=120)
        nodes = splitter.get_nodes_from_documents(documents=self.documents)
        
        self.nodes = nodes
        self.store_in_memory()
        
    def store_in_memory(self):
        client = chromadb.EphemeralClient()
        chroma_collection = client.get_or_create_collection("user_session")
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        index = VectorStoreIndex(self.nodes, storage_context=storage_context)
        
        self.client = client
        self.index = index
        self.get_chat_engine(self.index)
        
    def get_chat_engine(self, index):
        vector_tool = QueryEngineTool(
            index.as_query_engine(similarity_top_k=5),
            metadata= ToolMetadata(
                name = "vector search",
                description= "useful for searching specific facts"
            )
        )
        
        summary_tool = QueryEngineTool(
            index.as_query_engine(response_mode="tree_summarize"),
            metadata= ToolMetadata(
                name = "summary",
                description= "useful for summarizing whole document"
            )
        )
        
        router_engine = RouterQueryEngine.from_defaults(
            [vector_tool, summary_tool], select_multi = True
        )
        
        chat_engine = CondenseQuestionChatEngine.from_defaults(
            query_engine=  router_engine,
            memory= ChatMemoryBuffer(token_limit=1000)
        )
        
        self.chat_engine = chat_engine
        
    def chat(self, question: str):
        if self.chat_engine is None:
            print("❌ chat_engine is None. Did you call store_in_memory() after chunking?")
            print(f"📄 Documents: {len(self.documents)} | 🧩 Nodes: {len(self.nodes)} | 📦 Index: {self.index}")
            raise RuntimeError("Chat engine not initialized.")
        
        question = self.rewrite_if_vague(question)
        
        # Step 1: Let chat engine generate the context-aware query & retrieve answer
        raw_response = self.chat_engine.chat(question)
        
        # Step 2: Inject your system prompt only in final generation prompt
        response_prompt = f"{SYSTEM_PROMPT}\n\nQuestion: {question}\n\nContext:\n{raw_response}\n\nAnswer:"
        
        # Step 3: Rerun just the generation step manually with your LLM
        llm_response = Settings.llm.complete(response_prompt)
        
        return llm_response.text
    
    def rewrite_if_vague(self, question: str) -> str:
        question_lower = question.strip().lower()
        vague_summaries = {"give summary", "summary", "summarize", "tell me the summary"}

        if question_lower in vague_summaries and self.documents:
            # Extract unique document names
            filenames = list(set(
                doc.metadata.get("filename", "a document") for doc in self.documents
            ))

            # Format filenames into a bullet list or comma-separated string
            file_list = ", ".join(f"'{name}'" for name in filenames)

            # Return a more specific query
            return f"Give a combined summary of the following topics: {file_list}"

        return question
    
    def reset(self):
        print("🔁 Resetting Chatbot state...")
        if hasattr(self, "client") and self.client:
            try:
                self.client.delete_collection("user_session")
            except Exception as e:
                print(f"⚠️ Failed to clear vector store: {e}")
        
        self.documents = []
        self.nodes = []
        self.index = None
        self.chat_engine = None
        self.client = None

