# Prescription Data Flow Rebuild Requirements

## 0) 문서 목적
이 문서는 Prescription Data Flow를 `독립 실행형 추적/검증/정산 파이프라인`으로 다시 세울 때 필요한 요구사항을 정리한다.

핵심은 다음 세 가지다.

1. 파이프라인이 화면 없이도 돌아가야 한다.
2. 상세 산출물과 공식 승인 패키지를 분리해야 한다.
3. 승인된 결과만 나중에 OPS에 넘겨야 한다.

## 1) 제품 재정의
### 1.1 최상위 목적
- 1순위 목적: 처방추적
- 2순위 목적: claim 검증
- 3순위 목적: 쉐어 정산
- 4순위 목적: KPI 발행
- 5순위 목적: 승인 패키지 export

### 1.2 새 기준 한 줄
`Prescription은 승인된 입력을 받아 추적/정산/KPI를 계산하고, 승인된 결과 패키지를 export 하는 독립 실행형 운영 파이프라인이다.`

## 2) 필수 운영 시나리오
### 2.1 표준 실행 흐름
1. 원천 스냅샷 준비
2. 병합 원천 로우 생성
3. 마스터링
4. 추적 검증
5. 쉐어 정산
6. KPI 발행
7. validation/trace 생성
8. 승인 패키지 export

### 2.2 꼭 답해야 하는 운영 질문
- 병원이 주장한 실적은 출하 데이터로 설명 가능한가?
- 누락은 어느 구간에서 생겼는가?
- 전분기 연장이 맞게 적용되었는가?
- 정산 후 총량 보전이 유지되는가?
- 이번 실행 결과를 공식 패키지로 넘겨도 되는가?

## 3) 입력 요구사항
- 도매 출하 원천
- 병원/약국 주소 원천
- 병원-문전약국 등록 데이터
- 담당자/권역 배정 데이터
- 분기 쉐어 룰
- 병원 claim 또는 추정량 입력
- 각 입력의 기준일, 버전, 출처 파일 정보

## 4) 엔진 요구사항
### 4.1 고정 단계
1. `generate_or_ingest`
2. `ingest_merge`
3. `mastering`
4. `tracking_validation`
5. `share_settlement`
6. `kpi_publish`
7. `validation_trace`
8. `approval_package_export`

### 4.2 단계별 요구사항
- `mastering`
  - `pharmacy_uid`, `territory_code` 부여
  - lineage 유지
- `tracking_validation`
  - `tracked_amount`, `coverage_ratio`, `gap_amount`, `tracking_quality_flag`
- `share_settlement`
  - `direct`, `extended`, `none` 구분
  - 보전성 유지
- `kpi_publish`
  - 월/분기/연 KPI 6종과 요약 3종 생성
- `validation_trace`
  - validation 이슈와 trace 상태전이 생성
- `approval_package_export`
  - 상세 산출물 요약
  - 승인 메타 연결
  - OPS/Builder 전달용 파일 생성

## 5) 산출물 요구사항
### 5.1 상세 산출물
- `tracking_report.*`
- `share_settlement.*`
- `rep_kpi_month.*`, `rep_kpi_quarter.*`, `rep_kpi_year.*`
- `kpi_summary_month.*`, `kpi_summary_quarter.*`, `kpi_summary_year.*`
- `validation_report.*`
- `trace_log.*`

### 5.2 공식 승인 패키지
- `prescription_result_asset.json`
- `prescription_builder_payload.json`
- `prescription_ops_handoff.json`

### 5.3 필수 메타
- `run_id`
- `input_manifest`
- `rule_version`
- `quality_status`
- `approval_status`
- `approved_version`
- `approved_by`
- `approved_at`
- `handoff_ready`

## 6) 로컬 검토 화면 요구사항
로컬 검토 화면은 있을 수 있지만 제품 본체는 아니다.

허용:
- 결과 조회
- 필터링
- 다운로드
- 품질 상태 확인

비허용:
- 화면이 없으면 실행이 안 되는 구조
- 화면에서만 가능한 핵심 승인 로직
- 화면을 결과 패키지 대신 공식 산출물로 간주하는 일

## 7) 품질 게이트 요구사항
### 7.1 필수 게이트
- 입력 계약 통과
- 마스터링 품질 통과
- tracking 계산 통과
- 정산 보전성 통과
- KPI 일관성 통과
- validation 치명 이슈 확인
- 공식 패키지 schema 통과

### 7.2 rejection 조건
- 필수 산출물 누락
- 보전성 위배
- 승인 메타 누락
- `quality_status=FAIL`
- handoff 파일 누락

## 8) 문서/거버넌스 요구사항
- 비즈니스 규칙, 데이터 사전, 실행 절차, 게이트 문서가 같은 용어를 써야 한다.
- 승인자는 결과 패키지 기준으로 기록한다.
- 상세 산출물 수정 이력과 승인 이력을 분리해 남긴다.

## 9) 재빌드 우선순위
1. 입력/계약 고정
2. 핵심 엔진 안정화
3. 승인 패키지 표준화
4. OPS handoff 문서화
5. 선택 기능 추가

## 10) Definition of Done
- 독립 실행 가능
- 상세 산출물 생성 성공
- 승인 패키지 3종 생성 성공
- 로컬 화면 없이도 완료 가능
- OPS handoff 검증 통과
