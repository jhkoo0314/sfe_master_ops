# Part2 모듈 역할 정의 고정본

작성일: 2026-03-16  
상태: `legacy` / 원문 상태: `고정(Freeze)`
현재 기준 문서: `docs/architecture/12_part2_status_source_of_truth.md`

---

## 0. 문서 목적

이 문서는 Part2에서 **역할 혼선을 막기 위한 공식 고정본**이다.

핵심은 3가지다.

1. 누가 계산하는지 고정  
2. 누가 검증하는지 고정  
3. 누가 보여주기만 하는지 고정

---

## 1. 시스템 한 줄 정의

`Adapter가 표준화하고, Module/KPI가 계산하고, OPS가 검증하고, Builder가 표현한다.`

공식 흐름:

`원천데이터 -> Adapter -> Module -> Result Asset -> OPS -> Builder`

내부 계산 흐름:

`원천데이터 -> Adapter -> Module Core -> KPI Engine -> Result Asset`

---

## 2. 공통 원칙 (전체 모듈 공통)

1. Builder 계산 금지  
2. OPS 계산 금지(검증/게이트 전담)  
3. KPI 엔진 계산 전담  
4. Module Service는 오케스트레이션 전담(입력 정리, 엔진 호출, 자산 조립)  
5. 모든 저장 경로는 `company_key` 기준

---

## 3. 레이어별 역할

### 3-1. Adapter 레이어

- 위치: `adapters/*`
- 하는 일:
  - 회사별 raw 차이를 표준 컬럼/표준 타입으로 정리
  - 원본값과 표준값을 함께 보존(추적 가능)
- 입력:
  - 회사 raw 파일
- 출력:
  - `ops_standard/{company_key}/...`
- 금지:
  - KPI 산식 계산
  - HTML 표현 로직

### 3-2. Module Core 레이어

- 위치: `modules/crm`, `modules/prescription`, `modules/sandbox`, `modules/territory`
- 하는 일:
  - 도메인 흐름 처리
  - KPI 엔진 호출 전 입력 구조 준비
  - Result Asset 형태로 조립
- 입력:
  - adapter 표준 데이터, 이전 모듈 자산
- 출력:
  - 각 모듈 Result Asset
- 금지:
  - Builder 템플릿 종속 계산

### 3-3. KPI Engine 레이어 (내부 계산 모듈)

- 위치: `modules/kpi/*_engine.py`
- 하는 일:
  - 공식 KPI 산식 계산
  - 계산 버전/규칙 추적
  - 상세/요약 지표 산출
- 입력:
  - module core가 정리한 표준 입력
- 출력:
  - KPI 결과 dict/row bundle (Result Asset 조립용)
- 금지:
  - 파일 I/O 중심 처리
  - 템플릿/화면 주입 로직

### 3-4. Result Asset 레이어

- 위치: `result_assets/*.py`, `data/ops_validation/{company_key}/*_result_asset.json`
- 하는 일:
  - 모듈 공식 결과의 계약 단위
  - OPS/Builder의 유일한 참조 입력
- 금지:
  - 임의 계산 로직 추가

### 3-5. OPS 레이어

- 위치: `ops_core/*`
- 하는 일:
  - 품질 상태 평가
  - 다음 모듈 전달 가능 여부 판단
  - 실행 게이트 역할
- 입력:
  - Result Asset
- 출력:
  - quality status, next modules, 운영 판단
- 금지:
  - 도메인 KPI 산식 계산

### 3-6. Builder 레이어

- 위치: `modules/*/builder_payload.py`, `modules/builder/*`, `templates/*`
- 하는 일:
  - 이미 계산된 결과를 템플릿 계약 형식으로 변환
  - 대용량은 chunk asset으로 분리
  - HTML 렌더링
- 입력:
  - Result Asset 또는 모듈이 만든 builder payload
- 출력:
  - `*_preview.html`, `*_assets/*.js`
- 금지:
  - 공식 KPI 계산/재계산

---

## 4. 모듈별 상세 역할

### 4-1. CRM 모듈

- 핵심 목적:
  - CRM 행동 데이터를 표준 8대 행동 + 공식 11 KPI 체계로 관리
- KPI 계산:
  - `modules/kpi/crm_engine.py`
- Service 역할:
  - CRM 입력 정리, 엔진 호출, `crm_result_asset` 조립
- Builder 역할:
  - `crm_result_asset` 기반 표현 payload 조립만 수행
- 금지:
  - Builder에서 CRM KPI 재계산

### 4-2. Prescription 모듈

- 핵심 목적:
  - 도매→약국→병원 흐름의 연결성/정합성/성과를 추적
- Core 규칙:
  - `flow_builder.py`: 흐름 조립/매핑 판정
  - `id_rules.py`: 범용 ID 규칙
- KPI 계산:
  - `modules/kpi/prescription_engine.py`
- Service 역할:
  - 입력 준비 + 엔진 호출 + 자산/payload 조립 경유
- Builder 역할:
  - 계산 없이 payload 조립/청크 분할
- 금지:
  - Builder에서 흐름 집계/품질 점수 재산식

### 4-3. Sandbox 모듈

- 핵심 목적:
  - CRM + Sales + Target 기반 성과 대시보드 분석
- KPI 계산:
  - `modules/kpi/sandbox_engine.py`
- 공식 KPI:
  - 상단 공식 KPI 6개(월/분기/연 단위)
- Service 역할:
  - 엔진 호출 + 보조지표 계산 + result asset 조립
- Builder 역할:
  - report payload 주입, 지점 chunk 지연 로딩
- 금지:
  - Sandbox에서 CRM KPI 산식 재계산

### 4-4. Territory 모듈

- 핵심 목적:
  - 권역/담당자/동선 관점의 실행력과 커버리지 분석
- KPI 계산:
  - `modules/kpi/territory_engine.py`
- Service 역할:
  - 엔진 호출 + result asset/payload 조립 경유
- Builder 역할:
  - 계산 없이 payload 조립/담당자·월 chunk 분할
- 금지:
  - Builder payload에서 거리/반경/달성률 등 계산

### 4-5. HTML Builder 모듈

- 핵심 목적:
  - 모듈별 payload를 최종 HTML로 표현
- 하는 일:
  - 템플릿 계약 준수
  - 분리 asset 복사/주입
- 금지:
  - 모듈 KPI 계산
  - OPS 판단 대체

---

## 5. 책임 경계 표 (요약)

- KPI 엔진:
  - 공식 계산 책임 O
  - 검증 책임 X
  - 표현 책임 X
- OPS:
  - 공식 계산 책임 X
  - 검증 책임 O
  - 표현 책임 X
- Builder:
  - 공식 계산 책임 X
  - 검증 책임 X
  - 표현 책임 O

---

## 6. 금지사항 (고정)

1. Builder에서 공식 KPI 계산/재계산 금지  
2. OPS에서 KPI 산식 계산 금지  
3. Sandbox에서 CRM KPI 산식 재계산 금지  
4. Result Asset 없이 화면 지표 먼저 맞추기 금지  
5. `company_key` 경로 원칙 무시 금지

---

## 7. 완료 판정 체크리스트

- 모듈 계산 코드가 `modules/kpi/*_engine.py`에 있는가  
- module service가 엔진 호출 경유로 동작하는가  
- builder_payload가 계산 없이 조립/분할만 하는가  
- OPS가 Result Asset 기준 검증만 하는가  
- `hangyeol_pharma`, `daon_pharma` 회귀가 통과했는가

---

## 8. 한 줄 결론

`Part2 고정 역할은 KPI=계산, OPS=검증, Builder=표현이며, module service는 이 세 층을 연결하는 오케스트레이터다.`
