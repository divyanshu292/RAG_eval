import streamlit as st
import plotly.graph_objects as go

from lib.api import get_analytics, get_query_history, list_knowledge_bases

st.set_page_config(page_title="Analytics", layout="wide")
st.title("Analytics")

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

# Summary metrics
try:
    analytics = get_analytics(kb_id)
except Exception:
    st.error("Could not load analytics.")
    st.stop()

st.subheader("Summary")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Queries", analytics.get("total_queries", 0))
col2.metric("Avg Relevance", f"{analytics.get('avg_retrieval_relevance', 0):.3f}")
col3.metric("Avg Faithfulness", f"{analytics.get('avg_answer_faithfulness', 0):.3f}")
col4.metric("Avg Hallucination", f"{analytics.get('avg_hallucination_score', 0):.3f}")
col5.metric("Avg Latency", f"{analytics.get('avg_latency_ms', 0):.0f}ms")

st.divider()

# Query history with trends
st.subheader("Query History")

try:
    queries = get_query_history(kb_id)
except Exception:
    queries = []

if not queries:
    st.info("No queries yet. Go to the Chat page to ask questions.")
    st.stop()

# Trend chart
relevance_scores = [q["evaluation"]["retrieval_relevance"] for q in reversed(queries)]
faithfulness_scores = [q["evaluation"]["answer_faithfulness"] for q in reversed(queries)]
hallucination_scores = [q["evaluation"]["hallucination_score"] for q in reversed(queries)]
query_indices = list(range(1, len(queries) + 1))

fig = go.Figure()
fig.add_trace(go.Scatter(x=query_indices, y=relevance_scores, mode="lines+markers", name="Retrieval Relevance"))
fig.add_trace(go.Scatter(x=query_indices, y=faithfulness_scores, mode="lines+markers", name="Answer Faithfulness"))
fig.add_trace(go.Scatter(x=query_indices, y=hallucination_scores, mode="lines+markers", name="Hallucination Score"))
fig.update_layout(
    title="Evaluation Metrics Over Queries",
    xaxis_title="Query #",
    yaxis_title="Score (0-1)",
    yaxis=dict(range=[0, 1.05]),
    height=400,
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# Query detail table
st.subheader("Recent Queries")
for q in queries[:20]:
    with st.expander(f"Q: {q['question'][:80]}..."):
        st.markdown(f"**Answer:** {q['answer']}")
        cols = st.columns(4)
        cols[0].metric("Relevance", f"{q['evaluation']['retrieval_relevance']:.3f}")
        cols[1].metric("Faithfulness", f"{q['evaluation']['answer_faithfulness']:.3f}")
        cols[2].metric("Hallucination", f"{q['evaluation']['hallucination_score']:.3f}")
        cols[3].metric("Latency", f"{q['latency_ms']}ms")
