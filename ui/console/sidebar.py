import streamlit as st

from common.company_registry import (
    find_company_by_name,
    list_registered_companies,
    register_company,
)
from modules.validation.workflow.execution_registry import (
    get_execution_mode_description,
    get_execution_mode_label,
    get_execution_mode_modules,
    get_execution_mode_requirements,
)
from ui.console.paths import get_active_company_key, get_project_root


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("<h3 style='margin:0 0 8px 0; color: var(--primary) !important;'>RUN control</h3>", unsafe_allow_html=True)
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

        project_root = get_project_root()
        companies = list_registered_companies(project_root)
        company_keys = [item.company_key for item in companies]
        current_key = st.session_state.get("company_key", get_active_company_key()).strip()
        default_index = company_keys.index(current_key) if current_key in company_keys else 0

        def _company_label(company_key: str) -> str:
            for item in companies:
                if item.company_key == company_key:
                    return f"{item.company_name} ({item.company_key})"
            return company_key

        company_options = company_keys if company_keys else [""]
        selected_company_key = st.selectbox(
            "회사 선택",
            company_options,
            index=default_index if company_keys else 0,
            format_func=_company_label,
            disabled=not bool(company_keys),
        )

        selected_company = next((item for item in companies if item.company_key == selected_company_key), None)
        if selected_company is not None:
            st.session_state.company_key = selected_company.company_key
            st.session_state.company_name = selected_company.company_name
            st.markdown(
                f"""
                <div class="selected-company-note">
                  <div><span class="label">선택 회사</span> {selected_company.company_name}</div>
                  <div><span class="label">고정 key</span> <span class="value">{selected_company.company_key}</span></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.session_state.company_key = ""
            st.session_state.company_name = ""

        with st.expander("신규 회사 등록", expanded=False):
            if "register_company_name" not in st.session_state:
                st.session_state.register_company_name = ""
            if "register_company_code_external" not in st.session_state:
                st.session_state.register_company_code_external = ""

            register_name = st.text_input(
                "회사 이름",
                key="register_company_name",
                help="예: 지원제약",
            )
            register_external_code = st.text_input(
                "외부 회사 코드(선택)",
                key="register_company_code_external",
                help="기존 업무 코드가 있으면 저장합니다.",
            )
            if st.button("회사 등록", use_container_width=True):
                try:
                    existing = find_company_by_name(project_root, register_name)
                    entry = existing or register_company(
                        project_root,
                        register_name,
                        company_code_external=register_external_code,
                    )
                    st.session_state.company_key = entry.company_key
                    st.session_state.company_name = entry.company_name
                    st.session_state.register_company_name = ""
                    st.session_state.register_company_code_external = ""
                    st.success(f"등록 완료: {entry.company_name} ({entry.company_key})")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

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
