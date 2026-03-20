from __future__ import annotations

from datetime import datetime
from typing import Any

import streamlit as st

from ui.console.agent.artifacts import _load_run_artifacts, _pick_evidence_items
from ui.console.agent.context import _load_run_contexts
from ui.console.agent.history import _append_agent_history, _read_agent_history
from ui.console.agent.llm import build_artifact_contexts, generate_agent_answer, is_llm_configured
from ui.console.agent.mock import _build_mock_agent_answer
from ui.console.agent.runs import (
    _build_legacy_run_entry,
    _legacy_pipeline_root,
    _load_json_if_exists,
    _resolve_company_key_for_agent,
    _scan_successful_runs,
)
from ui.console.display import render_page_hero, render_panel_header
from ui.console.paths import get_active_company_key, get_active_company_name


def _dedupe_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    rows: list[str] = []
    for value in values:
        cleaned = str(value or '').strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        rows.append(cleaned)
    return rows


def _run_label(row: dict[str, Any]) -> str:
    run_id = str(row.get('run_id', '')).strip()
    mode = str(row.get('mode', '-') or '-')
    finished_at = str(row.get('finished_at', '-') or '-')
    return f"{run_id} | {mode} | {finished_at}"


def _scope_label(scope: str) -> str:
    return '근거 중심' if scope == 'evidence_trace' else '보고서 요약 중심'


def _display_evidence(evidence_refs: list[str]) -> None:
    render_panel_header('근거 요약')
    if not evidence_refs:
        st.info('현재 선택한 run에서 표시할 근거 경로가 없습니다.')
        return
    for ref in evidence_refs[:5]:
        st.code(ref, language='text')


def _display_history(history: list[dict[str, Any]]) -> None:
    render_panel_header('대화 이력')
    if not history:
        st.info('이 run에는 아직 대화 이력이 없습니다.')
        return

    for index, item in enumerate(history[:20], start=1):
        asked_at = str(item.get('created_at', '') or item.get('asked_at', '')).strip()
        question = str(item.get('question', '')).strip() or '질문 없음'
        answer = str(item.get('answer', '')).strip() or '답변 없음'
        model = str(item.get('model', '')).strip()
        provider = str(item.get('provider', '')).strip()
        header = f"{index}. {question[:70]}"
        if asked_at:
            header += f" | {asked_at[:19]}"
        with st.expander(header, expanded=(index == 1)):
            st.markdown(f"**질문**\n\n{question}")
            st.markdown(f"**답변**\n\n{answer}")
            meta_bits = [bit for bit in [provider, model] if bit]
            if meta_bits:
                st.caption(' / '.join(meta_bits))
            evidence_refs = item.get('evidence_refs', []) if isinstance(item.get('evidence_refs'), list) else []
            if evidence_refs:
                st.caption('근거 경로')
                for ref in evidence_refs[:3]:
                    st.code(str(ref), language='text')


def render_agent_tab() -> None:
    try:
        company_name = get_active_company_name()
        raw_company_key = get_active_company_key().strip()
        company_key = _resolve_company_key_for_agent(raw_company_key)

        render_page_hero(
            'Agent',
            f'{company_name} run 결과를 읽고 질문에 답합니다. KPI를 다시 계산하지 않고 저장된 결과물만 사용합니다.',
            'AGENT',
        )

        if not company_key:
            st.warning('먼저 회사를 선택하세요.')
            return

        legacy_summary_path = _legacy_pipeline_root(company_key) / 'pipeline_validation_summary.json'
        runs = _scan_successful_runs(company_key)
        if not runs and legacy_summary_path.exists():
            legacy_summary = _load_json_if_exists(legacy_summary_path)
            if legacy_summary:
                forced_entry = _build_legacy_run_entry(company_key, legacy_summary, legacy_summary_path)
                forced_entry['storage_type'] = 'legacy-forced'
                runs = [forced_entry]

        runs = [item for item in runs if str(item.get('run_id', '')).strip()]

        if not runs:
            st.warning('선택 가능한 run이 없습니다.')
            return

        run_label_map = {_run_label(row): row for row in runs}
        run_labels = list(run_label_map.keys())

        selected_run_id = str(st.session_state.get('selected_run_id', '')).strip()
        default_index = 0
        if selected_run_id:
            for idx, row in enumerate(runs):
                if str(row.get('run_id', '')).strip() == selected_run_id:
                    default_index = idx
                    break

        selected_run_label = st.selectbox('Run 선택', run_labels, index=default_index, key='agent_run_selector')
        selected_run = run_label_map[selected_run_label]
        selected_run_id = str(selected_run.get('run_id', '')).strip()
        selected_run_db_id = str(selected_run.get('run_db_id', '')).strip()
        selected_run_mode = str(selected_run.get('mode', '-') or '-')
        selected_finished_at = str(selected_run.get('finished_at', '-') or '-')

        st.session_state.selected_run_id = selected_run_id
        st.session_state.selected_run_db_id = selected_run_db_id
        st.session_state.selected_mode = selected_run_mode

        full_ctx, prompt_ctx = _load_run_contexts(company_key, selected_run_id, run_db_id=selected_run_db_id)
        history = _read_agent_history(company_key, selected_run_id, limit=20, run_db_id=selected_run_db_id)

        selection_bits = [selected_run_mode]
        if selected_finished_at:
            selection_bits.append(selected_finished_at[:19])
        selection_label = ' | '.join([bit for bit in selection_bits if bit and bit != '-'])
        if selection_label:
            st.caption(f"선택 run: {selected_run_id[:8]} | {selection_label}")
        else:
            st.caption(f"선택 run: {selected_run_id[:8]}")

        exec_summary = ''
        if isinstance(prompt_ctx, dict):
            exec_summary = str(prompt_ctx.get('executive_summary', '')).strip()
        if not exec_summary and isinstance(full_ctx, dict):
            exec_summary = str(full_ctx.get('executive_summary', '')).strip()
        if exec_summary:
            st.markdown(f'**실행 요약**\n\n{exec_summary}')

        default_evidence_refs = [item['path'] for item in _pick_evidence_items(full_ctx, limit=3)] if isinstance(full_ctx, dict) else []

        render_panel_header('질문하기')
        with st.form('agent_question_form'):
            answer_scope = st.selectbox(
                '답변 범위',
                ['final_report_only', 'evidence_trace'],
                index=0 if st.session_state.get('current_answer_scope', 'final_report_only') == 'final_report_only' else 1,
                format_func=_scope_label,
            )
            question = st.text_area(
                '질문',
                key='agent_question_input',
                height=110,
                placeholder='예: 1분기 실적 상위 5명과 하위권 차이를 알려줘',
            )
            submitted = st.form_submit_button('질문하기', use_container_width=True)

        st.session_state.current_answer_scope = answer_scope

        latest_record = None
        last_state = st.session_state.get('agent_last_record')
        if isinstance(last_state, dict) and last_state.get('run_id') == selected_run_id:
            latest_record = last_state.get('record')
        if latest_record is None and history:
            latest_record = history[0]

        if submitted:
            clean_question = question.strip()
            if not clean_question:
                st.warning('질문을 입력하세요.')
            else:
                artifacts = _load_run_artifacts(company_key, selected_run_id, run_db_id=selected_run_db_id)
                # 보고서가 5~6개까지 생성되므로 모두 포함하도록 상한을 넉넉히 둔다.
                artifact_contexts, artifact_evidence_refs = build_artifact_contexts(artifacts, max_items=8)
                combined_evidence_refs = _dedupe_strings(default_evidence_refs + artifact_evidence_refs)
                used_mock = False
                fallback_reason = ''
                provider = 'mock'
                model = 'mock'

                try:
                    response = generate_agent_answer(
                        question=clean_question,
                        prompt_ctx=prompt_ctx,
                        full_ctx=full_ctx,
                        answer_scope=answer_scope,
                        evidence_refs=combined_evidence_refs,
                        artifact_contexts=artifact_contexts,
                    )
                    answer_text = str(response.get('answer_text', '')).strip()
                    combined_evidence_refs = _dedupe_strings(list(response.get('evidence_refs', [])) + combined_evidence_refs)
                    provider = str(response.get('provider', '')).strip() or provider
                    model = str(response.get('model', '')).strip() or model
                except Exception as exc:
                    used_mock = True
                    fallback_reason = str(exc)
                    mock_response = _build_mock_agent_answer(clean_question, prompt_ctx, full_ctx, answer_scope)
                    answer_text = str(mock_response.get('answer_text', '')).strip()
                    combined_evidence_refs = _dedupe_strings(list(mock_response.get('evidence_refs', [])) + combined_evidence_refs)
                    if is_llm_configured():
                        model = 'fallback_after_llm_error'
                    else:
                        model = 'llm_not_configured'

                latest_record = {
                    'created_at': datetime.now().astimezone().isoformat(timespec='seconds'),
                    'mode': selected_run_mode,
                    'question': clean_question,
                    'answer': answer_text,
                    'answer_scope': answer_scope,
                    'model': model,
                    'provider': provider,
                    'evidence_refs': combined_evidence_refs[:5],
                    'used_mock': used_mock,
                    'run_id': selected_run_id,
                }
                if fallback_reason:
                    latest_record['fallback_reason'] = fallback_reason

                _append_agent_history(company_key, selected_run_id, latest_record, run_db_id=selected_run_db_id)
                st.session_state.agent_last_record = {'run_id': selected_run_id, 'record': latest_record}
                history = [latest_record] + history[:19]

        if latest_record:
            render_panel_header('최신 답변')
            if latest_record.get('used_mock'):
                reason = str(latest_record.get('fallback_reason', '')).strip()
                if reason and reason != 'llm_not_configured':
                    st.warning(f'LLM 응답에 실패해서 안전 폴백으로 답했습니다: {reason}')
                elif reason == 'llm_not_configured' or str(latest_record.get('model', '')) == 'llm_not_configured':
                    st.info('LLM 설정이 없어 mock 답변으로 표시합니다.')
            else:
                st.caption(f"{latest_record.get('provider', '')} / {latest_record.get('model', '')}")
            st.markdown(str(latest_record.get('answer', '')).strip())
            _display_evidence(list(latest_record.get('evidence_refs', [])))
        else:
            _display_evidence(default_evidence_refs)

        _display_history(history)

    except Exception as exc:
        st.error(f'Agent 화면 렌더 중 오류가 발생했습니다: {exc}')
        st.exception(exc)


__all__ = ["render_agent_tab"]
