import streamlit as st
from lib.api import query_knowledge_base, list_knowledge_bases

st.set_page_config(page_title="Chat", layout="wide")
st.title("Chat")

# KB selector
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

# Chat history per KB
history_key = f"chat_history_{kb_id}"
if history_key not in st.session_state:
    st.session_state[history_key] = []

# Display chat history
for msg in st.session_state[history_key]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and "evaluation" in msg:
            ev = msg["evaluation"]
            cols = st.columns(3)
            cols[0].metric("Relevance", f"{ev['retrieval_relevance']:.2f}")
            cols[1].metric("Faithfulness", f"{ev['answer_faithfulness']:.2f}")
            cols[2].metric("Hallucination", f"{ev['hallucination_score']:.2f}")

# Chat input
if question := st.chat_input("Ask a question about your documents..."):
    # Show user message
    st.session_state[history_key].append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    # Query backend
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                result = query_knowledge_base(kb_id, question)
                answer = result["answer"]
                evaluation = result["evaluation"]

                st.markdown(answer)
                cols = st.columns(3)
                cols[0].metric("Relevance", f"{evaluation['retrieval_relevance']:.2f}")
                cols[1].metric("Faithfulness", f"{evaluation['answer_faithfulness']:.2f}")
                cols[2].metric("Hallucination", f"{evaluation['hallucination_score']:.2f}")

                st.caption(f"Latency: {result['latency_ms']}ms")

                st.session_state[history_key].append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "evaluation": evaluation,
                    }
                )
            except Exception as e:
                st.error(f"Query failed: {e}")
