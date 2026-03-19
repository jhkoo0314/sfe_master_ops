import pandas as pd
import streamlit as st

from ui.console.display import render_page_hero, render_panel_header, render_upload_row
from ui.console.paths import get_active_company_name, get_source_target_display_path
from ui.console.runner import get_crm_package_status


def render_upload_tab() -> None:
    company_name = get_active_company_name()
    render_page_hero(
        "RAW 데이터 투입",
        f"{company_name} 원천 데이터를 회사별 폴더에 연결합니다. 검증 단계에서는 항목명, 짧은 설명, 업로드창을 한 줄에 두고 필요한 예시만 펼쳐서 봅니다.",
        "DATA ADAPTER",
    )
    render_panel_header("업로드 목록", "실행할 흐름에 필요한 원천 파일만 올리면 됩니다. 같은 파일을 여러 항목에 써도 됩니다.")
    crm_status = get_crm_package_status(st.session_state.uploaded_data)
    loaded_count = sum(1 for v in st.session_state.uploaded_data.values() if v is not None)
    st.markdown(
        f"""
        <div class="stat-strip">
          <div class="stat-chip"><div class="label">Loaded Files</div><div class="value">{loaded_count} / 7</div></div>
          <div class="stat-chip"><div class="label">Adapter Mode</div><div class="value">Standard Normalize</div></div>
          <div class="stat-chip"><div class="label">CRM Package</div><div class="value">{crm_status['package_count']} / 4</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="action-note">원본 추출 파일 우선 · 중복 업로드 허용 · 자세한 설명은 각 항목의 예시에서 확인</div>', unsafe_allow_html=True)

    render_panel_header("CRM 패키지", f"필수 2개, 권장 1개, 선택 1개 구조입니다. 현재 상태: {'필수 준비 완료' if crm_status['required_ready'] else '필수 미완성'}")
    render_upload_row("crm_activity", "crm_activity_up", "CRM 활동 원본", "필수", "방문, 디테일, 통화 같은 활동 로그", get_source_target_display_path("crm_activity"), ["방문일, 담당자명 또는 담당자ID", "방문기관명, 기관코드, 주소 중 하나 이상", "활동유형(방문, 디테일, 미팅 등)"], ["월별 합계보다 활동 한 줄 한 줄이 남아 있는 원본이 좋습니다.", "가공 요약표보다 시스템 추출 원본이 더 적합합니다."], "CRM 활동 업로드")
    render_upload_row("crm_rep_master", "crm_rep_master_up", "담당자 / 조직 마스터", "필수", "담당자, 지점, 팀 기준 파일", get_source_target_display_path("crm_rep_master"), ["담당자 ID, 담당자명", "지점명, 팀명, 조직코드", "직무 또는 역할"], ["CRM 활동 파일과 연결하려면 담당자 코드가 살아 있는 편이 좋습니다."], "담당자 마스터 업로드")
    render_upload_row("crm_account_assignment", "crm_assignment_up", "거래처 / 병원 담당 배정", "권장", "병원과 담당자를 연결하는 파일", get_source_target_display_path("crm_account_assignment"), ["병원코드 또는 거래처코드", "병원명 또는 거래처명", "담당자 ID 또는 담당자명"], ["있으면 CRM 연결 정확도가 높아집니다."], "담당 배정 업로드")
    render_upload_row("crm_rules", "crm_rules_up", "CRM 규칙 / KPI 설정", "선택", "방문 인정 기준과 KPI 규칙", get_source_target_display_path("crm_rules"), ["방문 점수 규칙", "활동 유형별 가중치", "월별 KPI 기준"], ["없으면 기본 규칙으로도 검증은 가능합니다."], "CRM 규칙 업로드")

    render_panel_header("Sandbox 입력")
    render_upload_row("sales", "sales_up", "실적(매출) 데이터", "필수", "병원/거래처 단위 매출 원본", get_source_target_display_path("sales"), ["거래처코드 또는 병원코드", "품목코드 또는 품목명", "매출금액, 매출월 또는 매출일"], ["지점별 합계보다 거래처 단위 원본이 좋습니다."], "실적 파일 업로드")
    render_upload_row("target", "target_up", "목표 데이터", "필수", "목표 금액이나 목표 수량 파일", get_source_target_display_path("target"), ["월 목표 또는 분기 목표", "담당자 ID/이름, 병원코드, 품목 중 일부", "목표금액 또는 목표수량"], ["실적과 비교할 수 있게 기간 컬럼이 있으면 좋습니다."], "목표 파일 업로드")

    render_panel_header("Prescription 입력")
    render_upload_row("prescription", "rx_up", "Prescription 데이터", "선택", "도매 -> 약국 흐름을 추적하는 출고 파일", get_source_target_display_path("prescription"), ["출고일, 도매상명, 약국명", "품목명 또는 SKU", "수량, 출고금액, 공급금액"], ["PDF 흐름 추적이 필요할 때만 사용합니다."], "Prescription 파일 업로드")

    render_panel_header("고급 설정", "기본적으로는 어댑터가 자동 정규화를 시도합니다. 이 영역은 정말 예외적인 컬럼명 차이가 있을 때만 사용합니다.")
    with st.expander("고급 설정: 컬럼 매핑", expanded=False):
        st.markdown('<div class="action-note">현재 검증 단계에서는 대부분 입력하지 않아도 됩니다. 실제 회사 파일 컬럼명이 표준과 크게 다를 때만 수동으로 조정하세요.</div>', unsafe_allow_html=True)
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

    render_panel_header("투입 현황")
    status_data = {
        "입력 묶음": ["CRM 활동 원본", "담당자/조직 마스터", "거래처 담당 배정", "CRM 규칙/KPI", "실적", "목표", "Prescription"],
        "상태": [
            "✅ 업로드됨" if st.session_state.uploaded_data["crm_activity"] else "⬜ 필수",
            "✅ 업로드됨" if st.session_state.uploaded_data["crm_rep_master"] else "⬜ 필수",
            "✅ 업로드됨" if st.session_state.uploaded_data["crm_account_assignment"] else "⬜ 권장",
            "✅ 업로드됨" if st.session_state.uploaded_data["crm_rules"] else "⬜ 선택",
            "✅ 업로드됨" if st.session_state.uploaded_data["sales"] else "⬜ 대기",
            "✅ 업로드됨" if st.session_state.uploaded_data["target"] else "⬜ 대기",
            "✅ 업로드됨" if st.session_state.uploaded_data["prescription"] else "⬜ 선택사항",
        ],
        "건수": [
            st.session_state.uploaded_data["crm_activity"]["row_count"] if st.session_state.uploaded_data["crm_activity"] else 0,
            st.session_state.uploaded_data["crm_rep_master"]["row_count"] if st.session_state.uploaded_data["crm_rep_master"] else 0,
            st.session_state.uploaded_data["crm_account_assignment"]["row_count"] if st.session_state.uploaded_data["crm_account_assignment"] else 0,
            st.session_state.uploaded_data["crm_rules"]["row_count"] if st.session_state.uploaded_data["crm_rules"] else 0,
            st.session_state.uploaded_data["sales"]["row_count"] if st.session_state.uploaded_data["sales"] else 0,
            st.session_state.uploaded_data["target"]["row_count"] if st.session_state.uploaded_data["target"] else 0,
            st.session_state.uploaded_data["prescription"]["row_count"] if st.session_state.uploaded_data["prescription"] else 0,
        ],
    }
    st.dataframe(pd.DataFrame(status_data), use_container_width=True, hide_index=True)


__all__ = ["render_upload_tab"]
