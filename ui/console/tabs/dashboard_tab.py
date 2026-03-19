from textwrap import dedent

import streamlit as st

from ui.console.display import render_page_hero, render_panel_header


def render_dashboard_tab() -> None:
    render_page_hero(
        "Sales Data OS Console",
        "입력부터 KPI 계산, 검증, 인텔리전스, 렌더링까지 이어지는 전체 흐름을 한 화면에서 점검합니다.",
    )
    result = st.session_state.pipeline_result

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""<div class="metric-card"><div class="metric-lbl">전체 품질 점수</div><div class="metric-val">{result['overall_score'] if result else '—'}</div><div class="metric-sub">현재 실행 흐름의 평균 평가</div></div>""", unsafe_allow_html=True)
    with col2:
        status = result["overall_status"] if result else "READY"
        icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}.get(status, "⬜")
        st.markdown(f"""<div class="metric-card"><div class="metric-lbl">플랫폼 상태</div><div class="metric-val" style="font-size: 28px;">{icon} {status}</div><div class="metric-sub">최근 실행 결과 기준</div></div>""", unsafe_allow_html=True)
    with col3:
        steps = result["steps"] if result else []
        active_steps = [s for s in steps if s.get("status") != "SKIP"]
        n_pass = sum(1 for s in active_steps if s.get("status") == "PASS")
        st.markdown(f"""<div class="metric-card"><div class="metric-lbl">통과 단계</div><div class="metric-val">{n_pass}/{len(active_steps) if active_steps else '—'}</div><div class="metric-sub">실행 대상 단계 기준</div></div>""", unsafe_allow_html=True)
    with col4:
        dur = f"{result['total_duration_ms']}ms" if result else "—"
        st.markdown(f"""<div class="metric-card"><div class="metric-lbl">총 실행 시간</div><div class="metric-val">{dur}</div><div class="metric-sub">현재 선택 흐름 전체 시간</div></div>""", unsafe_allow_html=True)

    render_panel_header(
        "Sales Data OS 레이어 흐름",
        "Data Layer → Adapter Layer → Core Engine Layer → Validation Layer → Intelligence Layer → Presentation Layer 흐름을 한 화면에서 확인합니다.",
    )
    flow_html = dedent(
        """
        <div class="os-flow-shell">
          <div class="os-flow-grid">
            <div class="os-flow-row row-top">
              <div class="os-layer-card layer-data">
                <div class="os-layer-step">L1</div>
                <div class="os-layer-title">Data Layer</div>
                <div class="os-layer-copy">CRM / Sales / Target / Prescription 원천 데이터 집합</div>
                <div class="os-layer-tags"><span>Raw</span><span>Source</span></div>
              </div>
              <div class="os-layer-link">&rarr;</div>
              <div class="os-layer-card layer-adapter">
                <div class="os-layer-step">L2</div>
                <div class="os-layer-title">Adapter Layer</div>
                <div class="os-layer-copy">원천 컬럼을 표준 스키마로 정렬하고 의미를 보존</div>
                <div class="os-layer-tags"><span>Normalize</span><span>Standard</span></div>
              </div>
              <div class="os-layer-link">&rarr;</div>
              <div class="os-layer-card layer-kpi">
                <div class="os-layer-step">L3</div>
                <div class="os-layer-title">Core Engine Layer</div>
                <div class="os-layer-copy">KPI Module이 공식 지표를 단일 소스로 계산</div>
                <div class="os-layer-tags"><span>KPI</span><span>Single Source</span></div>
              </div>
            </div>

            <div class="os-flow-turn">&darr;</div>

            <div class="os-flow-row row-bottom">
              <div class="os-layer-card layer-builder">
                <div class="os-layer-step">L6</div>
                <div class="os-layer-title">Presentation Layer</div>
                <div class="os-layer-copy">Builder가 승인된 payload를 HTML로 렌더링</div>
                <div class="os-layer-tags"><span>Render-only</span><span>Preview</span></div>
              </div>
              <div class="os-layer-link">&larr;</div>
              <div class="os-layer-card layer-intel">
                <div class="os-layer-step">L5</div>
                <div class="os-layer-title">Intelligence Layer</div>
                <div class="os-layer-copy">Sandbox / Territory / Prescription / RADAR 분석</div>
                <div class="os-layer-tags"><span>Insight</span><span>Signal</span></div>
              </div>
              <div class="os-layer-link">&larr;</div>
              <div class="os-layer-card layer-ops">
                <div class="os-layer-step">L4</div>
                <div class="os-layer-title">Validation Layer</div>
                <div class="os-layer-copy">품질 검증, 매핑 검증, 전달 가능 여부 판단</div>
                <div class="os-layer-tags"><span>Quality Gate</span><span>Handoff</span></div>
              </div>
            </div>
          </div>
          <div class="os-flow-note">KPI는 Core Engine에서 1회 계산되고, OPS는 검증/오케스트레이션만 수행합니다. 이후 Intelligence와 Builder가 승인 결과를 소비합니다.</div>
        </div>
        """
    )
    if hasattr(st, "html"):
        st.html(flow_html)
    else:
        st.markdown(flow_html, unsafe_allow_html=True)

    if result and result.get("recommended_actions"):
        render_panel_header("AI 기반 운영 최적화 제언")
        for action in result["recommended_actions"]:
            st.markdown(f"""<div class="insight-card"><span>{action}</span></div>""", unsafe_allow_html=True)


__all__ = ["render_dashboard_tab"]
