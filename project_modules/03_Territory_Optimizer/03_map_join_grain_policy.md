# Territory Independent Build Join And Grain Policy

## 목적
Territory 실험 단계와 OPS handoff 단계에서 행 단위와 조인키가 흔들리지 않도록 기준을 고정한다.

## 기준 Grain
- `scenario_assignment`: `scenario_id + hospital_id + rep_id`
- `route_activity`: `scenario_id + rep_id + metric_month + activity_date`
- `territory_zone`: `scenario_id + territory_id`
- `ops_handoff`: `company_key + approved_version + scenario_id`

## 조인키 우선순위
1. `hospital_id + scenario_id`
2. `rep_id + scenario_id`
3. `territory_id + scenario_id`
4. 이름 기반 조인은 표시용으로만 허용

## 사전 검증
- `scenario_id` 누락 여부
- 병원 중복 배정 여부
- 담당자 없는 병원 비율
- 권역 미배정 병원 비율
- 월 포맷 정합성

## Fail-Fast 임계치
- 시나리오 ID 누락 > 0건: 중단
- 동일 `scenario_id + hospital_id` 중복 배정 > 0건: 중단
- 승인 패키지에서 `approved_version` 누락 > 0건: handoff 중단
- 권역 미배정 병원 비율 > 임계치: 승인 불가

## 로그 필수 항목
- `run_id`
- `scenario_id`
- `approved_version`
- `join_name`
- `key_list`
- `before_count`
- `after_count`
- `failure_reason`
