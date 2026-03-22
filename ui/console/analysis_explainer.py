from __future__ import annotations

from typing import Any


def _format_number(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.1f}"
    return str(value)


def explain_module_result(module: str, step: dict[str, Any]) -> dict[str, Any]:
    summary = step.get("summary") or {}
    status = str(step.get("status", "")).upper()
    score = step.get("score")

    if module == "crm":
        company_unmapped = int(summary.get("company_unmapped_count", 0))
        crm_unmapped = int(summary.get("crm_unmapped_count", 0))
        if status == "PASS":
            explanation = (
                "병원, 담당자, CRM 활동 연결이 전반적으로 정상이며 다음 단계로 전달 가능한 상태입니다. "
                "다만 일부 unmapped 데이터는 남아 있어 운영 점검 대상으로 볼 수 있습니다."
            )
        elif status == "WARN":
            explanation = "CRM 기본 연결은 됐지만 매핑 누락이나 품질 저하가 있어 후속 단계 해석 시 주의가 필요합니다."
        else:
            explanation = "CRM 입력 연결 또는 정규화에 실패해 다음 단계로 넘기기 어려운 상태입니다."
        evidence = [
            f"hospital_count={summary.get('hospital_count', '-')}",
            f"company_unmapped_count={company_unmapped}",
            f"crm_unmapped_count={crm_unmapped}",
            f"quality_score={_format_number(score)}",
        ]
        return {"summary": explanation, "evidence": evidence}

    if module == "prescription":
        gap_count = int(summary.get("gap_record_count", 0))
        completion = summary.get("flow_completion_rate", 0)
        if status == "PASS":
            explanation = "Prescription 흐름 연결이 정상이며 gap 없이 다음 분석 단계에서 활용 가능한 상태입니다."
        elif status == "WARN":
            explanation = "Prescription 흐름은 생성됐지만 연결 누락 또는 검토 대상 케이스가 남아 있습니다."
        else:
            explanation = "Prescription 흐름 추적 또는 검증에 실패해 후속 활용이 어렵습니다."
        evidence = [
            f"flow_record_count={summary.get('flow_record_count', '-')}",
            f"gap_record_count={gap_count}",
            f"flow_completion_rate={completion}",
            f"quality_score={_format_number(score)}",
        ]
        return {"summary": explanation, "evidence": evidence}

    if module == "sandbox":
        month_count = summary.get("metric_month_count", "-")
        if status == "PASS":
            explanation = "CRM, 실적, 목표 데이터가 함께 정리돼 Sandbox 분석에 필요한 월별 KPI 계산이 가능한 상태입니다."
        elif status == "WARN":
            explanation = "Sandbox 분석은 가능하지만 일부 입력 정합성이나 월별 계산 품질을 추가 점검해야 합니다."
        else:
            explanation = "Sandbox 입력 정규화 또는 KPI 계산이 실패한 상태입니다."
        evidence = [
            f"crm_record_count={summary.get('crm_record_count', '-')}",
            f"sales_record_count={summary.get('sales_record_count', '-')}",
            f"target_record_count={summary.get('target_record_count', '-')}",
            f"metric_month_count={month_count}",
        ]
        return {"summary": explanation, "evidence": evidence}

    if module == "territory":
        gap_count = int(summary.get("gap_count", 0))
        quality_status = str(summary.get("quality_status", "")).lower()
        if quality_status == "warn" or status == "WARN":
            explanation = (
                "Territory 데이터는 생성됐고 커버리지도 충분하지만, 담당자 배치 불균형이 감지돼 운영 경고가 발생했습니다. "
                "즉 실행 불가가 아니라 현업 배분 상태를 재점검하라는 의미입니다."
            )
        elif status == "PASS":
            explanation = "Territory 커버리지, 동선, 배치 균형이 모두 기준을 만족해 안정적으로 활용 가능한 상태입니다."
        else:
            explanation = "Territory 지도/동선 생성 또는 검증 기준을 충족하지 못한 상태입니다."
        evidence = [
            f"route_count={summary.get('route_count', '-')}",
            f"coverage_rate={summary.get('coverage_rate', '-')}",
            f"gap_count={gap_count}",
            f"rep_filter_count={summary.get('rep_filter_count', '-')}",
        ]
        return {"summary": explanation, "evidence": evidence}

    if module == "radar":
        top_issue = summary.get("top_issue", "-")
        signal_count = summary.get("signal_count", "-")
        if status == "APPROVED":
            explanation = "RADAR 입력 품질은 승인됐고, 현재 신호를 기반으로 우선순위 해석이 가능한 상태입니다."
        elif status == "WARN":
            explanation = "RADAR 신호는 생성됐지만 입력 품질이나 신호 해석 결과를 추가로 검토해야 합니다."
        else:
            explanation = "RADAR 신호 생성 또는 승인 기준 충족에 실패했습니다."
        evidence = [
            f"signal_count={signal_count}",
            f"top_issue={top_issue}",
            f"period_value={summary.get('period_value', '-')}",
            f"quality_score={_format_number(score)}",
        ]
        return {"summary": explanation, "evidence": evidence}

    if module == "builder":
        built_report_count = summary.get("built_report_count", "-")
        if status == "PASS":
            explanation = "Builder가 승인된 payload를 사용해 최종 HTML 결과물을 정상 생성한 상태입니다."
        elif status == "WARN":
            explanation = "Builder 결과물은 생성됐지만 일부 리포트 누락 또는 출력 품질 점검이 필요합니다."
        else:
            explanation = "Builder 렌더링 또는 결과물 생성에 실패했습니다."
        evidence = [
            f"built_report_count={built_report_count}",
            f"skipped_reports={len(summary.get('skipped_reports', [])) if isinstance(summary, dict) else '-'}",
            f"quality_score={_format_number(score)}",
        ]
        return {"summary": explanation, "evidence": evidence}

    explanation = "상태는 계산됐지만 이 모듈용 해석 문장이 아직 정의되지 않았습니다."
    evidence = [f"status={status}", f"score={_format_number(score)}"]
    return {"summary": explanation, "evidence": evidence}

