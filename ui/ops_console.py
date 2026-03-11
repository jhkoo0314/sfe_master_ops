"""
SFE OPS 운영 콘솔 (Streamlit)

실행 방법:
  cd c:\\sfe_master_ops
  streamlit run ui/ops_console.py
"""

import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.console_state import init_console_state
from ui.console_sidebar import render_sidebar
from ui.console_tabs import (
    render_artifacts_tab,
    render_builder_tab,
    render_dashboard_tab,
    render_pipeline_tab,
    render_upload_tab,
)


st.set_page_config(
    page_title="SFE OPS 운영 콘솔",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

css = """
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded" rel="stylesheet">
<style>
  :root {
    --bg: #0d1117;
    --surface: #161b22;
    --surface2: #21262d;
    --border: #30363d;
    --text: #e6edf3;
    --muted: #8b949e;
    --primary: #58a6ff;
    --primary2: #1f6feb;
    --success: #3fb950;
    --warning: #d29922;
    --danger: #f85149;
  }
  html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
  }
  body, p, div, span, label, li, input, textarea, button, select, h1, h2, h3, h4, h5, h6 {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
  }
  .material-symbols-rounded,
  [class*="material-symbols"],
  [data-testid="stExpander"] summary span[data-testid="stIconMaterial"],
  [data-testid="stExpander"] summary .material-symbols-rounded {
    font-family: 'Material Symbols Rounded' !important;
    font-weight: normal !important;
    font-style: normal !important;
    letter-spacing: normal !important;
    text-transform: none !important;
    display: inline-block !important;
    white-space: nowrap !important;
    word-wrap: normal !important;
    direction: ltr !important;
    -webkit-font-smoothing: antialiased !important;
  }
  [data-testid="stHeader"] {
    background: rgba(13,17,23,0.85) !important;
    border-bottom: 1px solid var(--border);
  }
  [data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(22,27,34,0.98), rgba(13,17,23,0.98)) !important;
    border-right: 1px solid var(--border);
  }
  [data-testid="stSidebar"] * {
    color: var(--text) !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
  }
  .stTabs [data-baseweb="tab-list"] {
    background: rgba(13,17,23,0.92);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 8px 10px;
    gap: 10px;
  }
  .stTabs [data-baseweb="tab"] {
    color: var(--muted) !important;
    border-radius: 10px;
    font-weight: 700 !important;
    padding: 12px 18px !important;
  }
  .stTabs [aria-selected="true"] {
    background: var(--surface2) !important;
    color: var(--text) !important;
  }
  .stButton button,
  .stDownloadButton button,
  .stTextInput input,
  .stSelectbox [data-baseweb="select"] {
    background: var(--surface) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
  }
  .stSelectbox,
  .stSelectbox > div,
  .stSelectbox div[data-baseweb="select"],
  .stSelectbox div[data-baseweb="select"] > div,
  [data-testid="stSidebar"] .stSelectbox,
  [data-testid="stSidebar"] .stSelectbox > div,
  [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"],
  [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div {
    background: var(--surface) !important;
    border-color: var(--border) !important;
  }
  .stFileUploader section,
  .stFileUploader section > div,
  .stFileUploader [data-testid="stFileUploaderDropzone"],
  .stFileUploader [data-testid="stFileUploaderDropzoneInstructions"],
  .stFileUploader [data-testid="stFileUploaderDropzone"] * {
    background: var(--surface) !important;
    color: var(--text) !important;
    border-color: var(--border) !important;
  }
  .stFileUploader small,
  .stFileUploader label,
  .stFileUploader span,
  .stFileUploader p {
    color: var(--muted) !important;
  }
  .stFileUploader button {
    background: var(--surface2) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
  }
  .stSelectbox [data-baseweb="select"] > div,
  .stSelectbox [data-baseweb="select"] span,
  .stSelectbox [data-baseweb="select"] input,
  .stSelectbox [data-baseweb="select"] svg,
  .stSelectbox div[data-baseweb="select"] * ,
  [data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] > div,
  [data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] span,
  [data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] input,
  [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] * {
    color: var(--text) !important;
    fill: var(--text) !important;
    -webkit-text-fill-color: var(--text) !important;
    opacity: 1 !important;
    background: transparent !important;
  }
  div[role="listbox"],
  div[data-baseweb="popover"],
  div[role="option"],
  li[role="option"],
  [data-baseweb="popover"] * {
    background: var(--surface) !important;
    color: var(--text) !important;
    -webkit-text-fill-color: var(--text) !important;
  }
  div[role="option"]:hover,
  li[role="option"]:hover {
    background: var(--surface2) !important;
  }
  div[data-testid="stExpander"],
  div[data-testid="stDataFrame"],
  [data-testid="stMetric"] {
    border: 1px solid var(--border);
    border-radius: 14px;
    overflow: hidden;
  }
  .page-hero,
  .sidebar-shell,
  .block-card,
  .metric-card,
  .insight-card,
  .step-card,
  .stat-chip {
    background: linear-gradient(180deg, rgba(33,38,45,0.92), rgba(22,27,34,0.92));
    border: 1px solid var(--border);
    border-radius: 16px;
  }
  .page-hero {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 20px;
    padding: 24px;
    margin-bottom: 16px;
  }
  .page-hero h1,
  .panel-header h3,
  .block-card h4,
  .sidebar-shell h3 {
    color: var(--text) !important;
    margin: 0 0 8px 0;
  }
  .hero-kicker,
  .sidebar-kicker,
  .block-eyebrow {
    color: var(--primary) !important;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }
  .page-hero p,
  .panel-header p,
  .block-card p,
  .sidebar-shell p,
  .sidebar-mini-note,
  .helper-note,
  .action-note {
    color: var(--muted) !important;
    line-height: 1.6;
  }
  label[data-testid="stWidgetLabel"] p,
  label[data-testid="stWidgetLabel"] span,
  .stSelectbox label,
  .stTextInput label {
    color: var(--primary) !important;
    font-weight: 700 !important;
  }
  .app-badge,
  .decision-badges span {
    display: inline-flex;
    align-items: center;
    padding: 6px 10px;
    border-radius: 999px;
    background: rgba(88,166,255,0.12);
    color: var(--primary) !important;
    font-size: 12px;
    font-weight: 800;
  }
  .panel-header {
    margin: 18px 0 12px 0;
  }
  .block-card,
  .sidebar-shell,
  .metric-card,
  .insight-card,
  .step-card {
    padding: 16px;
  }
  .metric-lbl,
  .label {
    color: var(--muted) !important;
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
  }
  .metric-val,
  .value {
    color: var(--text) !important;
    font-size: 28px;
    font-weight: 800;
  }
  .metric-sub {
    color: var(--muted) !important;
    font-size: 12px;
  }
  .stat-strip {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 10px;
    margin-bottom: 16px;
  }
  .stat-chip {
    padding: 14px;
  }
  .sidebar-status-list {
    display: grid;
    gap: 8px;
  }
  .sidebar-status-item {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    color: var(--text) !important;
    font-size: 13px;
  }
  .ops-network {
    padding: 18px;
    border: 1px solid var(--border);
    border-radius: 18px;
    background: linear-gradient(180deg, rgba(22,27,34,0.92), rgba(13,17,23,0.92));
  }
  .ops-world {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr) auto minmax(0, 1fr);
    gap: 14px;
    align-items: center;
  }
  .flow-stage,
  .decision-core {
    min-height: 240px;
    padding: 18px;
    border: 1px solid var(--border);
    border-radius: 18px;
    background: rgba(22,27,34,0.92);
  }
  .flow-arrow {
    color: var(--primary) !important;
    font-size: 24px;
    font-weight: 800;
  }
  .stage-kicker {
    color: var(--primary) !important;
    font-size: 11px;
    font-weight: 800;
    text-transform: uppercase;
  }
  .stage-title,
  .core-title,
  .chip-name {
    color: var(--text) !important;
    font-size: 18px;
    font-weight: 800;
  }
  .stage-copy,
  .core-copy,
  .chip-meta {
    color: var(--muted) !important;
    font-size: 12px;
    line-height: 1.6;
  }
  .flow-list {
    display: grid;
    gap: 10px;
    margin-top: 14px;
  }
  .flow-chip {
    padding: 12px;
    border: 1px solid var(--border);
    border-radius: 14px;
    background: rgba(33,38,45,0.92);
  }
  .decision-core {
    text-align: center;
    background: radial-gradient(circle at center, rgba(88,166,255,0.16), rgba(13,17,23,0.95));
  }
  .decision-badges {
    display: flex;
    justify-content: center;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 12px;
  }
  .action-note {
    margin: 10px 0 16px 0;
    padding: 12px 14px;
    border-radius: 12px;
    border: 1px solid var(--border);
    background: rgba(22,27,34,0.92);
  }
  .step-pass { border-left: 4px solid var(--success); }
  .step-warn { border-left: 4px solid var(--warning); }
  .step-fail { border-left: 4px solid var(--danger); }
  .step-skip { border-left: 4px solid var(--muted); }
  @media (max-width: 1100px) {
    .ops-world {
      grid-template-columns: 1fr;
    }
    .flow-arrow {
      display: none;
    }
    .page-hero {
      flex-direction: column;
    }
  }
</style>
"""

st.markdown(css, unsafe_allow_html=True)

init_console_state()
render_sidebar()

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "🏠 대시보드",
        "📂 데이터 어댑터",
        "🚀 파이프라인",
        "📊 분석 인텔리전스",
        "📄 결과물 빌더",
    ]
)

with tab1:
    render_dashboard_tab()

with tab2:
    render_upload_tab()

with tab3:
    render_pipeline_tab()

with tab4:
    render_artifacts_tab()

with tab5:
    render_builder_tab()
