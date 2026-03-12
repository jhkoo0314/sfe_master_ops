# Synthetic Data Spec — Prescription Data Flow (MVP)

## 1) 목적
현실적인 난이도(의원 파편화, 룰 변경, 전분기 연장, 미포착)를 포함한 가상 데이터로
정산 로직이 운영 가능함을 증명한다.

## 2) 기본 스케일(권장)
- territory: 12
- reps: 60
- wholesalers: 12
- brands: 20
- hospitals: 종병 30 / 의원 900
- pharmacies: 2500
- 기간: 8개 분기(2년)

## 3) 생성 규칙
- brand별 성장/정체/하락 패턴 부여(계절성 포함)
- 종병 영향권은 특정 brand 볼륨이 크게 나오도록 구성
- 의원은 소액/분산(긴 꼬리)
- 미포착:
  - 일부 약국은 특정 분기 `UNKNOWN` wholesaler로 생성
  - 또는 출고 누락 상태로 생성
- 문전약국 제출:
  - 의원 1~3개/병원
  - 종병 8~12개/병원
- 쉐어 룰:
  - 전체 key의 20~30%에 룰 생성
  - 그중 10%는 다음 분기 룰 누락으로 전분기 연장 검증
  - 복수 의원 참여(2~5명) 케이스 포함

## 4) 재현성
- random seed 파라미터 제공
- 동일 seed/파라미터면 동일 결과 생성
- 재현성 해시는 핵심 산출 테이블의 안정 정렬 후 JSON 직렬화 SHA-1로 계산
- 실행 메타데이터는 별도 파일 `data/outputs/generate_synth_run_meta.json`에 저장
  - seed / 분포 파라미터 / SOP 매핑 점검 결과 / 테이블별 해시 / aggregate hash

## 5) 산출 파일(예시)
- data/raw/fact_ship_pharmacy.parquet
- data/dim/dim_pharmacy_master.parquet
- data/dim/dim_hospital_master.parquet
- data/map/map_front_pharmacy.parquet
- data/rules/rule_share_quarterly.parquet
- data/log/log_wholesaler_trace.parquet
- data/raw/source_mapping_checklist.parquet
- data/outputs/generate_synth_run_meta.json

## 6) 분포 파라미터 표준
- unknown 비율: `--unknown_wholesaler_rate`
- 수량 범위: `--qty_min`, `--qty_max`
- 단가 범위: `--unit_price_min`, `--unit_price_max`
- 브랜드 분포 집중도(Dirichlet alpha): `--brand_concentration`
- 룰 커버리지/연장 비율: `--rule_coverage_rate`, `--rule_extend_rate`
- 종병 배분비 범위: `--ratio_hosp_min`, `--ratio_hosp_max`

## 7) SOP 1:1 매핑 점검표
- 원천별 canonical column 기준으로 후보 매핑 성공 여부를 `source_mapping_checklist`로 기록
- `matched_flag=False` 항목이 1건이라도 있으면 생성 중단(ValueError)
