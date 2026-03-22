# CRM KPI 거버넌스 복구 계획서 (Part 1 안정화 보강)

작성일: 2026-03-15

## 0. 문서 목적

이 문서는 CRM 11개 지표를 다시 `공식 기준`으로 고정하기 위한
코드 수정 계획서다.

핵심 목표는 하나다.

- CRM에서 계산한 지표를 단일 기준으로 만들고
- OPS는 전달/검증만 하고
- Sandbox/Builder는 다시 계산하지 않게 구조를 복구한다.

이 문서는 `수정 청사진 + 실행 결과`를 함께 기록하는 문서다.

---

## 0-1. 2026-03-15 실행 결과 요약 (Phase 1~6)

완료 상태:

- Phase 1 완료
  - `crm_result_asset`에 `metric_version`, `rep_monthly_kpi_11`, `monthly_kpi_11` 반영
- Phase 2 완료
  - CRM KPI 계산을 `modules/crm/service.py` + KPI 엔진 호출로 일원화
- Phase 2-1 완료
  - `modules/kpi/crm_engine.py` 추가
  - CRM 11 KPI 계산 소스를 엔진 한 곳으로 수렴
- Phase 3 완료
  - `activity_type_raw`, `activity_type_standard` 분리 추적
  - 표준 활동유형을 8대 행동(PT/Demo/Closing/Needs/FaceToFace/Contact/Access/Feedback) 기준으로 고정
- Phase 4 완료
  - `modules/crm/builder_payload.py`에서 CRM KPI 재계산 제거
  - Builder는 `crm_result_asset` 기반 읽기 전용 주입으로 전환
- Phase 5 완료
  - `modules/sandbox/service.py`에서 CRM KPI 재계산 제거
  - Sandbox는 CRM KPI 입력값(공식 자산)만 사용하도록 전환
- Phase 6 완료
  - `hangyeol_pharma`, `daon_pharma` 회귀 검증 완료
  - CRM -> Builder, CRM -> Sandbox KPI 전달 불일치 0건 확인

검증 요약:

- `scripts/validate_crm_with_ops.py` (2개 회사) 통과
- `scripts/validate_sandbox_with_ops.py` (2개 회사) 통과
- KPI 전달 정합성 비교: mismatch 0

---

## 1. 현재 문제 요약 (코드 검토 결과)

### 1.1 CRM Result Asset에 11 KPI가 공식 필드로 없음

- 파일: `result_assets/crm_result_asset.py`
- 현재는 월 방문/디테일콜 중심 요약만 있고,
  11 KPI를 공식 자산으로 내려주는 구조가 부족하다.

영향:
- 다음 모듈이 CRM 공식값을 안정적으로 재사용하기 어렵다.

### 1.2 Builder payload에서 KPI 재계산이 발생

- 파일: `modules/crm/builder_payload.py`
- `_score_scope` 내부에서 `HIR~SWR` 계열 계산이 수행된다.

영향:
- Builder가 표현 모듈이 아니라 계산 모듈처럼 동작한다.
- 문서 세계관(`Result Asset -> Builder`)과 충돌한다.

### 1.3 Sandbox에서 CRM KPI를 다시 계산

- 파일: `modules/sandbox/service.py`
- `hir/rtr/bcr/phr` 등을 Sandbox 내부 수식으로 다시 계산한다.

영향:
- CRM 단일 기준이 깨지고, 모듈별 지표 해석이 달라진다.

### 1.4 Adapter 단계에서 원본 행동 의미가 단순화됨

- 파일: `adapters/crm/adapter_config.py`
- 현재 `접근/대면/니즈환기` 등이 `방문/전화/행사/디지털`로 합쳐진다.

영향:
- 가중치가 달라도 최종 표현에서 행동 차이가 약해진다.

---

## 2. 복구 원칙 (이번 작업의 절대 기준)

1. CRM 11 KPI는 CRM 모듈에서만 계산한다.
2. Result Asset이 KPI의 유일한 기준 원천(Single Source of Truth)이다.
3. OPS는 계산기가 아니라 검증/전달 게이트다.
4. Sandbox/Builder는 KPI를 재계산하지 않고 읽기만 한다.
5. Adapter는 원본 의미를 보존하고, 표준화는 별도 필드로 분리한다.
6. KPI Engine은 독립 내부 모듈로 승격하되, 외부 공식 흐름은 바꾸지 않는다.

---

## 2-1. KPI Engine 아키텍처 결정

이번 계획에서 KPI는 `독립 내부 모듈`로 취급한다.

- 외부 공식 흐름(문서/운영 기준)은 유지:
  - `원천데이터 -> Adapter -> Module -> Result Asset -> OPS -> Builder`
- 내부 구현 흐름(모듈 내부 계산 경로):
  - `원천데이터 -> Adapter -> Module Core -> KPI Engine -> Result Asset -> OPS -> Builder`

중요:
- KPI Engine은 내부 모듈이므로 OPS 외부 계약 단위로 노출하지 않는다.
- 즉, OPS는 여전히 `Result Asset`만 본다.

---

## 3. 목표 지표 세트 (고정)

이번 계획의 공식 11 KPI:

- HIR
- RTR
- BCR
- PHR
- NAR
- AHS
- PV
- FGR
- PI
- TRG
- SWR

주의:
- 위 11개 정의/수식/가중치는 CRM 규칙 문서 기준으로만 관리한다.
- Builder/Sandbox 코드에 KPI 수식을 두지 않는다.

---

## 4. 단계별 코드 수정 계획

## 4-0. 이번 라운드 범위 고정

이번 라운드(즉시 실행)는 아래까지만 한다.

1. CRM KPI 복구
2. CRM KPI Engine 분리 구현 (재사용 가능한 계산 엔진)
3. CRM 결과 기준 Builder 정합화
4. CRM 기준 Sandbox 전달 정합화
5. 회사 2곳 회귀 검증

이번 라운드에서 하지 않는 일:

- 모듈 전체 공통 KPI 엔진 프레임워크 도입
- Sandbox/Territory/Prescription용 신규 KPI 엔진 분리 설계 확정

위 항목은 CRM 복구 검증 완료 후 다음 단계에서 설계한다.

## Phase 1. KPI 계약 고정 (문서/스키마)

작업:
- CRM 11 KPI 계약서 작성 또는 보강
  - 입력 필드
  - 결측 처리
  - 신뢰도 가중
  - 계산식 버전(`metric_version`)
- `CrmResultAsset` 스키마 확장
  - `rep_kpi_11` (담당자 x 월 또는 담당자 x 기간)
  - `monthly_kpi_11`
  - `metric_version`
  - `unscored_reason`/`data_quality_flags`

완료 기준:
- CRM Result Asset만 보면 11 KPI 원값을 재현 가능해야 한다.

---

## Phase 2. CRM 계산 엔진 일원화

작업:
- `modules/crm/service.py`에 11 KPI 계산 로직을 집중
- 기존 Builder 내 KPI 계산 로직은 CRM service로 이동
- `scripts/validate_crm_with_ops.py`에서 생성 결과를
  확장된 `crm_result_asset.json`으로 저장

완료 기준:
- `builder_payload.py` 없이도 CRM KPI 원값 JSON 확인 가능

---

## Phase 2-1. CRM KPI Engine 분리 구현 (이번 라운드 필수)

작업:
- CRM 전용 KPI 계산 엔진을 `독립 내부 모듈`로 분리
  - 예시 경로: `modules/kpi/crm_engine.py`
  - 대안 경로: `modules/crm/kpi_engine.py` (1차 적용 시)
- 11 KPI 계산 함수를 엔진 모듈에 집중
  - 입력: CRM 표준 활동/집계 입력
  - 출력: `rep x month`/`monthly` KPI 구조
- `modules/crm/service.py`는 엔진 호출자(오케스트레이터) 역할로 축소
- `builder_payload.py`/`sandbox`에서 KPI 수식 직접 사용 금지

완료 기준:
- CRM KPI 계산 소스가 `kpi_engine` 한 곳으로 수렴
- 다른 모듈에서 CRM KPI를 재사용할 때 엔진 결과만 참조

---

## Phase 3. Adapter 의미 보존 구조로 변경

작업:
- CRM 활동 표준에서 타입 필드 분리
  - `activity_type_raw` (원본)
  - `activity_type_standard` (표준)
- 기존 `activity_type_map`은 표준화에만 사용
- KPI 계산에서 어떤 필드를 쓰는지 명시적으로 고정

완료 기준:
- 행동 원문과 표준 표현이 동시에 추적 가능

---

## Phase 4. Builder 계산 제거 (읽기 전용화)

작업:
- `modules/crm/builder_payload.py`에서 KPI 수식 제거
- Builder는 `crm_result_asset`의 11 KPI를 그대로 주입
- Builder 파일 내 KPI 계산 코드 존재 여부 점검

완료 기준:
- Builder는 렌더링용 payload 조립만 수행

---

## Phase 5. Sandbox KPI 재계산 제거

작업:
- `modules/sandbox/service.py`의 CRM KPI 재계산 제거
- Sandbox는 CRM KPI를 입력으로 받아 조합/비교만 수행
- Sandbox 고유 해석지표는 이름을 분리해 오해 방지
  - 예: `sandbox_proxy_*`

완료 기준:
- Sandbox 출력에서 CRM KPI 값 출처가 CRM Result Asset임이 명확

---

## Phase 6. 검증/회귀 테스트

작업:
- 2개 회사(`daon_pharma`, `hangyeol_pharma`) 기준 회귀 검증
- 체크 항목:
  - CRM KPI 값이 Builder/Sandbox와 동일하게 전달되는지
  - Builder/Sandbox에 KPI 재계산 코드가 남아 있지 않은지
  - 문서와 경로가 최신인지

완료 기준:
- KPI 불일치 0건
- 지표 출처 설명 가능(추적 가능성 확보)

---

## Phase 7. 후속 설계 (CRM 검증 완료 후 착수)

작업:
- 모듈별 KPI 엔진 분리 설계 초안 작성
  - CRM KPI Engine (공식 11 KPI)
  - Sandbox KPI Engine (통합 KPI, CRM 공식지표 재계산 금지)
  - Territory/Prescription KPI Engine 필요 범위 정의
- 공통 인터페이스(입력/출력/버전/추적키) 제안
- OPS 전달 규약(`Result Asset only`)을 엔진별 계약으로 문서화

완료 기준:
- CRM 복구 결과를 기준으로 다음 단계 설계 문서가 분리 작성됨
- 엔진 분리 도입 범위와 도입 순서가 확정됨

현재 상태:
- Phase 7은 아직 미착수
- 다음 라운드에서 설계 문서 분리 작성 예정

---

## 5. 파일별 작업 책임 (예정)

핵심 수정:

- `adapters/crm/adapter_config.py`
- `adapters/crm/crm_activity_adapter.py`
- `modules/crm/schemas.py`
- `modules/kpi/crm_engine.py` (또는 1차로 `modules/crm/kpi_engine.py`)
- `modules/crm/service.py`
- `result_assets/crm_result_asset.py`
- `modules/crm/builder_payload.py`
- `modules/sandbox/service.py`
- `scripts/validate_crm_with_ops.py`
- `scripts/validate_sandbox_with_ops.py`

문서 동기화:

- `docs/ai/05_crm_rules.md`
- `docs/ai/04_module_map.md`
- `docs/ai/06_builder_and_outputs.md`
- `README.md`
- `RUNBOOK.md`
- `STRUCTURE.md`

---

## 6. 리스크와 대응

리스크 1: 기존 보고서 숫자와 달라질 수 있음
- 대응: `metric_version` 명시 + 변경 로그 제공

리스크 2: Sandbox 대시보드 일부 카드 공백 가능
- 대응: KPI 전달 필드 먼저 연결 후 카드 순차 전환

리스크 3: 회사별 컬럼 편차로 Adapter 오류 발생
- 대응: `activity_type_raw/standard` 분리 적용 후 샘플 검증

---

## 7. 구현 순서 요약 (실행용 체크리스트)

1. KPI 계약/스키마 고정
2. CRM KPI Engine 분리 구현
3. CRM service 계산 일원화 (엔진 호출 구조)
4. Adapter 원본/표준 타입 분리
5. Builder 계산 제거
6. Sandbox KPI 재계산 제거
7. 회귀검증 + 문서동기화
8. (후속) 모듈별 KPI 엔진 분리 설계 착수

---

## 8. KPI 엔진 확장 방향 (후속)

CRM 복구 완료 후, 같은 패턴으로 모듈별 엔진을 확장한다.

- `modules/kpi/crm_engine.py`
- `modules/kpi/sandbox_engine.py`
- `modules/kpi/territory_engine.py`
- `modules/kpi/prescription_engine.py`

원칙:
- 모듈별 KPI 계산은 해당 엔진에만 둔다.
- 서비스/빌더/OPS에는 계산식을 두지 않는다.
- OPS는 계속 `Result Asset` 기준 게이트 역할만 수행한다.

---

## 9. 한 줄 결론

`CRM 11 KPI를 CRM 모듈의 공식 결과자산으로 고정하고, Sandbox/Builder는 그 값을 재계산하지 않는 구조로 복구한다.`
