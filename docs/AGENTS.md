# Project Guardrails

이 저장소에서 SFE OPS 관련 구현을 할 때는 아래 원칙을 항상 먼저 따른다.

이 문서는 단순 메모가 아니라,
앞으로 코드와 문서를 볼 때 계속 따라야 하는 `통합 구현 규칙`이다.

---

## 1. 기준 문서 우선순위

문서가 많아서 충돌할 수 있으므로,
앞으로는 아래 순서로 기준을 본다.

1. `sfe_ops_master_docs` 아래 마스터 문서 세트
2. 이 `AGENTS.md`
3. 기존 `project_modules/00_SFE_OPS` 개별 문서

즉 기존 문서와 마스터 문서가 충돌하면
`sfe_ops_master_docs` 기준을 우선한다.

---

## 2. 가장 중요한 원칙

- 어떤 원천데이터도 바로 OPS로 보내지 않는다.
- 먼저 `adapter`가 원천데이터를 공통 규칙으로 가공한다.
- 모듈은 adapter가 정리한 입력으로 `Result Asset`을 만든다.
- OPS는 `Result Asset`만 검증하고 평가하고 다음 모듈 연결을 판단한다.

쉽게 말하면:

- `adapter` = 회사별/raw별 차이를 흡수하는 입구
- `module` = 자기 결과 자산을 만드는 처리기
- `OPS` = 결과 자산을 보고 연결 판단하는 중앙 엔진

공식 문장:

`원천데이터 -> adapter -> module -> Result Asset -> OPS`

---

## 3. SFE OPS 세계관

- 중심은 `Sandbox`가 아니라 `OPS Engine`이다.
- 5개 모듈은 OPS를 통해 연결되는 방사형 구조다.
- `Sandbox`는 중요한 통합 분석 모듈이지만 전체 허브는 아니다.
- OPS는 공통규칙엔진이고, Sandbox는 분석엔진이다.
- 모듈 간 기본 교환 단위는 raw가 아니라 `Result Asset`이다.

절대 잊지 말 것:

- OPS가 중심
- Sandbox는 핵심 모듈이지만 허브는 아님
- 모듈은 자기 계산을 하고, OPS는 연결을 판단함

---

## 4. 공식 통합 계획 순서

전체 SFE OPS 기획 기준의 공식 순서는 아래다.

1. 기준 문서 통합
2. CRM 공통축 안정화
3. Prescription 범용 구조 구축
4. Sandbox 통합 분석 표준화
5. Territory 확장
6. HTML Builder 범용 출력화

이 순서는 처음부터 다시 시작하는 공식 기준이다.

---

## 5. 모듈별 핵심 역할

### 5.1 Behavior CRM

- 행동프로파일과 KPI 구조를 만드는 출발 자산 모듈
- 병원/지점/담당자 공통 문맥의 시작점

### 5.2 SFE Sandbox

- OPS가 허용한 자산 조합을 분석하는 통합 분석엔진
- 전체 허브가 아님

### 5.3 Territory Optimizer

- Sandbox 결과를 공간 실행 관점으로 재해석하는 Allocation 모듈

### 5.4 Prescription Data Flow

- 도매 -> 약국 -> 병원 흐름을 검증 자산으로 만드는 Validation 모듈

### 5.5 HTML Builder

- Result Asset을 사람이 읽는 보고 자산으로 바꾸는 마지막 표현 모듈

---

## 6. Prescription 작업 시 비가역 원칙

- `Prescription`은 회사 맞춤부터 만들지 않는다.
- 회사 데이터가 없다는 가정에서도 먼저 작동하는 범용 규칙을 만든다.
- 병원 키는 새로 만들지 않고 CRM에서 이미 정의할 공통 `hospital_id`를 재사용한다.
- 약국 raw를 보고 범용 `pharmacy_id` 규칙을 먼저 만든다.
- 도매 raw를 보고 범용 `wholesaler_id` 규칙을 먼저 만든다.
- 그 다음 `도매 -> 약국 -> 병원` 흐름 연결 규칙을 만든다.
- 그 다음에 `prescription_raw_adapter`를 만든다.
- adapter보다 뒤쪽 pipeline/service를 먼저 확장하지 않는다.

즉 Prescription은 항상
`common-key-first`, `adapter-first`로 간다.

---

## 7. 구현 순서 원칙

새 모듈 작업은 가능하면 아래 순서를 지킨다.

1. 세계관/역할 확인
2. 공통 키 규칙 확인
3. raw adapter 설계
4. adapter 구현
5. module 내부 서비스 구현
6. Result Asset 생성
7. OPS 평가 연결
8. 다음 모듈 handoff 연결

이 순서가 어긋나면,
지금 작업이 앞단인지 뒷단인지부터 다시 확인한다.

---

## 8. 문서 작성 원칙

- 새 문서는 되도록 `sfe_ops_master_docs` 체계를 강화하는 방향으로만 추가한다.
- 기존 문서를 조금씩 늘려 기준이 퍼지게 만들지 않는다.
- 문서는 현재 상태 보고서가 아니라 공식 설계 문서로 쓴다.
- 구현 진행 상황보다 원칙과 순서를 먼저 적는다.

쉽게 말하면:

- 문서를 늘리기보다 기준을 모아야 한다.

---

## 9. 금지할 오해

- `Sandbox 중심 구조`로 이해하지 않는다.
- `원천데이터를 OPS가 직접 해석한다`고 가정하지 않는다.
- `회사 데이터가 와야만 범용 설계를 시작할 수 있다`고 가정하지 않는다.
- `adapter 없이 pipeline부터 만들면 된다`고 가정하지 않는다.
- `Builder가 중심 허브`라고 이해하지 않는다.

---

## 10. 기술 스택 해석 원칙

- Streamlit은 `운영 콘솔`이다.
- FastAPI/Pydantic은 `OPS Core`다.
- Polars는 `가공 처리 엔진`이다.
- Supabase PostgreSQL은 `운영 메타 저장소`다.

즉:

- UI는 엔진이 아니다.
- DB는 판단기가 아니다.
- 기술 스택은 세계관을 따라야 한다.

---

## 11. 설명 방식

- 비개발자도 이해할 수 있게 아주 쉽게 설명한다.
- 무엇을 만들 것인지와 어떤 순서로 만들 것인지를 분리해서 설명한다.
- 순서가 어긋났으면 바로 인정하고, 어떤 레이어가 앞이고 뒤인지 명확히 설명한다.
- 가능하면 어려운 용어 대신 역할 중심 표현을 쓴다.

---

## 12. 한 줄 결론

`앞으로 이 저장소의 SFE OPS 작업은 sfe_ops_master_docs를 기준으로, OPS 중심 세계관과 adapter-first 원칙을 지키면서 진행하고, 문서와 코드 모두 raw가 아니라 Result Asset 중심으로 설명하고 구현한다.`
