# Agent 탭 구현 계획서 (Part2 실행안)

작성일: 2026-03-19  
상태: `draft`

이 문서는 `10_agent_tab_mvp.md`, `11_run_based_storage.md`, `12_part2_status_source_of_truth.md`를 실제 코드 작업 순서로 풀어쓴 실행 계획서입니다.

---

## 1. 목표 (쉬운 요약)

- 사용자가 **실행 1번(run)** 을 고르면,
- 그 실행에서 만들어진 **최종 보고서 문맥(report_context)** 을 읽어서,
- Agent 탭이 질문에 답하고 근거를 함께 보여주도록 만든다.

중요:
- Agent는 계산기가 아니다.
- KPI 재계산을 하지 않는다.
- 보고서에 없는 숫자는 만들지 않는다.

---

## 2. 이번 구현 범위 (MVP)

### 포함
- Streamlit에 `Agent` 탭 추가
- 성공 run 목록 조회 + 기본 run 자동 선택
- `report_context.prompt.json` 우선 로딩
- 필요 시 `report_context.full.json` 근거 조회
- 질문/답변 UI
- evidence 상위 3개 표시
- 대화 20개 표시
- 대화 로그 파일 저장
  - `data/ops_validation/{company_key}/runs/{run_id}/chat/agent_chat_history.jsonl`

### 제외 (후속)
- 실시간 KPI 계산
- 원본 raw 재조인
- 고급 에이전트 워크플로우(툴 호출 체인)

---

## 3. 선행 조건

- DB 마이그레이션 `migrations/002_run_based_schema.sql` 완료 (완료 상태로 간주)
- run 기반 저장 경로가 최소한 읽기 가능해야 함
  - `data/ops_validation/{company_key}/runs/{run_id}/`
- Builder가 `report_context.full.json`, `report_context.prompt.json`를 생성해야 함

주의:
- Builder 생성이 아직 불완전하면 Agent 탭은 경고를 표시하고 입력창을 비활성화한다.

---

## 4. 작업 파일 (1차)

- `ui/ops_console.py`
  - 탭 리스트에 `Agent` 추가
- `ui/console_tabs.py`
  - `render_agent_tab()` 추가
  - run 스캔/로딩/질의 UI/이력 표시 구현
- (필요 시 신규 유틸)
  - `ui/console_agent.py` (권장)
    - run 조회
    - context 로더
    - history append/read

---

## 5. 화면 요구사항

Agent 탭에 아래를 순서대로 보여준다.

1. Run 선택 드롭다운
2. mode 표시
3. 기간(period/comparison) 표시
4. validation/confidence 표시
5. 답변 범위(scope) 선택
   - `final_report_only`
   - `evidence_trace`
6. 질문 입력창
7. 답변 출력
8. 근거 요약 (evidence index 상위 3개)
9. 대화 이력 (최신 20개)

---

## 6. 상태값(session_state)

필수 키:
- `selected_run_id`
- `selected_mode`
- `report_context_full`
- `report_context_prompt`
- `agent_history`
- `current_answer_scope`

초기화 규칙:
- 키가 없으면 기본값 생성
- run 변경 시 context/full/scope/history를 재로딩

---

## 7. 처리 흐름

1. `runs/` 폴더에서 성공 run 목록 조회
2. 최신 successful run 자동 선택
3. `report_context.prompt.json` 로드
4. `report_context.full.json` 로드(없어도 prompt만 있으면 최소 동작)
5. 로드 실패 시 경고 + 질문 입력 비활성
6. 질문 입력
7. 안전 프롬프트로 응답 생성(초기엔 mock/adapter 허용)
8. 답변 + evidence + scope를 화면에 출력
9. chat jsonl에 append
10. (선택) DB `agent_chat_logs` 비동기 저장

---

## 8. LLM API 연결 계획 (멀티 프로바이더)

목표:
- 아직 특정 모델을 확정하지 않고, `Gemini/OpenAI/Claude`를 모두 붙일 수 있는 구조로 만든다.
- UI 코드와 LLM 호출 코드를 분리해, 나중에 모델을 바꿔도 화면 코드는 거의 수정하지 않도록 한다.

### 8-1. 연결 구조

- UI(`render_agent_tab`)는 공통 함수만 호출:
  - 예: `ask_agent(question, context_prompt, context_full, answer_scope)`
- 실제 API 호출은 어댑터 레이어에서 분기:
  - `ui/console_agent_llm.py` (권장)
  - provider별 클라이언트
    - `ui/llm_clients/openai_client.py`
    - `ui/llm_clients/claude_client.py`
    - `ui/llm_clients/gemini_client.py`

### 8-2. 설정값(환경변수)

- `LLM_PROVIDER` (`openai` | `claude` | `gemini`)
- `LLM_MODEL`
- `LLM_API_KEY`
- `LLM_BASE_URL` (옵션)
- `LLM_TIMEOUT_SEC` (기본 30)
- `LLM_MAX_TOKENS` (기본 1200)
- `LLM_TEMPERATURE` (기본 0.2)

원칙:
- API 키는 코드/문서/로그에 직접 쓰지 않는다.
- 회사별로 모델이 달라도 같은 인터페이스로 호출 가능해야 한다.

### 8-3. 공통 입력/출력 규격

입력:
- `report_context.prompt.json` (기본)
- 사용자 질문
- `answer_scope` (`final_report_only` | `evidence_trace`)
- 필요 시 `report_context.full.json`의 evidence 일부

출력(정규화):
- `answer_text`
- `evidence_refs` (최대 3)
- `cautions`
- `follow_up_points`
- `provider`, `model`, `latency_ms`, `token_usage`(가능한 경우)

### 8-4. 공통 안전 프롬프트

시스템 규칙(모든 provider 공통):
- KPI 재계산 금지
- raw 재조인 금지
- 보고서 범위 밖 추정 금지
- 근거가 없으면 \"확인 불가\"로 답변
- 불확실하면 불확실하다고 명시

### 8-5. 실패 대응/폴백

- 타임아웃/일시 오류(429, 5xx): 최대 2회 재시도
- 최종 실패 시:
  - 사용자에게 쉬운 경고 메시지 표시
  - 질문창은 유지하고 재시도 가능 상태로 둠
  - 필요 시 mock/로컬 요약 fallback(옵션)

### 8-6. 로그/감사

- run별 `chat/agent_chat_history.jsonl`에 저장:
  - 질문/답변/근거/run_id/provider/model/created_at
- 저장 금지:
  - API 키
  - 과도하게 긴 원문 프롬프트 전문

### 8-7. 구현 단계

1. 공통 인터페이스 + provider router 구현
2. OpenAI/Claude/Gemini 각 client 최소 호출 구현
3. 응답 정규화 + 재시도 + 타임아웃 처리
4. UI 연결 + run별 로그 저장
5. 비정상 케이스 테스트(키 없음/타임아웃/빈 응답)

---

## 9. 안전 가드레일

시스템 고정 규칙:
- KPI 재계산 금지
- raw 재조인 금지
- 보고서 범위 밖 추정 금지
- 근거 없으면 "확인 불가"로 답변
- 불확실하면 uncertainty 문구 포함

응답 형식:

```text
[핵심 답변]
...

[근거]
- ...

[주의사항]
- ...

[추가로 볼 포인트]
- ...
```

---

## 10. 구현 단계 (권장 순서)

### Step 1. 탭 골격 추가
- Agent 탭 진입/렌더만 연결
- DoD: 탭 클릭 시 빈 화면 대신 기본 UI 보임

### Step 2. run 선택/컨텍스트 로딩
- run 목록 + 최신 성공 run 기본 선택
- context 로드 실패 처리
- DoD: run 변경 시 표시 정보가 바뀜

### Step 3. 질문/답변 + 로그 저장
- 질문 입력 -> 응답 -> jsonl 저장
- DoD: 질문 1회 후 history 파일에 기록 생성

### Step 4. evidence/이력 표시 고도화
- evidence 상위 3개
- history 최신 20개
- DoD: 화면에서 근거와 과거 질문 확인 가능

### Step 5. 안정화
- context 없음/손상/정상 케이스 점검
- DoD: 예외 상황에서도 탭이 죽지 않고 경고 표시

---

## 11. 테스트 체크리스트

- run 폴더 없음
- 성공 run 없음
- prompt만 있고 full 없음
- prompt/full 둘 다 손상(JSON parse 실패)
- 질문 미입력 상태에서 전송 클릭
- 긴 질문 입력
- history 20개 초과 시 최신 20개만 표시
- 다른 run으로 변경 시 기존 문맥이 섞이지 않는지 확인

---

## 12. 완료 기준 (Definition of Done)

아래를 만족하면 MVP 완료로 본다.

- Agent 탭이 운영 콘솔에 표시된다.
- 성공 run을 선택할 수 있다.
- report_context를 읽어 질문에 답할 수 있다.
- 답변 시 근거 3개가 함께 나온다.
- 대화 이력이 run별 jsonl에 저장된다.
- KPI 재계산/원본 재조인 없이 동작한다.
- 오류 상황에서 사용자에게 이해 가능한 경고를 보여준다.
- `LLM_PROVIDER` 전환만으로 OpenAI/Claude/Gemini 중 하나를 선택해 동작시킬 수 있다.

---

## 13. 다음 단계 (MVP 이후)

1. `agent_chat_logs` DB 저장 연결
2. evidence 링크 클릭 이동 UX 개선
3. answer scope별 프롬프트 미세 조정
4. RUNBOOK/STRUCTURE에 Agent 운영 절차 상세 반영

---

## 14. 한 줄 결론

이번 계획의 핵심은 **"한 run의 최종 보고 문맥을 Agent가 안전하게 읽고 설명하도록 연결"** 하는 것입니다.
