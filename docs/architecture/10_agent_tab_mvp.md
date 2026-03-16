# Agent Tab MVP Spec

작성일: 2026-03-16

이 문서는 Streamlit 기반 Agent 탭 MVP 구현 명세다.

## 1. 목적
- Agent는 계산 엔진이 아니다.
- Agent는 Final Report Package 해석 레이어다.
- Agent는 `report_context.prompt.json`을 기본으로 읽고, 필요 시 `report_context.full.json` 근거를 참조한다.

## 2. 붙일 위치
현재 UI 구조 기준:
- 탭 선언: `ui/ops_console.py`
- 탭 렌더 함수: `ui/console_tabs.py`

구현 권장:
- `ui/ops_console.py`에 6번째 탭 `Agent` 추가
- `ui/console_tabs.py`에 `render_agent_tab()` 추가

## 3. 화면 구성
- Run 선택 드롭다운
- 현재 mode 표시
- 기간(period/comparison) 표시
- validation/confidence 표시
- 질문 입력창
- 답변 영역
- 근거 요약 영역(evidence index 상위 3개)
- 대화 이력 영역(최신 20개)

## 4. session_state 설계
필수 키:
- `selected_run_id`
- `selected_mode`
- `report_context_full`
- `report_context_prompt`
- `agent_history`
- `current_answer_scope`

초기화 규칙:
- 탭 진입 시 키가 없으면 기본값 생성
- run 변경 시 `report_context_*`와 `current_answer_scope` 재로딩

## 5. 로딩 흐름
1. `data/ops_validation/{company_key}/runs/`에서 성공 run 목록 조회
2. 기본값으로 최신 successful run 선택
3. `report_context.full.json`, `report_context.prompt.json` 로드
4. 로드 실패 시 경고 + 질문창 비활성
5. 질문 입력
6. LLM 호출(초기 MVP는 mock/adapter 가능)
7. 답변 + 근거 + scope 저장
8. `chat/agent_chat_history.jsonl`에 append
9. 가능하면 `agent_chat_logs` DB에도 비동기 저장

## 6. 질문 허용 범위
초기 MVP에서 허용:
- 이번 보고서 핵심 요약
- 비교 기간 대비 변화 설명
- KPI 변화 해석
- RADAR 우선순위/이슈 설명
- validation 경고 해석
- 추천 확인 포인트 제시(보고서 범위 내)

## 7. 금지 범위
초기 MVP에서 금지:
- KPI 재계산
- 원본 데이터 재조인
- 임의 세그먼트 생성
- 보고서 범위 밖 추정
- 존재하지 않는 숫자 생성

## 8. 프롬프트 전략
System prompt 핵심 원칙:
- 현재 `run_id`와 `report_context` 범위 안에서만 답변
- 근거가 없으면 모른다고 답변
- 불확실하면 uncertainty를 명시
- 가능하면 `evidence_index`를 함께 제시
- 역할은 계산이 아니라 해석

권장 prompt 입력:
- `report_context.prompt.json` 전체
- 사용자 질문
- `answer_scope` (`final_report_only` 또는 `evidence_trace`)

## 9. 응답 포맷
표준 응답 블록:
- 핵심 답변
- 근거
- 주의사항
- 추가로 볼 포인트

예시:
```text
[핵심 답변]
...

[근거]
- ... (artifact path)

[주의사항]
- ...

[추가로 볼 포인트]
- ...
```

## 10. 저장/로그
초기 저장:
- `data/ops_validation/{company_key}/runs/{run_id}/chat/agent_chat_history.jsonl`

레코드 예시:
```json
{
  "created_at": "2026-03-16T14:20:01+09:00",
  "run_id": "...",
  "mode": "integrated_full",
  "question": "이번 분기 핵심 이슈가 뭐야?",
  "answer": "...",
  "used_context_version": "v1",
  "answer_scope": "final_report_only",
  "evidence_refs": ["artifacts/final/sandbox_report_preview.html"]
}
```

후속 DB 저장:
- `agent_chat_logs`

## 11. 구현 순서
1. `runs/{run_id}` 스캔 유틸 추가
2. context 로더(`full`, `prompt`) 추가
3. `render_agent_tab()` 뷰 추가
4. 질문/답변 로컬 jsonl 저장 구현
5. answer scope 토글 추가
6. evidence 표시 블록 추가
7. DB insert adapter 추가(실패 시 로컬만 유지)
8. 기본 안전 프롬프트 적용
9. 테스트: context 없음/손상/정상 케이스
10. 문서(RUNBOOK/STRUCTURE) 동기화

## 12. 현재 코드와 연결 포인트
- Streamlit 탭 구성: `ui/ops_console.py`, `ui/console_tabs.py`
- 실행 결과(run_id/steps): `ops_core/workflow/execution_service.py`
- 모드 정의: `ops_core/workflow/execution_registry.py`
- Builder 결과 생성: `scripts/validate_builder_with_ops.py`
- 최종 Builder 스키마: `modules/builder/schemas.py`
