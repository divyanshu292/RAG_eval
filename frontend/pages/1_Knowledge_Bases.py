import streamlit as st
from lib.api import create_knowledge_base, list_knowledge_bases, delete_knowledge_base

st.set_page_config(page_title="Knowledge Bases", layout="wide")
st.title("Knowledge Bases")

# Create new KB
with st.expander("Create New Knowledge Base", expanded=True):
    with st.form("create_kb"):
        name = st.text_input("Name")
        description = st.text_area("Description (optional)")
        submitted = st.form_submit_button("Create")
        if submitted and name:
            try:
                kb = create_knowledge_base(name, description)
                st.success(f"Created: **{kb['name']}**")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to create: {e}")

st.divider()

# List KBs
st.subheader("Your Knowledge Bases")

try:
    kbs = list_knowledge_bases()
except Exception:
    kbs = []
    st.error("Could not connect to backend. Is it running?")

if not kbs:
    st.info("No knowledge bases yet. Create one above.")
else:
    for kb in kbs:
        col1, col2, col3 = st.columns([4, 2, 1])
        with col1:
            st.markdown(f"**{kb['name']}**")
            if kb.get("description"):
                st.caption(kb["description"])
        with col2:
            st.metric("Documents", kb.get("document_count", 0))
        with col3:
            if st.button("Delete", key=f"del_{kb['id']}"):
                try:
                    delete_knowledge_base(kb["id"])
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
        st.divider()

# Store selected KB in session
if kbs:
    st.sidebar.subheader("Select Knowledge Base")
    kb_options = {kb["name"]: kb["id"] for kb in kbs}
    selected = st.sidebar.selectbox("Knowledge Base", list(kb_options.keys()))
    if selected:
        st.session_state["selected_kb_id"] = kb_options[selected]
        st.session_state["selected_kb_name"] = selected
