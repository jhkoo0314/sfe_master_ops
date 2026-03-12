# Runbook - Prescription Data Flow Independent Execution

## 0) 목적
이 문서는 Prescription Data Flow를 `독립 실행형 파이프라인`으로 돌릴 때의 표준 절차다.
핵심은 화면이 아니라 `재현 가능한 실행 순서`를 지키는 것이다.

고정 흐름:
`merge -> mastering -> tracking_validation -> share_settlement -> kpi_publish -> validation_trace -> approval_package_export`

## 1) 실행 전 점검
1. Python/의존성 확인
   - `python -V`
   - `python -m pip -V`
2. 입력 스냅샷 확인
   - 도매 출하 원천
   - 병원/약국 주소 원천
   - 병원-문전약국 등록 데이터
   - 담당자/권역 배정 데이터
   - 분기 쉐어 룰
   - 병원 claim 입력
3. 인코딩 점검
   - 텍스트 파일 UTF-8 유지
   - `U+FFFD` 유입 금지
4. 승인 전제 확인
   - 이번 실행에 사용할 기준 룰 버전과 기준 파일 날짜를 기록

## 2) 표준 실행 절차 (CLI 우선)
1. raw/합성 입력 준비
   - `python -m src.generate_synth --seed 42 --valid-from 2026-01-01 --output-dir data/raw`
   - `python -m src.ingest_merge --raw-dir data/raw --output-dir data/raw --seed 42`
2. 마스터링
   - `python -m src.mastering --raw-dir data/raw --output-dir data/outputs --seed 42 --territory-missing-threshold 0.05`
3. 추적 검증
   - `python -m src.tracking_validation --input-dir data/outputs --output-dir data/outputs --min-coverage 0.75`
4. 쉐어 정산
   - `python -m src.share_engine --input-dir data/outputs --output-dir data/outputs`
5. KPI 발행
   - `python -m src.kpi_publish --input-dir data/outputs --output-dir data/outputs`
6. 검증/트레이스
   - `python -m src.validation --input-dir data/outputs --output-dir data/outputs`
   - `python -m src.trace_log --input-dir data/outputs --output-dir data/outputs`
7. 승인 패키지 export
   - 상세 테이블을 확인한 뒤 `prescription_result_asset.json`
   - `prescription_builder_payload.json`
   - `prescription_ops_handoff.json`
   - 를 생성한다.

## 3) 선택 절차 - 로컬 검토 화면
로컬 화면은 `있으면 편한 보조 도구`다.
핵심 파이프라인 완료 조건은 아니다.

가능한 용도:
- coverage/gap 확인
- 쉐어 적용 결과 검토
- KPI 요약 확인
- validation/trace 내려받기

금지할 오해:
- 화면이 있어야만 실행 가능한 구조로 만들지 않는다.
- 화면에서만 승인 가능하도록 설계하지 않는다.

## 4) 산출물 점검 체크리스트
### 4.1 상세 산출물
1. `tracking_report.*`
2. `share_settlement.*`
3. `rep_kpi_month.*`, `rep_kpi_quarter.*`, `rep_kpi_year.*`
4. `kpi_summary_month.*`, `kpi_summary_quarter.*`, `kpi_summary_year.*`
5. `validation_report.*`
6. `trace_log.*`

### 4.2 공식 패키지
1. `prescription_result_asset.json`
2. `prescription_builder_payload.json`
3. `prescription_ops_handoff.json`

### 4.3 필수 조건
1. `pharmacy_uid` 누락 0건
2. `share_rule_source` 허용값 외 0건
3. 보전성 위배 0건
4. `quality_status` 존재
5. `approval_status=approved` 또는 `rejected` 명시

## 5) 승인 절차
1. 상세 산출물 검토
2. validation 이슈 확인
3. 룰 버전/입력 버전 확인
4. 승인 메타 기록
   - `approved_version`
   - `approved_by`
   - `approved_at`
   - `approval_note`
5. handoff 준비 완료 시 `handoff_ready=true` 설정

## 6) 장애 대응
1. `ModuleNotFoundError: src`
   - 실행 위치와 프로젝트 루트 경로 점검
2. 한글 깨짐
   - 파일 저장 인코딩 UTF-8 재확인
3. 출력 누락
   - 상위 단계 산출물 존재 확인 후 재실행
   - 순서 유지: `tracking -> share -> kpi -> validation -> trace`
4. 보전성 위배
   - `share_engine` 입력 룰과 참여자 구성을 우선 점검
5. handoff 실패
   - 승인 메타, 품질 상태, 파일 누락 여부 확인

## 7) 권장 테스트 실행
1. `pytest -m unit`
2. `pytest -m contract`
3. `pytest -m integration`
4. `pytest -m regression`
5. `pytest -m e2e`
6. 선택적으로 `pytest -m local_workbench_smoke`

## 8) 릴리스 판정
`PASS` 조건:
1. 필수 테스트 100% 통과
2. 필수 산출물 누락 0건
3. 보전성 위배 0건
4. handoff 패키지 검증 통과

`FAIL` 조건:
1. 필수 산출물 누락
2. validation 치명 이슈 미해결
3. 승인 메타 누락
4. handoff 패키지 schema 불일치
