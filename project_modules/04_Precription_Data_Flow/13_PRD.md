# PRD - Prescription Data Flow Independent Build

## 0. 문서 정보
- 문서명: Prescription Data Flow 제품 요구사항(PRD)
- 버전: v3.0
- 기준일: 2026-03-12
- 범위: 독립 실행형 처방추적/검증/정산 파이프라인

## 1. 제품 정체성
Prescription Data Flow는 `도매 -> 약국 -> 병원/담당자` 흐름을 추적하고,
그 결과를 `검증 -> 쉐어 정산 -> KPI 발행 -> 승인 패키지 export`로 연결하는 독립 실행형 운영 파이프라인이다.

이 제품의 중심은 화면이 아니라 `재현 가능한 실행 흐름`이다.

우선순위:
1. 처방추적
2. claim 검증
3. 쉐어 정산
4. KPI 발행
5. 승인 패키지 export

## 2. 문제 정의
- 외부 처방데이터 구매 비용이 높아 상시 운영에 불리하다.
- 병원/담당자 단위 실적 주장을 내부 데이터만으로 검증할 기준이 약하다.
- 누락/미포착 케이스를 다음 분기 품질 개선으로 연결할 운영 루프가 필요하다.

## 3. 목표
### 3.1 현재 빌드 목표
- 승인된 입력 스냅샷만으로 파이프라인을 독립 실행할 수 있어야 한다.
- `merge -> mastering -> tracking -> share -> KPI -> validation/trace` 흐름이 한 번에 재현돼야 한다.
- 결과를 승인 가능한 공식 패키지로 export 할 수 있어야 한다.

### 3.2 다음 확장 목표
- overlap ON 정산 운영 고도화
- 승인 워크플로우와 버전 관리 강화
- 로컬 검토 화면 고도화
- 원천 업로드 자동화는 마지막 단계에서 검토

## 4. 고정 운영 플로우
1. `source_snapshot_load`
2. `ingest_merge`
3. `mastering`
4. `tracking_validation`
5. `share_settlement`
6. `kpi_publish`
7. `validation_trace`
8. `approval_package_export`

## 5. 핵심 비즈니스 규칙
- KPI 금액 기준: `amount_ship`
- 날짜 기준: `ship_date`
- 기간 기준: `year_month`, `year_quarter`, `year`
- 권역 기준: `territory_code`
- 쉐어 그레인: `year_quarter x territory_code x brand`
- 룰 누락 시 전분기 룰 연장(`extended`)
- 추적 시작 이전 기간 소급 귀속 금지
- 미포착 케이스는 `trace_log`로 남기고 다음 실행에서 다시 확인한다

## 6. 입력/출력 계약
### 6.1 입력
- 도매 출하 원천 스냅샷
- 병원/약국 주소 스냅샷
- 병원-문전약국 등록 데이터
- 담당자/권역 배정 데이터
- 분기 쉐어 룰
- 병원 claim 또는 내부 검증 대상 데이터

### 6.2 핵심 상세 산출물
- `fact_ship_pharmacy_mastered.*`
- `tracking_report.*`
- `share_settlement.*`
- `rep_kpi_month.*`, `rep_kpi_quarter.*`, `rep_kpi_year.*`
- `kpi_summary_month.*`, `kpi_summary_quarter.*`, `kpi_summary_year.*`
- `validation_report.*`
- `trace_log.*`

### 6.3 공식 export 패키지
- `prescription_result_asset.json`
- `prescription_builder_payload.json`
- `prescription_ops_handoff.json`

## 7. 구현 모듈
- `src/generate_synth.py`
- `src/ingest_merge.py`
- `src/mastering.py`
- `src/tracking_validation.py`
- `src/share_engine.py`
- `src/kpi_publish.py`
- `src/validation.py`
- `src/trace_log.py`
- 로컬 검토 화면이 필요하면 별도 app을 둘 수 있으나, 핵심 파이프라인의 필수 조건은 아니다.

## 8. 제품 경계
### 8.1 Prescription이 하는 일
- 원천을 합치고 해석 가능한 구조로 바꾼다.
- 추적과 검증을 수행한다.
- 쉐어 정산과 KPI 발행을 수행한다.
- 승인 가능한 결과 패키지를 만든다.

### 8.2 Prescription이 하지 않는 일
- OPS 대신 중앙 허브 역할을 하지 않는다.
- Builder처럼 최종 표현을 책임지지 않는다.
- UI가 없으면 실행되지 않는 구조로 만들지 않는다.

## 9. 현재 평가
잘한 점:
- 운영 규칙과 정산 흐름이 5개 모듈 중 가장 구체적이다.
- 추적, 검증, 정산, KPI가 한 제품 안에서 논리적으로 이어진다.
- 실무에서 바로 쓰기 좋은 감사 로그 사고가 있다.

아쉬운 점:
- 문서가 `Streamlit 운영 시스템`처럼 읽히는 부분이 있었다.
- 업로드 자동화와 수동 확정 UI가 제품 본체처럼 강조돼 있었다.
- 승인 전 상세 결과와 OPS 전달용 공식 결과가 분리되어 있지 않았다.

개선 방향:
- CLI/배치 중심으로 실행 모델을 고정한다.
- 로컬 검토 화면은 보조 수단으로 내린다.
- 승인 패키지와 OPS handoff 규격을 문서로 고정한다.

## 10. 완료 기준
1. 승인된 입력 스냅샷으로 독립 실행 가능
2. 핵심 상세 산출물 누락 0건
3. 보전성 위배 0건
4. `tracking_report`, `validation_report`, `trace_log` 생성 성공
5. `prescription_result_asset.json` 생성 성공
6. 승인 메타와 품질 상태가 포함된 handoff 패키지 생성 성공

## 11. 비범위
- 경쟁사 점유율/외부 시장데이터 통합
- 환자 레벨 추적
- OPS 내부 직접 재계산
- Builder 내부 계산 로직
- 파일 업로드 UI를 제품 핵심 완료 조건으로 간주하는 일

## 12. 테스트 전략
- `unit`
- `contract`
- `integration`
- `regression`
- `e2e`
- 선택적으로 `local_workbench_smoke`

Phase 종료 조건:
- 필수 테스트 100% 통과
- 필수 실패 0건
- 필수 산출물 누락 0건
- 공식 export 패키지 검증 통과

## 13. 리스크 및 대응
1. 원천 컬럼/인코딩 변동
   - 입력 스냅샷 단계에서 스키마/인코딩 검사 강화
2. 룰 관리 복잡도 증가
   - 룰 버전/상태/적용기간 관리 고정
3. 정산 신뢰성 이슈
   - 보전성/연장/중첩/재배분 회귀 테스트 상시 운영
4. 화면 의존도 과다
   - CLI 기준 완료를 우선 조건으로 고정
