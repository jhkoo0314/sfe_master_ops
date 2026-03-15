# Part2 모듈별 KPI 엔진 분리 설계 계획

작성일: 2026-03-15
최종 업데이트: 2026-03-15

## 0. 상태 선언

- Part1은 `문서화/구조 고정 + CRM KPI 거버넌스 복구(Phase 1~6)`까지 완료로 본다.
- 이 문서는 Part2에서 시작하는 `모듈별 KPI 엔진 분리`의 실행 기준 문서다.
- 현재 확정 사실:
  - CRM 공식 11 KPI는 `modules/kpi/crm_engine.py`가 계산한다.
  - Builder는 CRM KPI를 재계산하지 않는다.
  - Sandbox도 CRM KPI를 재계산하지 않는다.

---

## 1. 문서 목적

이 문서의 목적은 3가지다.

1. KPI 계산 책임을 모듈 서비스에서 KPI 엔진으로 분리한다.
2. 공식 KPI와 화면 보조지표의 경계를 고정한다.
3. OPS/Builder 역할을 흔들지 않고 분리 순서를 확정한다.

핵심은 `외부 흐름 유지 + 내부 계산 책임 분리`다.

---

## 2. 용어 정의

## 2-1. 공식 KPI

- 결과 비교, 운영 판단, 성과 설명에 쓰는 공식 점수
- 반드시 KPI 엔진에서 계산
- Result Asset에 버전과 함께 저장

## 2-2. 보조/표현 지표

- 대시보드 가독성, 정렬, 하이라이트, 상관표 같은 화면 보조값
- 공식 KPI를 바꾸지 않는 범위에서 모듈 서비스/Builder payload에서 생성 가능

## 2-3. KPI 엔진

- 공식 KPI 산식 전담 내부 모듈
- OPS와 Builder의 직접 입력이 아니라 모듈 서비스 내부 호출 대상

## 2-4. 모듈 서비스

- 입력 정리 -> KPI 엔진 호출 -> Result Asset 조립 담당

---

## 3. 고정 원칙

1. 외부 공식 흐름 유지
   - `원천데이터 -> Adapter -> Module -> Result Asset -> OPS -> Builder`
2. 내부 계산 흐름 분리
   - `원천데이터 -> Adapter -> Module Core -> KPI Engine -> Result Asset`
3. KPI 엔진은 내부 모듈 (OPS 계약 단위로 직접 노출하지 않음)
4. Builder는 계산 금지
5. Sandbox는 CRM 공식 KPI 재계산 금지
6. 모든 실행/저장은 `company_key` 기준

---

## 4. 모듈별 엔진 분리 범위

## 4-1. CRM KPI Engine (운영 반영 완료)

- 경로: `modules/kpi/crm_engine.py`
- 역할: CRM 공식 11 KPI 계산
- 출력: `rep_monthly_kpi_11`, `monthly_kpi_11`, `metric_version`
- 상태: 완료/운영 반영

## 4-2. Sandbox KPI Engine (Part2 1순위)

- 신규 경로: `modules/kpi/sandbox_engine.py`
- 역할:
  - Sandbox 고유 공식 KPI 계산 전담
  - CRM KPI는 입력값 사용만 허용
- 금지:
  - CRM KPI(HIR/RTR/BCR/PHR/NAR/AHS/PV/FGR/PI/TRG/SWR) 재산식

## 4-3. Territory KPI Engine (Part2 2순위)

- 신규 경로: `modules/kpi/territory_engine.py`
- 역할: 권역 실행/커버리지/동선 효율 공식 KPI 계산

## 4-4. Prescription KPI Engine (Part2 3순위)

- 신규 경로: `modules/kpi/prescription_engine.py`
- 역할: 처방 흐름/완결성/성과 공식 KPI 계산

---

## 5. 공통 인터페이스 계약(초안)

모든 엔진은 아래 형태를 공통으로 맞춘다.

- 입력
  - 표준화 레코드(list 또는 집계 dict)
  - `metric_version`
  - 선택: 회사별 가중치/룰 설정
- 출력
  - 엔터티 x 월 KPI detail
  - 월 요약 KPI
  - `unscored_reasons`
  - 계산 메타(`metric_version`)

함수 시그니처(초안):

```python
compute_<module>_kpi_bundle(input_records, *, metric_version="...") -> (detail_rows, monthly_rows, metric_version)
```

---

## 6. 책임 분리 표

- KPI 엔진이 하는 일:
  - 공식 KPI 산식 계산
  - 결측/신뢰도 처리
  - 버전 부여
- 모듈 서비스가 하는 일:
  - 입력 정리/그룹핑
  - KPI 엔진 호출
  - Result Asset 조립
- Builder가 하는 일:
  - payload 조립/템플릿 주입
  - 공식 KPI 재계산 금지

---

## 7. Phase7 실행 순서

## 7-1. Sandbox 엔진 분리

1. Sandbox 공식 KPI 목록 확정
2. `modules/kpi/sandbox_engine.py` 생성
3. `modules/sandbox/service.py`에서 공식 KPI 계산부를 엔진 호출로 전환
4. Result Asset에 `metric_version`/추적 필드 보강

완료 기준:
- Sandbox 공식 KPI 계산 코드가 엔진 파일로 이동
- 서비스는 오케스트레이터 역할만 수행

Sandbox 모듈 분리 완료 기준(확정):

1. 공식 KPI 계산 위치
   - `modules/kpi/sandbox_engine.py`에서 수행
2. CRM KPI 재계산 금지
   - Sandbox에서 CRM KPI 산식 재계산 코드 없음
3. 결과 정합성
   - `hangyeol_pharma`, `daon_pharma` 회귀 검증 `pass`
4. Builder 영향 없음
   - Sandbox 포함 최종 HTML 5종 생성 검증 `pass`
5. 문서 동기화
   - 본 문서 + 실행계획 + 운영 문서에 상태 반영

상태: `완료 (2026-03-15)`

Sandbox 공식 KPI 목록(고정):

1. `monthly_sales` (월 전사 매출)
2. `monthly_target` (월 전사 목표)
3. `monthly_attainment_rate` (월 목표달성률)
4. `quarterly_sales` (분기 전사 매출)
5. `quarterly_target` (분기 전사 목표)
6. `annual_attainment_rate` (연간 목표달성률)

## 7-2. Territory 엔진 뼈대 생성

1. KPI 목록/정의 확정
2. `modules/kpi/territory_engine.py`에 인터페이스 고정
3. 기존 서비스에서 호출 경로 연결

완료 기준:
- Territory 공식 KPI 계산 위치가 명시적으로 분리됨

## 7-3. Prescription 엔진 뼈대 생성

1. KPI 목록/정의 확정
2. `modules/kpi/prescription_engine.py` 인터페이스 고정
3. 기존 서비스 호출 연결

완료 기준:
- Prescription 공식 KPI 계산 위치가 명시적으로 분리됨

---

## 8. 검증 기준

회귀 검증 대상 회사:

- `hangyeol_pharma`
- `daon_pharma`

검증 통과 기준:

1. CRM KPI 전달 불일치 0건 유지
2. Sandbox/Territory/Prescription 공식 KPI 출처 추적 가능
3. Builder 파일에 공식 KPI 산식 없음
4. OPS는 Result Asset 기준 판단만 수행

---

## 9. 금지사항

1. KPI 산식을 Builder로 다시 올리지 않는다.
2. Sandbox에서 CRM KPI를 다시 계산하지 않는다.
3. OPS를 계산 엔진처럼 확장하지 않는다.
4. 회사별 raw 차이를 무시한 단일 하드코딩을 하지 않는다.
5. Result Asset 없이 화면 지표를 먼저 맞추지 않는다.

---

## 10. 승인 필요 항목

Phase7 착수 전에 아래 3개를 확정해야 한다.

1. Sandbox 공식 KPI 목록
2. Territory 공식 KPI 목록
3. Prescription 공식 KPI 목록

확정 전에는 `엔진 인터페이스 뼈대 + 버전 규칙`까지만 먼저 고정한다.

---

## 11. 한 줄 결론

`Part2 KPI 엔진 분리는 공식 OPS 흐름을 바꾸지 않고, 모듈 내부 계산 책임을 엔진으로 분리해 KPI 출처를 추적 가능하게 만드는 작업이다.`
