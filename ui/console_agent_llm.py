from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

import httpx

from common.config import settings


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _load_json_file(path: Path) -> dict[str, Any] | list[Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _load_branch_asset_json(path: Path) -> dict[str, Any] | None:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return None
    match = re.search(r"=\s*(\{.*\})\s*;?\s*$", text, re.S)
    if not match:
        return None
    try:
        data = json.loads(match.group(1))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _sum_period(values: Any, start_idx: int, end_idx: int) -> float:
    if not isinstance(values, list):
        return 0.0
    total = 0.0
    for value in values[start_idx:end_idx]:
        try:
            total += float(value or 0)
        except Exception:
            continue
    return total


def _summarize_sandbox_payload(path: Path) -> str:
    data = _load_json_file(path)
    if not isinstance(data, dict):
        return ""
    payload = data.get("payload", {})
    if not isinstance(payload, dict):
        return ""
    manifest = payload.get("branch_asset_manifest", {})
    assets_dir = path.parent / "sandbox_report_preview_assets"
    ranking_rows: list[dict[str, Any]] = []
    if isinstance(manifest, dict):
        for branch_name, asset_name in manifest.items():
            branch_data = _load_branch_asset_json(assets_dir / str(asset_name))
            if not branch_data:
                continue
            for member in branch_data.get("members", []) or []:
                if not isinstance(member, dict):
                    continue
                q1_actual = round(_sum_period(member.get("monthly_actual"), 0, 3))
                q1_target = round(_sum_period(member.get("monthly_target"), 0, 3))
                attainment = round((q1_actual / q1_target) * 100, 1) if q1_target else 0.0
                ranking_rows.append(
                    {
                        "branch": branch_name,
                        "rep_name": _clean_text(member.get("성명")),
                        "q1_actual": q1_actual,
                        "q1_target": q1_target,
                        "q1_attainment": attainment,
                        "HIR": float(member.get("HIR", 0) or 0),
                        "RTR": float(member.get("RTR", 0) or 0),
                        "BCR": float(member.get("BCR", 0) or 0),
                        "PHR": float(member.get("PHR", 0) or 0),
                        "PI": float(member.get("PI", 0) or 0),
                        "FGR": float(member.get("FGR", 0) or 0),
                    }
                )
    if not ranking_rows:
        return f"[artifact] {path.name}\n- payload keys: {list(payload.keys())[:20]}"

    top5 = sorted(ranking_rows, key=lambda item: item["q1_actual"], reverse=True)[:5]
    bottom5 = sorted(ranking_rows, key=lambda item: item["q1_actual"])[:5]

    def _avg(items: list[dict[str, Any]], key: str) -> float:
        return round(sum(float(item.get(key, 0) or 0) for item in items) / len(items), 1) if items else 0.0

    gap_lines = []
    for key in ["HIR", "RTR", "BCR", "PHR", "PI", "FGR"]:
        gap_lines.append(f"- {key}: top5 평균 {_avg(top5, key)} / bottom5 평균 {_avg(bottom5, key)} / 격차 {round(_avg(top5, key)-_avg(bottom5, key),1)}")

    return (
        f"[artifact] {path.name}\n"
        f"- branch_count: {len(manifest) if isinstance(manifest, dict) else 0}\n"
        "[Q1 top5 reps]\n"
        + "\n".join(
            f"- {idx+1}. {item['branch']} {item['rep_name']} | 실적 {item['q1_actual']:,}원 | 목표 {item['q1_target']:,}원 | 달성률 {item['q1_attainment']}%"
            for idx, item in enumerate(top5)
        )
        + "\n[Q1 bottom5 reps]\n"
        + "\n".join(
            f"- {idx+1}. {item['branch']} {item['rep_name']} | 실적 {item['q1_actual']:,}원 | 목표 {item['q1_target']:,}원 | 달성률 {item['q1_attainment']}%"
            for idx, item in enumerate(bottom5)
        )
        + "\n[metric gaps]\n"
        + "\n".join(gap_lines[:4])
    )


def _summarize_generic_json(path: Path) -> str:
    data = _load_json_file(path)
    if isinstance(data, dict):
        preview = {key: data[key] for key in list(data.keys())[:15]}
        return f"[artifact] {path.name}\n{json.dumps(preview, ensure_ascii=False, indent=2)[:4000]}"
    if isinstance(data, list):
        return f"[artifact] {path.name}\nlist_length={len(data)}\n{json.dumps(data[:3], ensure_ascii=False, indent=2)[:3000]}"
    return ""


def _summarize_html(path: Path) -> str:
    try:
        raw = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""
    text = re.sub(r"<script.*?</script>", " ", raw, flags=re.S | re.I)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return f"[artifact] {path.name}\n{text[:2500]}"


def build_artifact_contexts(artifacts: list[dict[str, Any]], max_items: int = 4) -> tuple[str, list[str]]:
    prioritized = sorted(
        artifacts,
        key=lambda item: (
            0 if item.get("artifact_role") == "sandbox_report" else 1,
            0 if item.get("artifact_type") == "report_payload_standard" else 1,
            0 if item.get("artifact_type") == "report_result_asset" else 1,
            0 if item.get("artifact_type") == "report_html" else 1,
        ),
    )
    chunks: list[str] = []
    evidence_refs: list[str] = []
    for artifact in prioritized:
        path_text = _clean_text(artifact.get("storage_path"))
        if not path_text:
            continue
        path = Path(path_text)
        if not path.exists():
            continue
        summary = ""
        if path.name == "sandbox_report_preview_payload_standard.json":
            summary = _summarize_sandbox_payload(path)
        elif path.suffix.lower() == ".json":
            summary = _summarize_generic_json(path)
        elif path.suffix.lower() in {".html", ".htm"}:
            summary = _summarize_html(path)
        if not summary:
            continue
        chunks.append(summary)
        evidence_refs.append(path_text)
        if len(chunks) >= max_items:
            break
    return "\n\n".join(chunks), evidence_refs


def is_llm_configured() -> bool:
    return bool(_clean_text(settings.llm_provider) and _clean_text(settings.llm_model) and _clean_text(settings.llm_api_key))


def _provider() -> str:
    return _clean_text(settings.llm_provider).lower()


def _system_prompt(answer_scope: str) -> str:
    scope_line = "근거 경로를 우선 설명하라." if answer_scope == "evidence_trace" else "최종 보고서 요약 중심으로 답하라."
    return (
        "You are the Agent tab analyst for Sales Data OS. "
        "Use only the provided run report context. "
        "Do not recalculate KPI. "
        "Do not join raw data. "
        "If evidence is missing, say that it cannot be confirmed. "
        f"{scope_line}"
    )


def _user_prompt(
    question: str,
    prompt_ctx: dict[str, Any] | None,
    full_ctx: dict[str, Any] | None,
    answer_scope: str,
    artifact_contexts: str,
) -> str:
    return (
        "[answer_scope]\n"
        f"{answer_scope}\n\n"
        "[user_question]\n"
        f"{question}\n\n"
        "[prompt_context]\n"
        f"{prompt_ctx or {}}\n\n"
        "[full_context]\n"
        f"{full_ctx or {}}\n\n"
        "[artifact_contexts]\n"
        f"{artifact_contexts}\n\n"
        "[response_rule]\n"
        "Answer in Korean. Be concise. Mention only facts supported by the provided context."
    )


def _extract_openai_text(data: dict[str, Any]) -> str:
    text = _clean_text(data.get("output_text"))
    if text:
        return text
    for item in data.get("output", []) or []:
        for content in item.get("content", []) or []:
            if content.get("type") == "output_text":
                text = _clean_text(content.get("text"))
                if text:
                    return text
    return ""


def _call_openai(system_prompt: str, user_prompt: str) -> str:
    base_url = _clean_text(settings.llm_base_url) or "https://api.openai.com"
    response = httpx.post(
        f"{base_url.rstrip('/')}/v1/responses",
        headers={
            "Authorization": f"Bearer {settings.llm_api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": settings.llm_model,
            "input": [
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": system_prompt}],
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": user_prompt}],
                },
            ],
            "temperature": settings.llm_temperature,
            "max_output_tokens": settings.llm_max_tokens,
        },
        timeout=settings.llm_timeout_sec,
    )
    response.raise_for_status()
    return _extract_openai_text(response.json())


def _call_claude(system_prompt: str, user_prompt: str) -> str:
    base_url = _clean_text(settings.llm_base_url) or "https://api.anthropic.com"
    response = httpx.post(
        f"{base_url.rstrip('/')}/v1/messages",
        headers={
            "x-api-key": settings.llm_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": settings.llm_model,
            "max_tokens": settings.llm_max_tokens,
            "temperature": settings.llm_temperature,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        },
        timeout=settings.llm_timeout_sec,
    )
    response.raise_for_status()
    data = response.json()
    parts = data.get("content", []) or []
    for part in parts:
        if part.get("type") == "text":
            text = _clean_text(part.get("text"))
            if text:
                return text
    return ""


def _call_gemini(system_prompt: str, user_prompt: str) -> str:
    base_url = _clean_text(settings.llm_base_url) or "https://generativelanguage.googleapis.com"
    model = settings.llm_model
    response = httpx.post(
        f"{base_url.rstrip('/')}/v1beta/models/{model}:generateContent",
        params={"key": settings.llm_api_key},
        headers={"Content-Type": "application/json"},
        json={
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "temperature": settings.llm_temperature,
                "maxOutputTokens": settings.llm_max_tokens,
            },
        },
        timeout=settings.llm_timeout_sec,
    )
    response.raise_for_status()
    data = response.json()
    for candidate in data.get("candidates", []) or []:
        content = candidate.get("content", {})
        for part in content.get("parts", []) or []:
            text = _clean_text(part.get("text"))
            if text:
                return text
    return ""


def generate_agent_answer(
    *,
    question: str,
    prompt_ctx: dict[str, Any] | None,
    full_ctx: dict[str, Any] | None,
    answer_scope: str,
    evidence_refs: list[str],
    artifact_contexts: str = "",
) -> dict[str, Any]:
    if not is_llm_configured():
        raise RuntimeError("llm_not_configured")

    system_prompt = _system_prompt(answer_scope)
    user_prompt = _user_prompt(question, prompt_ctx, full_ctx, answer_scope, artifact_contexts)
    provider = _provider()

    if provider == "openai":
        answer_text = _call_openai(system_prompt, user_prompt)
    elif provider == "claude":
        answer_text = _call_claude(system_prompt, user_prompt)
    elif provider == "gemini":
        answer_text = _call_gemini(system_prompt, user_prompt)
    else:
        raise RuntimeError(f"unsupported_llm_provider:{provider}")

    answer_text = _clean_text(answer_text)
    if not answer_text:
        raise RuntimeError("empty_llm_response")

    return {
        "answer_text": answer_text,
        "evidence_refs": evidence_refs,
        "provider": provider,
        "model": settings.llm_model,
    }
