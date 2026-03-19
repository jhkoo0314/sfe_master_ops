from __future__ import annotations

from typing import Any

from ui.console.agent.artifacts import _pick_evidence_refs


def _build_mock_agent_answer(
    question: str,
    prompt_ctx: dict[str, Any] | None,
    full_ctx: dict[str, Any] | None,
    answer_scope: str,
) -> dict[str, Any]:
    executive_summary = ""
    if isinstance(prompt_ctx, dict):
        executive_summary = str(prompt_ctx.get("executive_summary", "")).strip()
    if not executive_summary and isinstance(full_ctx, dict):
        executive_summary = str(full_ctx.get("executive_summary", "")).strip()
    if not executive_summary:
        executive_summary = "현재 run 문맥에서 요약 본문을 찾지 못했습니다."

    evidence_refs = _pick_evidence_refs(full_ctx, limit=3)
    caution = "이 답변은 report_context 범위 내 mock 해석이며 KPI를 재계산하지 않습니다."
    if answer_scope == "evidence_trace":
        follow_up = "근거 파일 경로를 열어 수치 원문을 확인하세요."
    else:
        follow_up = "필요하면 answer scope를 evidence_trace로 바꿔 근거 중심으로 다시 질문하세요."

    sales_rankings = full_ctx.get("sales_rankings", {}) if isinstance(full_ctx, dict) else {}
    comparison_insights = full_ctx.get("comparison_insights", {}) if isinstance(full_ctx, dict) else {}
    question_lower = question.lower()
    ranking_lines: list[str] = []
    comparison_lines: list[str] = []
    if isinstance(sales_rankings, dict) and any(token in question_lower for token in ["top", "상위", "하위", "1분기", "1-3"]):
        for item in sales_rankings.get("q1_top5_members", [])[:5]:
            ranking_lines.append(
                f"- {item.get('rank')}. {item.get('branch')} {item.get('rep_name')} | Q1 실적 {int(item.get('q1_actual', 0)):,}원 | 달성률 {item.get('q1_attainment', 0)}%"
            )
    if isinstance(comparison_insights, dict) and any(token in question_lower for token in ["이유", "차이", "왜"]):
        metric_gaps = comparison_insights.get("metric_gaps", [])
        activity_gaps = comparison_insights.get("activity_gaps", [])
        if metric_gaps:
            comparison_lines.append("[상하위 차이 지표]")
            for item in metric_gaps[:3]:
                comparison_lines.append(
                    f"- {item.get('metric')}: 상위 평균 {item.get('top5_avg')} / 하위 평균 {item.get('bottom5_avg')} / 격차 {item.get('gap')}p"
                )
        if activity_gaps:
            comparison_lines.append("[상하위 활동 차이]")
            for item in activity_gaps[:3]:
                comparison_lines.append(
                    f"- {item.get('activity')}: 상위 평균 {item.get('top5_avg')} / 하위 평균 {item.get('bottom5_avg')} / 격차 {item.get('gap')}"
                )

    answer_text = (
        "[핵심 답변]\n"
        f"- 질문: {question}\n"
        f"- 요약: {executive_summary}\n\n"
        + ("[Q1 담당자 랭킹]\n" + "\n".join(ranking_lines) + "\n\n" if ranking_lines else "")
        + ("[차이 해석]\n" + "\n".join(comparison_lines) + "\n\n" if comparison_lines else "")
        + "[근거]\n"
        + ("\n".join([f"- {ref}" for ref in evidence_refs]) if evidence_refs else "- 근거 인덱스 없음")
        + "\n\n[주의사항]\n"
        + f"- {caution}\n\n[추가로 볼 포인트]\n- {follow_up}"
    )
    return {"answer_text": answer_text, "evidence_refs": evidence_refs}

__all__ = ["_build_mock_agent_answer"]
