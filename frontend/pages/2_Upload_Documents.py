import time

import streamlit as st
from lib.api import upload_document, list_documents, delete_document, list_knowledge_bases

st.set_page_config(page_title="Upload Documents", layout="wide")
st.title("Upload Documents")

# KB selector in sidebar
try:
    kbs = list_knowledge_bases()
except Exception:
    kbs = []

if not kbs:
    st.warning("Create a knowledge base first.")
    st.stop()

kb_options = {kb["name"]: kb["id"] for kb in kbs}
selected_name = st.sidebar.selectbox("Knowledge Base", list(kb_options.keys()))
kb_id = kb_options[selected_name]
st.session_state["selected_kb_id"] = kb_id
st.session_state["selected_kb_name"] = selected_name

st.subheader(f"Upload to: {selected_name}")

# File uploader
uploaded_files = st.file_uploader(
    "Choose files (PDF, DOCX, TXT)",
    type=["pdf", "docx", "txt"],
    accept_multiple_files=True,
)

if uploaded_files:
    if st.button("Upload All"):
        progress = st.progress(0)
        for i, file in enumerate(uploaded_files):
            try:
                upload_document(kb_id, file)
                st.success(f"Uploaded: {file.name}")
            except Exception as e:
                st.error(f"Failed to upload {file.name}: {e}")
            progress.progress((i + 1) / len(uploaded_files))
        time.sleep(1)
        st.rerun()

st.divider()

# Document list
st.subheader("Documents")
try:
    docs = list_documents(kb_id)
except Exception:
    docs = []

if not docs:
    st.info("No documents uploaded yet.")
else:
    for doc in docs:
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        with col1:
            st.markdown(f"**{doc['filename']}**")
        with col2:
            status = doc.get("status", "unknown")
            color = {"ready": "green", "processing": "orange", "failed": "red"}.get(status, "gray")
            st.markdown(f":{color}[{status}]")
        with col3:
            st.caption(f"{doc.get('chunk_count', 0)} chunks")
        with col4:
            if st.button("Delete", key=f"deldoc_{doc['id']}"):
                try:
                    delete_document(doc["id"])
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
