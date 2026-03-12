# 04 Join Grain Policy

## 목적
Sandbox 분석 시나리오의 기준 행 단위와 조인키를 고정해 결과 흔들림을 줄인다.

## 마스터 Grain 정의
- 기본 grain 예시:
  - `hospital_id + metric_month + product_id`
- 시나리오별로 grain은 명시하되, 승인 전후에 바뀌면 안 된다.

## 조인키 규칙
- 이름 조인 금지, ID 조인 강제
- 월 포맷 통일 후 조인
- 조인 전 입력 자산을 동일 grain으로 정규화

## 사전 검증
- `scenario_id` 존재 여부
- 필수 키 null 비율
- 조인키 중복 건수
- 예상 행 수 대비 증감률

## Fail-Fast 임계치
- 필수 키 null 비율 > 임계치: 중단
- 조인키 중복 발견: 중단
- 조인 후 행 증가율 > 임계치: 중단
- 승인 패키지에 버전 메타 누락: handoff 중단

## 흔한 실패 패턴
- N:N 조인으로 행 폭증
- 월 포맷 불일치
- CRM/Sales/Target grain 불일치
- 시나리오 승인 전후 조인 기준 변경

## 로그 필수 항목
- `run_id`
- `scenario_id`
- `join_name`
- `used_keys`
- `before_count`
- `after_count`
- `failure_reason`
