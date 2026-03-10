"""
SFE OPS 운영 콘솔 (Streamlit)

실행 방법:
  cd c:\sfe_master_ops
  streamlit run ui/ops_console.py

구성 (탭 5개):
  1. 🏠 대시보드   - 전체 파이프라인 상태 요약
  2. 📂 데이터 투입 - 파일 업로드 (CRM·실적·목표·Prescription)
  3. 🚀 파이프라인  - OPS 평가 실행 및 단계별 결과
  4. 📊 분석 결과  - Sandbox/Territory 결과 시각화
  5. 📄 보고서 생성 - HTML Builder 연동
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import json
import uuid
from datetime import datetime

# ── 페이지 설정 ─────────────────────────────────────────
st.set_page_config(
    page_title="SFE OPS 운영 콘솔",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 커스텀 CSS (라이트 모드 최적화) ────────────────────────
css = """
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
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
    --radius: 16px;
  }
  html, body, [data-testid="stAppViewContainer"], .stMarkdown {
    font-family: 'Inter', -apple-system, sans-serif !important;
    color: var(--text) !important;
  }
  [data-testid="stAppViewContainer"] {
    background:
      radial-gradient(circle at top right, rgba(88,166,255,0.12), transparent 28%),
      radial-gradient(circle at top left, rgba(31,111,235,0.08), transparent 22%),
      var(--bg) !important;
  }
  [data-testid="stHeader"] {
    background: rgba(13,17,23,0.82) !important;
    border-bottom: 1px solid var(--border);
    backdrop-filter: blur(12px);
  }
  [data-testid="stToolbar"] * {
    color: var(--muted) !important;
  }
  [data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(22,27,34,0.98), rgba(13,17,23,0.98)) !important;
    border-right: 1px solid var(--border);
  }
  [data-testid="stSidebarContent"] {
    background: transparent !important;
    padding-top: 8px;
  }
  [data-testid="stSidebar"] * {
    color: var(--text) !important;
  }
  [data-testid="stSidebar"] hr {
    border-top: 1px solid var(--border) !important;
  }
  [data-testid="stSidebar"] .stSelectbox label, 
  [data-testid="stSidebar"] .stMarkdown p {
    color: var(--muted) !important;
  }
  .stTabs [data-baseweb="tab-list"] {
    background: rgba(13,17,23,0.92);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 6px;
    gap: 4px;
  }
  .stTabs [data-baseweb="tab"] {
    color: var(--muted) !important;
    background: transparent !important;
    border-radius: 10px;
    font-weight: 700 !important;
    padding: 10px 16px;
  }
  .stTabs [aria-selected="true"] {
    background: var(--surface2) !important;
    color: var(--text) !important;
    box-shadow: none !important;
    border-bottom: none !important;
  }
  h1, h2, h3, h4, h5, h6 {
    color: var(--text) !important;
    font-weight: 800 !important;
    letter-spacing: -0.4px;
  }
  p, li, label, span, small, div[data-testid="stExpander"] p {
    color: var(--text) !important;
  }
  [data-testid="stMarkdownContainer"] p {
    color: var(--text) !important;
  }
  label[data-testid="stWidgetLabel"] p {
    color: var(--muted) !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-size: 12px !important;
  }
  .stTextInput input,
  .stTextArea textarea,
  .stSelectbox [data-baseweb="select"],
  .stMultiSelect [data-baseweb="select"],
  .stNumberInput input {
    background: var(--surface) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
  }
  .stSelectbox [data-baseweb="select"] {
    box-shadow: none !important;
  }
  .stSelectbox [data-baseweb="select"] > div:first-child,
  .stMultiSelect [data-baseweb="select"] > div:first-child {
    background: var(--surface) !important;
    border-radius: 12px !important;
  }
  .stSelectbox svg,
  .stMultiSelect svg {
    fill: var(--text) !important;
  }
  .stTextInput input,
  .stTextArea textarea,
  .stNumberInput input,
  .stSelectbox input,
  .stMultiSelect input {
    -webkit-text-fill-color: var(--text) !important;
    caret-color: var(--text) !important;
  }
  .stSelectbox [data-baseweb="select"] > div,
  .stMultiSelect [data-baseweb="select"] > div,
  .stSelectbox [data-baseweb="select"] span,
  .stSelectbox [data-baseweb="select"] div,
  .stMultiSelect [data-baseweb="select"] span,
  .stMultiSelect [data-baseweb="select"] div,
  .stSelectbox [data-baseweb="select"] input,
  .stMultiSelect [data-baseweb="select"] input {
    background: var(--surface) !important;
    color: var(--text) !important;
    -webkit-text-fill-color: var(--text) !important;
  }
  .stSelectbox div[data-baseweb="popover"] ul,
  .stMultiSelect div[data-baseweb="popover"] ul,
  div[role="listbox"],
  div[data-baseweb="menu"],
  ul[data-testid="stSelectboxVirtualDropdown"] {
    background: var(--surface) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    box-shadow: 0 12px 32px rgba(0,0,0,0.35) !important;
  }
  div[role="option"],
  li[role="option"] {
    background: var(--surface) !important;
    color: var(--text) !important;
    -webkit-text-fill-color: var(--text) !important;
  }
  div[role="option"]:hover,
  li[role="option"]:hover {
    background: var(--surface2) !important;
  }
  [data-baseweb="popover"] *,
  div[role="listbox"] *,
  li[role="option"] * {
    color: var(--text) !important;
    -webkit-text-fill-color: var(--text) !important;
  }
  .stFileUploader section,
  .stFileUploader section div,
  .stFileUploader button {
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
  .stTextInput input::placeholder,
  .stTextArea textarea::placeholder {
    color: var(--muted) !important;
  }
  .stCheckbox label {
    color: var(--text) !important;
  }
  .stButton button {
    background: var(--surface) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
  }
  .stButton button:hover {
    border-color: var(--primary) !important;
    color: var(--primary) !important;
  }
  .stButton button[kind="primary"] {
    background: linear-gradient(180deg, var(--primary), var(--primary2)) !important;
    color: #ffffff !important;
    border-color: transparent !important;
  }
  div[data-testid="stNotification"] {
    background: var(--surface) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
  }
  div[data-testid="stExpander"] {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
  }
  div[data-testid="stDataFrame"] {
    border: 1px solid var(--border);
    border-radius: 14px;
    overflow: hidden;
  }
  [data-testid="stMetric"] {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 12px 14px;
  }
  .metric-card {
    background: linear-gradient(180deg, rgba(33,38,45,0.92), rgba(22,27,34,0.92));
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 22px 18px;
    text-align: left;
    min-height: 136px;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.03);
  }
  .metric-lbl {
    font-size: 11px;
    color: var(--muted) !important;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-weight: 700;
    margin-bottom: 12px;
  }
  .metric-val {
    font-size: 34px;
    font-weight: 800;
    color: var(--primary) !important;
    line-height: 1.1;
    letter-spacing: -1px;
  }
  .metric-sub {
    margin-top: 10px;
    font-size: 12px;
    color: var(--muted) !important;
  }
  .status-pass { color: var(--success) !important; font-weight: 800; }
  .status-warn { color: var(--warning) !important; font-weight: 800; }
  .status-fail { color: var(--danger) !important; font-weight: 800; }
  .status-skip { color: var(--muted) !important; font-weight: 800; }
  .page-hero {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 16px;
    padding: 24px 28px;
    margin-bottom: 20px;
    background: linear-gradient(135deg, rgba(22,27,34,0.96), rgba(13,17,23,0.96));
    border: 1px solid var(--border);
    border-radius: 20px;
  }
  .hero-kicker {
    font-size: 11px;
    color: var(--primary);
    text-transform: uppercase;
    letter-spacing: 1.1px;
    font-weight: 700;
    margin-bottom: 10px;
  }
  .page-hero h1 {
    margin: 0;
    font-size: 30px;
    line-height: 1.1;
  }
  .page-hero p {
    margin: 10px 0 0;
    color: var(--muted) !important;
    max-width: 720px;
    font-size: 14px;
    line-height: 1.7;
  }
  .app-badge {
    display: inline-flex;
    align-items: center;
    padding: 8px 12px;
    border-radius: 999px;
    background: rgba(88,166,255,0.08);
    border: 1px solid rgba(88,166,255,0.25);
    color: var(--primary) !important;
    font-size: 12px;
    font-weight: 700;
    white-space: nowrap;
  }
  .panel-shell {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 18px 20px;
    margin-bottom: 16px;
  }
  .block-card {
    background: linear-gradient(180deg, rgba(33,38,45,0.98), rgba(22,27,34,0.98));
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 18px 20px;
    margin-bottom: 14px;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.03);
  }
  .block-eyebrow {
    font-size: 10px;
    color: var(--primary);
    text-transform: uppercase;
    letter-spacing: 1px;
    font-weight: 700;
    margin-bottom: 8px;
  }
  .block-card h4 {
    margin: 0 0 8px;
    font-size: 17px;
    color: var(--text) !important;
  }
  .block-card p {
    margin: 0;
    font-size: 13px;
    line-height: 1.65;
    color: var(--muted) !important;
  }
  .stat-strip {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 10px;
    margin: 6px 0 16px;
  }
  .stat-chip {
    background: rgba(88,166,255,0.06);
    border: 1px solid rgba(88,166,255,0.15);
    border-radius: 14px;
    padding: 12px 14px;
  }
  .stat-chip .label {
    font-size: 10px;
    color: var(--muted) !important;
    text-transform: uppercase;
    letter-spacing: .9px;
    font-weight: 700;
    margin-bottom: 6px;
  }
  .stat-chip .value {
    font-size: 15px;
    color: var(--text) !important;
    font-weight: 700;
  }
  .action-note {
    background: rgba(31,111,235,0.08);
    border: 1px solid rgba(88,166,255,0.14);
    border-radius: 14px;
    padding: 12px 14px;
    margin: 8px 0 14px;
    color: var(--muted) !important;
    font-size: 13px;
    line-height: 1.6;
  }
  .tight-gap {
    margin-top: 4px;
    margin-bottom: 10px;
  }
  .panel-header {
    margin-bottom: 12px;
  }
  .panel-header h3 {
    margin: 0 0 6px;
    font-size: 16px;
  }
  .panel-header p {
    margin: 0;
    color: var(--muted) !important;
    font-size: 13px;
    line-height: 1.6;
  }
  .ops-network {
    padding: 18px;
    background: linear-gradient(180deg, rgba(13,17,23,0.65), rgba(22,27,34,0.65));
    border: 1px solid var(--border);
    border-radius: 18px;
  }
  .ops-world {
    display: grid;
    grid-template-columns: 1.15fr 0.5fr 1.3fr 0.5fr 1.15fr;
    gap: 14px;
    align-items: stretch;
  }
  .flow-stage {
    background: linear-gradient(180deg, rgba(33,38,45,0.98), rgba(22,27,34,0.98));
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 18px 16px;
    min-height: 250px;
  }
  .flow-stage .stage-kicker {
    font-size: 10px;
    color: var(--primary);
    text-transform: uppercase;
    letter-spacing: 1px;
    font-weight: 700;
    margin-bottom: 10px;
  }
  .flow-stage .stage-title {
    font-size: 18px;
    font-weight: 800;
    color: var(--text) !important;
    margin-bottom: 12px;
  }
  .flow-stage .stage-copy {
    font-size: 12px;
    color: var(--muted) !important;
    line-height: 1.65;
    margin-bottom: 14px;
  }
  .flow-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .flow-chip {
    background: rgba(88,166,255,0.06);
    border: 1px solid rgba(88,166,255,0.15);
    border-radius: 12px;
    padding: 10px 12px;
  }
  .flow-chip .chip-name {
    font-size: 12px;
    font-weight: 700;
    color: var(--text) !important;
  }
  .flow-chip .chip-meta {
    font-size: 11px;
    color: var(--muted) !important;
    margin-top: 4px;
    line-height: 1.5;
  }
  .flow-arrow {
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--primary) !important;
    font-size: 28px;
    font-weight: 800;
    opacity: 0.9;
  }
  .decision-core {
    background: radial-gradient(circle at center, rgba(88,166,255,0.22), rgba(13,17,23,0.95));
    border: 1px solid rgba(88,166,255,0.35);
    border-radius: 22px;
    padding: 20px 16px;
    min-height: 250px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    text-align: center;
    box-shadow: 0 0 36px rgba(31,111,235,0.14);
  }
  .decision-core .core-icon {
    font-size: 40px;
    margin-bottom: 10px;
  }
  .decision-core .core-title {
    font-size: 20px;
    font-weight: 900;
    color: var(--text) !important;
    margin-bottom: 10px;
  }
  .decision-core .core-copy {
    font-size: 12px;
    color: var(--muted) !important;
    line-height: 1.65;
    margin-bottom: 16px;
  }
  .decision-badges {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: center;
  }
  .decision-badges span {
    padding: 6px 10px;
    border-radius: 999px;
    border: 1px solid rgba(88,166,255,0.18);
    background: rgba(88,166,255,0.08);
    color: var(--text) !important;
    font-size: 11px;
    font-weight: 700;
  }
  .chart-shell {
    background: linear-gradient(180deg, rgba(33,38,45,0.98), rgba(22,27,34,0.98));
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 16px 18px;
    margin-bottom: 16px;
  }
  .chart-shell .shell-title {
    font-size: 14px;
    font-weight: 800;
    color: var(--text) !important;
    margin-bottom: 6px;
  }
  .chart-shell .shell-copy {
    font-size: 12px;
    color: var(--muted) !important;
    margin-bottom: 14px;
    line-height: 1.55;
  }
  .engine-core {
    width: 170px;
    height: 170px;
    margin: 0 auto 18px;
    border-radius: 50%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: radial-gradient(circle at center, rgba(88,166,255,0.22), rgba(13,17,23,0.95));
    border: 1px solid rgba(88,166,255,0.35);
    box-shadow: 0 0 36px rgba(31,111,235,0.18);
  }
  .engine-core .engine-name {
    font-size: 14px;
    font-weight: 800;
    color: var(--text) !important;
    margin-top: 8px;
  }
  .engine-core .engine-sub {
    font-size: 11px;
    color: var(--muted) !important;
    margin-top: 4px;
  }
  .mini-node {
    text-align: center;
    padding: 14px 10px;
    border-radius: 14px;
    background: var(--surface2);
    border: 1px solid var(--border);
    min-height: 98px;
  }
  .mini-node .node-title {
    font-size: 18px;
    margin-bottom: 8px;
  }
  .mini-node .node-name {
    font-size: 11px;
    font-weight: 800;
    color: var(--text) !important;
    letter-spacing: 0.8px;
  }
  .mini-node .node-meta {
    font-size: 10px;
    color: var(--muted) !important;
    margin-top: 6px;
  }
  .connector {
    text-align: center;
    color: var(--primary) !important;
    font-size: 22px;
    margin: 6px 0 12px;
  }
  .step-card {
    background: linear-gradient(180deg, rgba(33,38,45,0.96), rgba(22,27,34,0.96));
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 18px 20px;
    margin-bottom: 12px;
  }
  .step-pass { border-left: 4px solid var(--success); }
  .step-warn { border-left: 4px solid var(--warning); }
  .step-fail { border-left: 4px solid var(--danger); }
  .step-skip { border-left: 4px solid var(--muted); opacity: 0.9; }
  .insight-card {
    background: rgba(88,166,255,0.06);
    border: 1px solid rgba(88,166,255,0.18);
    border-left: 4px solid var(--primary);
    border-radius: 12px;
    padding: 12px 14px;
    margin-bottom: 10px;
  }
  .helper-note {
    color: var(--muted) !important;
    font-size: 12px;
  }
  .sidebar-shell {
    background: linear-gradient(180deg, rgba(33,38,45,0.98), rgba(22,27,34,0.98));
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 18px 16px;
    margin-bottom: 14px;
  }
  .sidebar-kicker {
    font-size: 10px;
    color: var(--primary);
    text-transform: uppercase;
    letter-spacing: 1px;
    font-weight: 700;
    margin-bottom: 8px;
  }
  .sidebar-shell h3 {
    margin: 0 0 6px;
    font-size: 18px;
  }
  .sidebar-shell p {
    margin: 0;
    color: var(--muted) !important;
    font-size: 12px;
    line-height: 1.6;
  }
  .sidebar-status-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .sidebar-status-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    background: rgba(88,166,255,0.05);
    border: 1px solid rgba(88,166,255,0.12);
    border-radius: 12px;
    padding: 10px 12px;
  }
  .sidebar-status-item .name {
    font-size: 12px;
    font-weight: 700;
    color: var(--text) !important;
  }
  .sidebar-status-item .state {
    font-size: 11px;
    color: var(--muted) !important;
    font-weight: 700;
  }
  .sidebar-mini-note {
    font-size: 11px;
    color: var(--muted) !important;
    line-height: 1.6;
  }
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# ── 세션 상태 초기화 ─────────────────────────────────────
if "pipeline_result" not in st.session_state:
    st.session_state.pipeline_result = None
if "uploaded_data" not in st.session_state:
    st.session_state.uploaded_data = {
        "crm": None, "sales": None, "target": None, "prescription": None
    }
if "run_log" not in st.session_state:
    st.session_state.run_log = []
if "module_status" not in st.session_state:
    st.session_state.module_status = {
        "crm": "미실행", "prescription": "미실행",
        "sandbox": "미실행", "territory": "미실행", "builder": "미실행",
    }
if "execution_mode" not in st.session_state:
    st.session_state.execution_mode = "auto_flow"


# ════════════════════════════════════════════════════════
# 유틸 함수
# ════════════════════════════════════════════════════════

def status_badge(status: str) -> str:
    icons = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌", "SKIP": "⏭️", "미실행": "⬜"}
    colors = {"PASS": "status-pass", "WARN": "status-warn", "FAIL": "status-fail", "SKIP": "status-skip", "미실행": "status-na"}
    icon = icons.get(status, "⬜")
    css = colors.get(status, "status-na")
    return f'<span class="{css}">{icon} {status}</span>'


def add_log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    st.session_state.run_log.append(f"[{ts}] {msg}")


def render_page_hero(title: str, subtitle: str, badge: str | None = None):
    badge_html = f'<span class="app-badge">{badge}</span>' if badge else ""
    st.markdown(
        f"""
        <div class="page-hero">
          <div>
            <div class="hero-kicker">SFE MASTER OPS</div>
            <h1>{title}</h1>
            <p>{subtitle}</p>
          </div>
          <div>{badge_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_panel_header(title: str, description: str = ""):
    desc_html = f"<p>{description}</p>" if description else ""
    st.markdown(
        f"""
        <div class="panel-header">
          <h3>{title}</h3>
          {desc_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_block_card(title: str, description: str, eyebrow: str = ""):
    eyebrow_html = f'<div class="block-eyebrow">{eyebrow}</div>' if eyebrow else ""
    st.markdown(
        f"""
        <div class="block-card">
          {eyebrow_html}
          <h4>{title}</h4>
          <p>{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def open_chart_shell(title: str, description: str = ""):
    desc_html = f'<div class="shell-copy">{description}</div>' if description else ""
    st.markdown(
        f"""
        <div class="chart-shell">
          <div class="shell-title">{title}</div>
          {desc_html}
        """,
        unsafe_allow_html=True,
    )


def close_chart_shell():
    st.markdown("</div>", unsafe_allow_html=True)


def get_execution_mode_label(mode: str) -> str:
    labels = {
        "auto_flow": "표준 자동 흐름",
        "include_rx": "Prescription 포함 흐름",
        "minimal_run": "최소 입력 실행",
    }
    return labels.get(mode, mode)


def run_mock_pipeline(execution_mode: str, uploaded: dict) -> dict:
    """
    실제 OPS API가 구동 중일 때는 requests.post("/ops/pipeline/run")을 호출.
    현재는 샘플 결과를 반환하여 UI 동작을 검증한다.
    """
    import time, random
    steps = []
    modules = ["crm", "prescription", "sandbox", "territory", "builder"]
    mode_label = get_execution_mode_label(execution_mode)
    for i, mod in enumerate(modules):
        time.sleep(0.1)
        s = "PASS"
        note = f"✅ {mod} 평가 완료."

        if mod == "crm":
            if uploaded.get("crm") is None:
                if execution_mode == "minimal_run":
                    s = "SKIP"
                    note = "⏭️ CRM 입력 없음 — 최소 입력 실행 모드라 자동 건너뜀."
                else:
                    s = "WARN"
                    note = "⚠️ CRM 입력 없음 — 자동 흐름 기준 보조 정보 없이 진행."
        elif mod == "prescription":
            if uploaded.get("prescription") is None:
                if execution_mode == "include_rx":
                    s = "WARN"
                    note = "⚠️ Prescription 포함 흐름 선택됨 — 하지만 Rx 입력이 없어 분석이 제한됨."
                else:
                    s = "SKIP"
                    note = "⏭️ Prescription 입력 없음 — 현재 흐름에서 자동 제외."
        elif mod == "sandbox":
            has_core = uploaded.get("sales") is not None or uploaded.get("target") is not None
            if not has_core:
                s = "WARN"
                note = "⚠️ 실적/목표 핵심 입력 부족 — 샘플 기준으로 Sandbox 판단 수행."
        elif mod == "territory":
            if execution_mode == "minimal_run":
                s = "SKIP"
                note = "⏭️ 최소 입력 실행 모드 — Territory 최적화는 이번 실행에서 생략."
        elif mod == "builder":
            note = "✅ 최종 결과물 생성 준비 완료."

        steps.append({
            "step": i + 1, "module": mod,
            "status": s, "score": round(random.uniform(70, 98), 1) if s != "SKIP" else 0,
            "reasoning_note": note,
            "next_modules": ["territory"] if mod == "sandbox" and s == "PASS"
                            else ["builder"] if mod == "territory" and s == "PASS" else [],
            "duration_ms": random.randint(20, 150),
        })
    active_scores = [s["score"] for s in steps if s["status"] != "SKIP"]
    overall = "WARN" if any(s["status"] == "WARN" for s in steps) else "PASS"
    return {
        "run_id": str(uuid.uuid4())[:8],
        "execution_mode": execution_mode,
        "execution_mode_label": mode_label,
        "overall_status": overall,
        "overall_score": round(sum(active_scores) / len(active_scores), 1) if active_scores else 0,
        "steps": steps,
        "final_eligible_modules": [m for m in ["territory", "builder"] if not (execution_mode == "minimal_run" and m == "territory")],
        "recommended_actions": [
            "✅ Sandbox 분석 품질 양호 — Territory Handoff 가능",
            "✅ HTML Builder 실행 가능 — 보고서를 생성하세요",
        ],
        "total_duration_ms": sum(s["duration_ms"] for s in steps),
    }


# ════════════════════════════════════════════════════════
# 사이드바
# ════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-shell">
          <div class="sidebar-kicker">SFE MASTER OPS</div>
          <h3>운영 콘솔</h3>
          <p>html_builder와 같은 톤으로 연결되는 컨트롤 허브입니다.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 모듈 상태 패널
    status_rows = []
    for mod, stat in st.session_state.module_status.items():
        icon = {"PASS": "🟢", "WARN": "🟡", "FAIL": "🔴", "SKIP": "⚪", "미실행": "⬜"}.get(stat, "⬜")
        status_rows.append(
            f'<div class="sidebar-status-item"><span class="name">{icon} {mod.upper()}</span><span class="state">{stat}</span></div>'
        )
    st.markdown(
        f"""
        <div class="sidebar-shell">
          <div class="sidebar-kicker">Module Status</div>
          <h3>실행 상태</h3>
          <div class="sidebar-status-list">
            {''.join(status_rows)}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 시나리오 선택
    st.markdown(
        """
        <div class="sidebar-shell">
          <div class="sidebar-kicker">Run Control</div>
          <h3>실행 모드</h3>
          <p>고정 시나리오 대신, 데이터 상태에 따라 어떻게 흐를지 기준만 정합니다.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    execution_mode = st.selectbox(
        "실행 모드",
        ["auto_flow", "include_rx", "minimal_run"],
        format_func=get_execution_mode_label,
        label_visibility="collapsed"
    )
    st.session_state.execution_mode = execution_mode

    st.markdown(
        f"""
        <div class="sidebar-shell">
          <div class="sidebar-kicker">Recent Activity</div>
          <div class="sidebar-mini-note">최근 실행: {'없음' if not st.session_state.run_log else st.session_state.run_log[-1][:20]}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ════════════════════════════════════════════════════════
# 메인 탭
# ════════════════════════════════════════════════════════

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🧭 OPS 관제 허브",
    "🗂️ 데이터 어댑터",
    "⚡ 엔진 실행 센터",
    "📈 분석 인텔리전스",
    "🛠️ 결과물 빌더",
])


# ────────────────────────────────────────────────────────
# TAB 1: 대시보드
# ────────────────────────────────────────────────────────
with tab1:
    render_page_hero(
        "SFE OPS 엔진 가동 지표",
        "html_builder의 다크 콘솔 톤을 그대로 가져와, 운영 상태와 전략 흐름이 한눈에 들어오도록 재구성한 메인 대시보드입니다.",
        "LIVE CONSOLE",
    )

    result = st.session_state.pipeline_result

    # KPI 요약 카드
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""<div class="metric-card">
          <div class="metric-lbl">전략적 정확성</div>
          <div class="metric-val">{result['overall_score'] if result else '—'}</div>
          <div class="metric-sub">전체 파이프라인 평균 점수</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        status = result['overall_status'] if result else 'READY'
        icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}.get(status, "⬜")
        st.markdown(f"""<div class="metric-card">
          <div class="metric-lbl">엔진 상태</div>
          <div class="metric-val" style="font-size: 28px;">{icon} {status}</div>
          <div class="metric-sub">최신 실행 결과 기준</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        n_pass = sum(1 for s in (result['steps'] if result else []) if s['status'] == "PASS")
        st.markdown(f"""<div class="metric-card">
          <div class="metric-lbl">검증 통과 모듈</div>
          <div class="metric-val">{n_pass}/5</div>
          <div class="metric-sub">핸드오프 가능한 단계 수</div>
        </div>""", unsafe_allow_html=True)
    with col4:
        dur = f"{result['total_duration_ms']}ms" if result else "—"
        st.markdown(f"""<div class="metric-card">
          <div class="metric-lbl">엔진 응답 속도</div>
          <div class="metric-val">{dur}</div>
          <div class="metric-sub">전체 파이프라인 수행 시간</div>
        </div>""", unsafe_allow_html=True)

    render_panel_header(
        "SFE 전략 피드백 루프",
        "실제 OPS 흐름에 맞춰 입력, 정규화, 샌드박스 판단, 산출물 핸드오프 단계로 다시 구성했습니다.",
    )
    st.markdown(
        """
        <div class="ops-network">
          <div class="ops-world">
            <div class="flow-stage">
              <div class="stage-kicker">Stage 01</div>
              <div class="stage-title">Data Intake</div>
              <div class="stage-copy">현장 데이터와 시스템 데이터를 먼저 어댑터가 수집합니다.</div>
              <div class="flow-list">
                <div class="flow-chip"><div class="chip-name">CRM 활동</div><div class="chip-meta">방문, 디테일링, 담당자 실행 로그</div></div>
                <div class="flow-chip"><div class="chip-name">실적 / 목표</div><div class="chip-meta">매출 기준과 목표 기준을 함께 확보</div></div>
                <div class="flow-chip"><div class="chip-name">Prescription</div><div class="chip-meta">선택 입력, 흐름 연결 검증 강화</div></div>
              </div>
            </div>
            <div class="flow-arrow">→</div>
            <div class="decision-core">
              <div class="core-icon">🔬</div>
              <div class="core-title">Sandbox Decision Engine</div>
              <div class="core-copy">정규화된 데이터를 검증하고, 점수와 이유를 만든 뒤 다음 모듈 핸드오프 여부를 결정합니다.</div>
              <div class="decision-badges">
                <span>Normalize</span>
                <span>Scoring</span>
                <span>Handoff</span>
              </div>
            </div>
            <div class="flow-arrow">→</div>
            <div class="flow-stage">
              <div class="stage-kicker">Stage 03</div>
              <div class="stage-title">Operational Outputs</div>
              <div class="stage-copy">판단 결과가 권역 최적화와 최종 결과물 생성으로 이어집니다.</div>
              <div class="flow-list">
                <div class="flow-chip"><div class="chip-name">Territory</div><div class="chip-meta">권역 성과, 미커버 병원, 방문 재배치</div></div>
                <div class="flow-chip"><div class="chip-name">Builder</div><div class="chip-meta">HTML 보고서와 WebSlide 결과물 생성</div></div>
                <div class="flow-chip"><div class="chip-name">Feedback Loop</div><div class="chip-meta">결과 확인 후 다시 입력 품질을 보강</div></div>
              </div>
            </div>
          </div>
          <div class="helper-note" style="text-align:center; margin-top:18px;">
            입력 데이터가 Sandbox를 거쳐 Territory와 Builder로 전달되고, 결과가 다시 입력 품질 개선으로 연결되는 OPS 루프입니다.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if result and result.get("recommended_actions"):
        render_panel_header("AI 기반 운영 최적화 제언")
        for action in result["recommended_actions"]:
            st.markdown(f"""
            <div class="insight-card">
                <span>{action}</span>
            </div>""", unsafe_allow_html=True)


# ────────────────────────────────────────────────────────
# TAB 2: 데이터 투입
# ────────────────────────────────────────────────────────
with tab2:
    render_page_hero(
        "원천 데이터 투입",
        "업로드 화면도 html_builder처럼 모듈 패널 중심으로 보이도록 정리했습니다. 실제 기능은 그대로이고 화면 톤만 운영 콘솔답게 맞췄습니다.",
        "DATA ADAPTER",
    )
    render_panel_header("업로드 워크스페이스", "CRM, 실적, 목표, Prescription 파일을 받아 표준 구조로 정리합니다.")
    loaded_count = sum(1 for v in st.session_state.uploaded_data.values() if v is not None)
    st.markdown(
        f"""
        <div class="stat-strip">
          <div class="stat-chip"><div class="label">Loaded Modules</div><div class="value">{loaded_count} / 4</div></div>
          <div class="stat-chip"><div class="label">Adapter Mode</div><div class="value">Standard Normalize</div></div>
          <div class="stat-chip"><div class="label">Input Status</div><div class="value">{'Ready' if loaded_count else 'Waiting for files'}</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_l, col_r = st.columns(2)

    with col_l:
        render_block_card("🏥 CRM 활동 데이터", "영업 활동 로그를 올리면 병원/담당자 기준으로 표준화합니다.", "Input Block 01")
        crm_file = st.file_uploader("CRM 파일 (CSV, XLSX)", type=["csv", "xlsx"], key="crm_up")
        if crm_file:
            try:
                df = pd.read_csv(crm_file) if crm_file.name.endswith(".csv") else pd.read_excel(crm_file)
                st.session_state.uploaded_data["crm"] = df.to_dict("records")
                st.success(f"✅ {len(df)}건 로드 완료")
                st.dataframe(df.head(3), use_container_width=True)
                add_log(f"CRM 데이터 {len(df)}건 업로드")
            except Exception as e:
                st.error(f"파일 읽기 오류: {e}")

        render_block_card("📈 실적(매출) 데이터", "매출 파일을 불러와 샌드박스 분석과 목표 대비 비교에 사용합니다.", "Input Block 02")
        sales_file = st.file_uploader("실적 파일 (CSV, XLSX)", type=["csv", "xlsx"], key="sales_up")
        if sales_file:
            try:
                df = pd.read_csv(sales_file) if sales_file.name.endswith(".csv") else pd.read_excel(sales_file)
                st.session_state.uploaded_data["sales"] = df.to_dict("records")
                st.success(f"✅ {len(df)}건 로드 완료")
                st.dataframe(df.head(3), use_container_width=True)
                add_log(f"실적 데이터 {len(df)}건 업로드")
            except Exception as e:
                st.error(f"파일 읽기 오류: {e}")

    with col_r:
        render_block_card("🎯 목표 데이터", "목표 수치 파일을 넣으면 달성률 계산과 경고 기준점으로 사용합니다.", "Input Block 03")
        target_file = st.file_uploader("목표 파일 (CSV, XLSX)", type=["csv", "xlsx"], key="target_up")
        if target_file:
            try:
                df = pd.read_csv(target_file) if target_file.name.endswith(".csv") else pd.read_excel(target_file)
                st.session_state.uploaded_data["target"] = df.to_dict("records")
                st.success(f"✅ {len(df)}건 로드 완료")
                st.dataframe(df.head(3), use_container_width=True)
                add_log(f"목표 데이터 {len(df)}건 업로드")
            except Exception as e:
                st.error(f"파일 읽기 오류: {e}")

        render_block_card("💊 Prescription 데이터", "선택 입력입니다. 흐름 분석이 필요한 경우에만 추가합니다.", "Optional Block")
        rx_file = st.file_uploader("Prescription 파일 (CSV, XLSX)", type=["csv", "xlsx"], key="rx_up")
        if rx_file:
            try:
                df = pd.read_csv(rx_file) if rx_file.name.endswith(".csv") else pd.read_excel(rx_file)
                st.session_state.uploaded_data["prescription"] = df.to_dict("records")
                st.success(f"✅ {len(df)}건 로드 완료")
                st.dataframe(df.head(3), use_container_width=True)
                add_log(f"Prescription 데이터 {len(df)}건 업로드")
            except Exception as e:
                st.error(f"파일 읽기 오류: {e}")

    render_panel_header("컬럼 매핑", "업로드한 파일의 컬럼 이름이 표준과 다를 때 여기서 맞춥니다.")
    st.markdown(
        '<div class="action-note">업로드 파일의 컬럼명이 다르더라도 여기서 이름만 맞추면 파이프라인 로직은 그대로 사용할 수 있습니다.</div>',
        unsafe_allow_html=True,
    )
    with st.expander("실적 데이터 컬럼 매핑"):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.text_input("병원 ID 컬럼", value="hospital_id", key="sales_hosp_col")
            st.text_input("병원명 컬럼 (대체용)", value="hospital_name", key="sales_name_col")
        with c2:
            st.text_input("제품 ID 컬럼", value="product_id", key="sales_prod_col")
            st.text_input("금액 컬럼", value="sales_amount", key="sales_amt_col")
        with c3:
            st.text_input("월 컬럼 (YYYYMM)", value="yyyymm", key="sales_month_col")
            st.text_input("담당자 ID 컬럼", value="rep_id", key="sales_rep_col")

    # 업로드 현황 요약
    render_panel_header("투입 현황")
    status_data = {
        "모듈": ["CRM", "실적", "목표", "Prescription"],
        "상태": [
            "✅ 업로드됨" if st.session_state.uploaded_data["crm"] else "⬜ 대기",
            "✅ 업로드됨" if st.session_state.uploaded_data["sales"] else "⬜ 대기",
            "✅ 업로드됨" if st.session_state.uploaded_data["target"] else "⬜ 대기",
            "✅ 업로드됨" if st.session_state.uploaded_data["prescription"] else "⬜ 선택사항",
        ],
        "건수": [
            len(st.session_state.uploaded_data["crm"]) if st.session_state.uploaded_data["crm"] else 0,
            len(st.session_state.uploaded_data["sales"]) if st.session_state.uploaded_data["sales"] else 0,
            len(st.session_state.uploaded_data["target"]) if st.session_state.uploaded_data["target"] else 0,
            len(st.session_state.uploaded_data["prescription"]) if st.session_state.uploaded_data["prescription"] else 0,
        ],
    }
    st.dataframe(pd.DataFrame(status_data), use_container_width=True, hide_index=True)


# ────────────────────────────────────────────────────────
# TAB 3: 파이프라인 실행
# ────────────────────────────────────────────────────────
with tab3:
    render_page_hero(
        "OPS 파이프라인 실행",
        "어떤 시나리오로 엔진을 돌릴지 정하고, 단계별 평가 결과를 같은 콘솔 룩으로 확인할 수 있게 정리했습니다.",
        "ENGINE RUN",
    )

    uploaded = st.session_state.uploaded_data
    ready = [k for k, v in uploaded.items() if v is not None]
    st.markdown(
        f"""
        <div class="stat-strip">
          <div class="stat-chip"><div class="label">Execution Mode</div><div class="value">{get_execution_mode_label(st.session_state.get('execution_mode', 'auto_flow'))}</div></div>
          <div class="stat-chip"><div class="label">Input Modules</div><div class="value">{len(ready)} active</div></div>
          <div class="stat-chip"><div class="label">Engine State</div><div class="value">{'Ready to run' if ready else 'Sample mode available'}</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_run, col_opt = st.columns([2, 1])
    with col_opt:
        render_block_card("실행 옵션", "실패 시 중단 여부와 시작 스텝을 먼저 정합니다.", "Control")
        stop_on_fail = st.checkbox("FAIL 시 즉시 중단", value=True)
        start_from = st.selectbox("시작 STEP", [1, 2, 3, 4, 5], index=0)

    with col_run:
        render_block_card(
            "실행 준비 상태",
            f"현재 실행 모드는 {get_execution_mode_label(st.session_state.get('execution_mode', 'auto_flow'))} 입니다. 투입 데이터는 {', '.join(ready) if ready else '없음 (샘플 데이터로 실행)'} 상태입니다.",
            "Run Context",
        )

    col_btn1, col_btn2, _ = st.columns([1, 1, 2])
    with col_btn1:
        run_btn = st.button("🚀 파이프라인 실행", type="primary", use_container_width=True)
    with col_btn2:
        reset_btn = st.button("🔄 초기화", use_container_width=True)

    if reset_btn:
        st.session_state.pipeline_result = None
        st.session_state.run_log = []
        for k in st.session_state.module_status:
            st.session_state.module_status[k] = "미실행"
        st.rerun()

    if run_btn:
        with st.spinner("OPS 파이프라인 실행 중..."):
            add_log(f"파이프라인 시작 — 실행 모드: {get_execution_mode_label(st.session_state.get('execution_mode', 'auto_flow'))}")
            result = run_mock_pipeline(
                execution_mode=st.session_state.get("execution_mode", "auto_flow"),
                uploaded=uploaded,
            )
            st.session_state.pipeline_result = result
            for step in result["steps"]:
                st.session_state.module_status[step["module"]] = step["status"]
                add_log(f"STEP {step['step']} [{step['module']}] → {step['status']} ({step['score']:.0f}점)")
            add_log(f"파이프라인 완료 — 전체: {result['overall_status']}")

        st.success(f"✅ 파이프라인 완료 — 전체 상태: **{result['overall_status']}** (점수: {result['overall_score']})")

    # 단계별 결과 표시
    result = st.session_state.pipeline_result
    if result:
        render_panel_header("단계별 평가 결과")
        st.markdown(
            '<div class="action-note">각 단계 카드는 html_builder의 리포트 카드처럼 상태가 분리되어 보이도록 간격과 경계선을 더 강하게 주었습니다.</div>',
            unsafe_allow_html=True,
        )
        for step in result["steps"]:
            s = step["status"]
            css = {"PASS": "step-pass", "WARN": "step-warn", "FAIL": "step-fail", "SKIP": "step-skip"}.get(s, "step-skip")
            icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌", "SKIP": "⏭️"}.get(s, "⬜")
            dur = step.get("duration_ms", 0)
            st.markdown(f"""
            <div class="step-card {css}">
              <strong>STEP {step['step']} — {step['module'].upper()}</strong>
              <span style="float:right;color:#6e7681;font-size:12px">{dur}ms</span><br>
              <small>{icon} {step['reasoning_note']}</small>
            </div>""", unsafe_allow_html=True)

        if result.get("recommended_actions"):
            render_panel_header("권고사항")
            for a in result["recommended_actions"]:
                st.info(a)

        if result.get("final_eligible_modules"):
            render_panel_header("Handoff 가능한 모듈")
            st.markdown(" · ".join([f"**{m}**" for m in result["final_eligible_modules"]]))

    # 실행 로그
    render_panel_header("실행 로그", "최근 로그 30개를 접어서 볼 수 있게 유지했습니다.")
    with st.expander("📋 실행 로그"):
        for log in reversed(st.session_state.run_log[-30:]):
            st.markdown(f"`{log}`")


# ────────────────────────────────────────────────────────
# TAB 4: 분석 결과
# ────────────────────────────────────────────────────────
with tab4:
    render_page_hero(
        "분석 결과 시각화",
        "샌드박스와 권역 분석 결과를 하나의 다크 콘솔 안에서 보도록 맞췄습니다. 자세한 지도 렌더링은 html_builder에서 이어집니다.",
        "ANALYTICS",
    )

    result = st.session_state.pipeline_result
    if not result:
        st.info("먼저 파이프라인을 실행하세요.")
    else:
        sub1, sub2 = st.tabs(["📈 Sandbox 분석", "🗺️ Territory 지도"])

        with sub1:
            render_panel_header("Sandbox 분석 결과", "차트와 표를 모두 같은 패널 언어로 묶어 읽기 쉽게 정리했습니다.")
            # 샘플 차트 데이터
            chart_data = pd.DataFrame({
                "병원": ["H001", "H002", "H003", "H004", "H005"],
                "매출": [7300000, 2900000, 8700000, 1800000, 950000],
                "목표": [8200000, 3500000, 10200000, 2000000, 1200000],
                "달성률(%)": [89.0, 82.9, 85.3, 90.0, 79.2],
            })
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                open_chart_shell("병원별 매출 vs 목표", "어느 병원에서 목표 대비 차이가 나는지 바로 보는 비교 차트입니다.")
                st.bar_chart(chart_data.set_index("병원")[["매출", "목표"]])
                close_chart_shell()
            with col_c2:
                open_chart_shell("병원별 달성률(%)", "위험 병원을 빠르게 찾기 좋은 성과 집중 차트입니다.")
                st.bar_chart(chart_data.set_index("병원")["달성률(%)"])
                close_chart_shell()

            open_chart_shell("상세 데이터", "차트 아래에서 병원별 수치를 그대로 비교하는 표입니다.")
            st.dataframe(chart_data, use_container_width=True, hide_index=True)
            close_chart_shell()

            # KPI 요약
            render_panel_header("KPI 요약")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("총 매출", "2,215만원")
            c2.metric("평균 달성률", "85.3%", delta="-4.7%p (목표 대비)")
            c3.metric("분석 병원", "6개")
            c4.metric("조인율", "83%")

        with sub2:
            render_panel_header("Territory 지도 결과", "지도 전 단계의 권역 성과를 패널 단위로 먼저 확인할 수 있게 맞췄습니다.")
            st.caption("실제 지도는 HTML Builder(ui/html_builder.html)에서 Leaflet으로 렌더링됩니다.")

            region_data = pd.DataFrame({
                "권역": ["서울", "부산", "인천"],
                "병원수": [2, 2, 2],
                "총 매출": [10200000, 10500000, 1450000],
                "평균 달성률(%)": [85.9, 87.7, 39.6],
                "방문수": [22, 18, 7],
                "담당자": ["REP001", "REP002", "REP003"],
            })
            c1, c2 = st.columns(2)
            with c1:
                open_chart_shell("권역별 매출", "권역별 매출 규모를 먼저 비교하는 운영용 차트입니다.")
                st.bar_chart(region_data.set_index("권역")["총 매출"])
                close_chart_shell()
            with c2:
                open_chart_shell("권역별 달성률(%)", "성과 대비 위험 권역을 파악하기 쉬운 차트입니다.")
                st.bar_chart(region_data.set_index("권역")["평균 달성률(%)"])
                close_chart_shell()

            open_chart_shell("권역 상세 데이터", "권역, 담당자, 방문 수를 함께 확인하는 운영 표입니다.")
            st.dataframe(region_data, use_container_width=True, hide_index=True)
            close_chart_shell()

            # 미커버 알림
            st.warning("⚠️ 미커버 병원 감지: H006 (인천) — 방문 0건, 담당자 미지정")


# ────────────────────────────────────────────────────────
# TAB 5: 보고서 생성
# ────────────────────────────────────────────────────────
with tab5:
    render_page_hero(
        "HTML 보고서 & WebSlide 생성",
        "html_builder와 가장 직접적으로 이어지는 탭이라, 같은 제품처럼 느껴지도록 액션 중심 화면으로 맞췄습니다.",
        "BUILDER HANDOFF",
    )

    result = st.session_state.pipeline_result
    builder_eligible = result and "builder" in result.get("final_eligible_modules", [])

    if not builder_eligible:
        st.warning("파이프라인 실행 후 Builder Handoff 조건을 충족해야 합니다.")
    else:
        st.markdown(
            """
            <div class="stat-strip">
              <div class="stat-chip"><div class="label">Builder Handoff</div><div class="value">Enabled</div></div>
              <div class="stat-chip"><div class="label">Output Modes</div><div class="value">HTML Report / WebSlide</div></div>
              <div class="stat-chip"><div class="label">Design Link</div><div class="value">Synced with html_builder</div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    col_r1, col_r2 = st.columns(2)

    with col_r1:
        render_block_card("📊 OPS 분석 보고서", "Sandbox/Territory/CRM 결과를 정리된 HTML 리포트로 내보내는 블록입니다.", "Output Block 01")

        report_type = st.selectbox(
            "보고서 유형",
            ["Sandbox 성과 분석", "Territory 지도 보고서", "CRM 활동 보고서", "통합 전체 보고서"]
        )
        report_period = st.text_input("기간", value="2025년 1~2월")
        st.markdown('<div class="action-note">리포트 유형과 기간만 정하면, 실제 최종 스타일은 html_builder에서 이어집니다.</div>', unsafe_allow_html=True)

        if st.button("📊 OPS 보고서 생성", disabled=not builder_eligible, use_container_width=True):
            st.success(f"✅ '{report_type}' HTML 보고서가 생성되었습니다.")
            st.info("📂 `ui/html_builder.html`을 브라우저에서 열어 보고서를 확인하고 다운로드하세요.")
            add_log(f"OPS 보고서 생성: {report_type} ({report_period})")

    with col_r2:
        render_block_card("🎨 WebSlide 슬라이드 제작", "분석 결과를 발표용 슬라이드 구조로 넘기는 블록입니다.", "Output Block 02")

        slide_theme = st.selectbox(
            "테마 선택",
            ["B | Enterprise Swiss (권장)", "A | Signature Premium", "D | Analytical Dashboard", "E | Deep Tech Dark"]
        )
        slide_content = st.text_area(
            "슬라이드 내용 (또는 비워두면 분석 결과 자동 사용)",
            height=100,
            placeholder="발표에 포함할 핵심 메시지나 내용을 입력하세요..."
        )
        st.markdown('<div class="action-note">테마만 고르면 슬라이드 HTML은 html_builder 쪽 시각 언어와 연결됩니다.</div>', unsafe_allow_html=True)

        if st.button("🎨 WebSlide 생성", disabled=not builder_eligible, use_container_width=True):
            st.success("✅ WebSlide Blueprint를 생성했습니다. HTML Builder에서 최종 슬라이드를 확인하세요.")
            add_log(f"WebSlide 생성: 테마 {slide_theme[:1]}")

    render_panel_header("HTML Builder 실행", "브라우저에서 직접 여는 별도 빌더 화면입니다. 위 디자인과 같은 계열 톤으로 연결됩니다.")
    st.markdown(
        '<div class="action-note">이 영역은 최종 결과물로 이동하는 마지막 액션 블록입니다. 경로 확인 후 바로 브라우저에서 열 수 있습니다.</div>',
        unsafe_allow_html=True,
    )
    builder_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "html_builder.html")
    )
    st.markdown(f"""
    HTML Builder는 브라우저에서 직접 실행하는 도구입니다.

    **경로**: `{builder_path}`

    아래 버튼을 클릭하거나 브라우저에서 직접 열어주세요.
    """)

    if st.button("🌐 HTML Builder 열기", use_container_width=False):
        import subprocess
        subprocess.Popen(["start", builder_path], shell=True)
        st.info("브라우저에서 HTML Builder가 열립니다.")
