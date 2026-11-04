"""Interactive public demonstration for the MC896 clinical NLP project."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from project1.src.interactive_demo import analyze_text, graph_to_dot


EXAMPLE = (
    "The fictional patient reported abdominal pain and nausea. A CT scan of the abdomen "
    "was performed and acute pancreatitis was diagnosed. She received intravenous fluids."
)

ACADEMIC_RESULTS = pd.DataFrame(
    [
        ("Dictionary + rules", 0.1373, 0.0458, 0.0578),
        ("Dictionary + k-NN", 0.1373, 0.0601, 0.0724),
        ("CRF + rules", 0.2415, 0.1078, 0.0941),
        ("CRF + k-NN", 0.2415, 0.1123, 0.1153),
    ],
    columns=["Pipeline", "Entity macro-F1", "Relation macro-F1", "Graph edge micro-F1"],
)


st.set_page_config(page_title="Clinical NLP · MC896", page_icon="🧬", layout="wide")
st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem; padding-bottom: 3rem; max-width: 1280px;}
    [data-testid="stMetric"] {background: #ffffff; border: 1px solid #e2e8f0; padding: .8rem 1rem; border-radius: 14px;}
    [data-testid="stMetric"] * {color: #0f172a !important;}
    .hero {padding: 1.25rem 1.5rem; border-radius: 18px; background: linear-gradient(120deg,#0f172a,#164e63); color: white; margin-bottom: 1rem;}
    .hero h1 {margin: 0; font-size: 2.25rem;}
    .hero p {margin: .45rem 0 0; color: #cbd5e1;}
    .method {display:inline-block; padding:.28rem .65rem; border-radius:999px; background:#ccfbf1; color:#115e59; font-weight:700; font-size:.82rem;}
    </style>
    <div class="hero">
      <span class="method">Dictionary + rules · live inference</span>
      <h1>Clinical text → knowledge graph</h1>
      <p>Explore entity extraction, relation rules and graph construction with fictional English text.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("About this demo")
    st.write("The live path uses the versioned Project 1 vocabularies and deterministic relation rules.")
    st.info("Enter only fictional or public text. Input is processed locally by this application.")
    st.markdown("**Live stages**\n1. Dictionary matching\n2. Rule relations\n3. Knowledge graph")
    st.markdown("**Language:** English  \n**Purpose:** NLP research demonstration")

with st.form("clinical-text"):
    text = st.text_area(
        "Fictional clinical report",
        value=EXAMPLE,
        height=145,
        max_chars=4000,
        help="The vocabularies and reported experiments are in English.",
    )
    submitted = st.form_submit_button("Run pipeline", type="primary", use_container_width=True)

if not text.strip():
    st.warning("Enter a fictional report to run the pipeline.")
    st.stop()

analysis = analyze_text(text)

metric_columns = st.columns(4)
metric_columns[0].metric("Entities", len(analysis.entities))
metric_columns[1].metric("Relations", len(analysis.relations))
metric_columns[2].metric("Graph nodes", len(analysis.nodes))
metric_columns[3].metric("Graph edges", len(analysis.edges))

entities_tab, relations_tab, graph_tab, comparison_tab = st.tabs(
    ["Entities", "Relations", "Knowledge graph", "Experimental comparison"]
)

with entities_tab:
    st.subheader("Extracted entities")
    if analysis.entities:
        st.dataframe(pd.DataFrame(analysis.entities), hide_index=True, width="stretch")
    else:
        st.info("No vocabulary entity was found in this text.")

with relations_tab:
    st.subheader("Rule-based relations")
    if analysis.relations:
        st.dataframe(pd.DataFrame(analysis.relations), hide_index=True, width="stretch")
    else:
        st.info("No relation was generated from the extracted entities.")

with graph_tab:
    st.subheader("Generated knowledge graph")
    if analysis.nodes:
        st.graphviz_chart(graph_to_dot(analysis), width="stretch", height=560)
    else:
        st.info("The graph is empty.")

with comparison_tab:
    st.subheader("Audited academic results")
    st.caption(
        "These scores come from the frozen 63-document external evaluation. They are context for "
        "the project and are not recomputed from the text above."
    )
    st.dataframe(
        ACADEMIC_RESULTS.style.format(precision=4).highlight_max(axis=0, color="#ccfbf1"),
        hide_index=True,
        width="stretch",
    )
    st.bar_chart(ACADEMIC_RESULTS.set_index("Pipeline"), horizontal=True, height=330)

st.caption(
    "Research prototype · The output is not a diagnosis or treatment recommendation. "
    "Dictionary coverage and simple relation rules limit generalization."
)
