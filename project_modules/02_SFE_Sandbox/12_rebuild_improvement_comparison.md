# 재구축 보완사항 상세 비교서 (As-Is vs To-Be)

## 1. 문서 목적
현재 Sandbox 문서를 기준으로, 독립 실행형 분석 엔진으로 다시 세울 때 무엇을 고쳐야 하는지 정리한다.

## 2. 현재 상태 요약 (As-Is)
- 강점
  - 공통 엔진, 시나리오 config, 품질 게이트 사고가 좋다.
  - Streamlit 콘솔, HTML 결과, 매핑 정책, Fail-Fast 철학이 정리돼 있다.
  - 실무 운영 관점의 로그/체크리스트 생각이 강하다.
- 한계
  - 문서만 읽으면 Sandbox가 OPS보다 중심 허브처럼 보일 수 있다.
  - 입력 표준화, 분석, 출력, 운영 설명이 한 덩어리라 범위가 넓다.
  - 승인 전 결과와 OPS 전달 결과가 분리돼 있지 않다.
  - Sandbox core와 무관한 다른 모듈 내용이 같이 들어 있어 경계가 흐려진다.

## 3. 목표 상태 (To-Be)
- Sandbox는 독립 실행형 분석 엔진이다.
- 승인된 입력 자산을 읽고 시나리오 분석을 수행한다.
- 공식 결과는 `sandbox_result_asset`이다.
- OPS는 승인된 Sandbox 결과만 읽는다.
- Sandbox core와 무관한 문서는 묶음에서 제거한다.

## 4. 상세 보완사항 비교

### 4.1 정체성 재정의
- As-Is
  - 공통 자동화 허브처럼 읽힌다.
- To-Be
  - 독립 실행형 분석 엔진으로 고정한다.
- 보완 액션
  - PRD, README, Workflow, AGENTS 문구 전면 수정

### 4.2 입력 경계 명확화
- As-Is
  - raw를 직접 흡수하는 엔진처럼 보일 수 있다.
- To-Be
  - 승인된 입력 자산만 읽는 구조로 정리
- 보완 액션
  - Data Contract, Scenario Spec, Architecture 문서 수정

### 4.3 승인과 handoff 분리
- As-Is
  - 분석 결과와 OPS 전달 결과 경계가 약하다.
- To-Be
  - `draft -> approved -> handoff` 단계 분리
- 보완 액션
  - handoff 계약 문서 신설
  - quality checklist와 runbook 수정

### 4.4 Builder 역할 축소
- As-Is
  - 결과 생성 흐름이 Sandbox 본체처럼 보일 수 있다.
- To-Be
  - Builder는 표현 단계로만 남긴다.
- 보완 액션
  - Workflow, Architecture, README에서 역할 분리 명시

### 4.5 Sandbox 범위 정리
- As-Is
  - Sandbox core와 무관한 다른 모듈 내용이 문서에 남아 있다.
- To-Be
  - Sandbox core 범위만 남긴다.
- 보완 액션
  - 범위 밖 spec 삭제
  - 범위 밖 예시 삭제
  - README/AGENTS 참조 목록 정리

## 5. 우선순위 로드맵

### Phase 0
- Sandbox 정체성 재정의
- 범위 밖 내용 제거
- handoff 규격 추가

### Phase 1
- 시나리오/승인/버전 구조 명확화
- 품질 체크와 runbook 보강

### Phase 2
- 승인 이력, 비교 리포트, 운영 자동화 확장

## 6. 결론
Sandbox 재구축의 핵심은 엔진을 더 크게 만드는 것이 아니라, Sandbox와 OPS의 경계를 분명히 하고 승인된 분석 결과만 연결되도록 구조를 다시 고정하는 데 있다.
