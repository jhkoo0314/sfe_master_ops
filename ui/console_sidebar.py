import streamlit as st

from ui.console_shared import (
    get_active_company_key,
    get_active_company_name,
    get_execution_mode_description,
    get_execution_mode_label,
    get_execution_mode_modules,
    get_execution_mode_requirements,
)


def render_sidebar() -> None:
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

        company_key = st.text_input("회사 코드", value=get_active_company_key(), help="예: hangyeol_pharma, demo_company")
        company_name = st.text_input("회사 이름", value=get_active_company_name(), help="화면과 이력에 표시할 이름입니다.")
        st.session_state.company_key = company_key.strip() or "default_company"
        st.session_state.company_name = company_name.strip() or st.session_state.company_key

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
            """
            <div class="sidebar-shell">
              <div class="sidebar-kicker">Run Control</div>
              <h3>실행 모드</h3>
              <p>지금 넣은 데이터 묶음에 맞춰, 어느 수준까지 엔진을 기대할지 정하는 메뉴입니다.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        execution_mode = st.selectbox(
            "실행 모드",
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
