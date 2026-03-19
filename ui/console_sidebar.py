import streamlit as st

from ops_core.workflow.execution_registry import (
    get_execution_mode_description,
    get_execution_mode_label,
    get_execution_mode_modules,
    get_execution_mode_requirements,
)
from ui.console_paths import get_active_company_key, get_active_company_name


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("<h3 style='margin:0 0 8px 0; color: var(--primary) !important;'>RUN control</h3>", unsafe_allow_html=True)
        execution_mode = st.selectbox(
            "",
            [
                "crm_to_sandbox",
                "crm_to_territory",
                "sandbox_to_html",
                "sandbox_to_territory",
                "crm_to_pdf",
                "crm_to_sandbox_to_territory",
                "integrated_full",
            ],
            format_func=get_execution_mode_label,
            label_visibility="collapsed",
        )
        st.session_state.execution_mode = execution_mode

        if "sidebar_company_key" not in st.session_state:
            st.session_state.sidebar_company_key = get_active_company_key()
        if "sidebar_company_name" not in st.session_state:
            st.session_state.sidebar_company_name = get_active_company_name()

        company_key = st.text_input(
            "회사 코드",
            key="sidebar_company_key",
            help="예: hangyeol_pharma, demo_company",
        )
        company_name = st.text_input(
            "회사 이름",
            key="sidebar_company_name",
            help="화면과 이력에 표시할 이름입니다.",
        )
        st.session_state.company_key = company_key.strip()
        st.session_state.company_name = company_name.strip()

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

        st.markdown(
            f"""
            <div class="sidebar-shell">
              <div class="sidebar-kicker">Mode Guide</div>
              <h3>{get_execution_mode_label(execution_mode)}</h3>
              <p>{get_execution_mode_description(execution_mode)}</p>
              <div class="sidebar-mini-note" style="margin-top:8px">기준: {get_execution_mode_requirements(execution_mode)}</div>
              <div class="sidebar-mini-note" style="margin-top:8px">실행 단계: {' -> '.join(get_execution_mode_modules(execution_mode)).upper()}</div>
             
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div class="sidebar-shell">
              <div class="sidebar-kicker">Recent Activity</div>
              <div class="sidebar-mini-note">최근 실행: {'없음' if not st.session_state.run_log else st.session_state.run_log[-1][:20]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
