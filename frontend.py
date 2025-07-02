import streamlit as st
from chatbot import Chatbot

# 🧠 Create the chatbot once per session
if "chatbot" not in st.session_state:
    st.session_state.chatbot = Chatbot()

chatbot = st.session_state.chatbot

# Page Config
st.set_page_config(page_title="Document Q&A Assistant", layout="wide")
st.title("📚 Chat with Your PDF")

# Sidebar Upload
st.sidebar.header("📂 Upload PDFs")
uploaded_files = st.sidebar.file_uploader(
    "Upload one or more PDF files (Max total size: 200 MB)",
    type=["pdf"],
    accept_multiple_files=True
)

# ✅ File size limit check
MAX_SIZE_MB = 200
if uploaded_files:
    total_size_mb = sum(file.size for file in uploaded_files) / (1024 * 1024)

    if total_size_mb > MAX_SIZE_MB:
        st.sidebar.error(f"🚫 Total file size exceeds {MAX_SIZE_MB} MB. Uploaded: {total_size_mb:.2f} MB")
    elif "pdfs_uploaded" not in st.session_state:
        with st.spinner("🔄 Processing uploaded documents..."):
            upload_message = chatbot.upload_pdfs(uploaded_files)
            st.sidebar.success(upload_message)
            st.session_state.pdfs_uploaded = True
        st.sidebar.success("✅ Ready to chat!")

# Chat Interface
if chatbot.chat_engine is not None:
    st.markdown("### 🤖 Ask something about your uploaded PDFs")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "last_question" not in st.session_state:
        st.session_state.last_question = ""

    # Chat input box
    user_input = st.text_input("Your question:", key="user_input")

    # Trigger if user presses Enter or clicks the button
    ask_triggered = st.button("Ask") or (
        user_input and user_input != st.session_state.last_question
    )

    if ask_triggered and user_input:
        st.session_state.last_question = user_input
        with st.spinner("💡 Thinking..."):
            try:
                response = chatbot.chat(user_input)
                st.session_state.chat_history.append(("You", user_input))
                st.session_state.chat_history.append(("Assistant", response))
            except Exception as e:
                st.error(f"❌ Error: {e}")

    # Display chat history
    for sender, message in st.session_state.chat_history:
        icon = "🧑" if sender == "You" else "🤖"
        st.markdown(f"**{icon} {sender}:** {message}")
else:
    st.info("👈 Upload one or more PDFs to start chatting.")

if st.sidebar.button("🔁 Reset Session"):
    if "chatbot" in st.session_state:
        st.session_state.chatbot.reset()  
    st.session_state.clear()            
    st.rerun()                         

