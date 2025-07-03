# 📚 Dynamic RAG PDF Chatbot 🤖

This is a Streamlit-based AI chatbot that allows you to upload one or more PDF files and ask questions about them using **Retrieval-Augmented Generation (RAG)** powered by **Google Gemini API**.

✅ Extracts content from both text-based and scanned (image-based) PDFs using OCR  
✅ Dynamically loads documents and queries them using semantic search  
✅ Summarizes documents or retrieves facts using a multi-tool LLM pipeline  
✅ Deployable on [Render](https://render.com) with free hosting

---

## 🔗 Live Demo

👉 [Launch App on Render](https://dynamic-rag-pdfs.onrender.com)

---

## 🚀 Features

- 📄 Upload multiple PDFs (total size up to 200MB)
- 🧠 Extracts text using PyMuPDF and OCR fallback with Tesseract
- 🧩 Chunks documents and indexes them in ChromaDB
- 🔎 Semantic search using Gemini embeddings
- 🗂️ Summarization and fact-based querying via Gemini LLM
- 💬 Conversational memory included
- 🌐 Deployable with `render.yaml`

---

## 🛠️ Installation (Local)

### 1. Clone the repository

```bash
git clone https://github.com/Faiq-Ali10/Dynamic-RAG-PDFs-Chatbot.git
cd dynamic-rag-pdf-chatbot
