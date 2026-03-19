from __future__ import annotations

from typing import Any

import httpx

from common.config import settings


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


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


def _user_prompt(question: str, prompt_ctx: dict[str, Any] | None, full_ctx: dict[str, Any] | None, answer_scope: str) -> str:
    return (
        "[answer_scope]\n"
        f"{answer_scope}\n\n"
        "[user_question]\n"
        f"{question}\n\n"
        "[prompt_context]\n"
        f"{prompt_ctx or {}}\n\n"
        "[full_context]\n"
        f"{full_ctx or {}}\n\n"
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
) -> dict[str, Any]:
    if not is_llm_configured():
        raise RuntimeError("llm_not_configured")

    system_prompt = _system_prompt(answer_scope)
    user_prompt = _user_prompt(question, prompt_ctx, full_ctx, answer_scope)
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
