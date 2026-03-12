# Validation & QA Plan - Prescription Data Flow Independent Build

## 1) 목표
정확한 처방 복제가 아니라, `추적 재현성`, `정산 일관성`, `승인 가능한 결과 패키지`를 보장한다.

## 2) Validation 체크리스트

### A. 입력 계약
- 원천 파일 누락 여부
- 필수 컬럼 누락 여부
- lineage 컬럼 존재 여부
- 인코딩 이상 여부

### B. 마스터링/매핑
- 약국 UID 미부여 비율
- `territory_code` 미부여 비율
- `territory_source` 구성비
- 중복 의심 약국:
  - 동일 전화 + 주소 유사
  - 동일 주소 + 약국명 유사

### C. 출고 데이터 품질
- `amount_ship` 음수/0 이상치
- 분기 경계 누락/급변 탐지
- unknown wholesaler 건수

### D. 룰 적용 품질
- 룰 누락 목록(`quarter x territory x brand`)
- 전분기 연장 적용 목록 및 근거 룰 버전
- `ratio_hosp + ratio_clinic = 1.0` 검증
- `share_rule_source` 허용값 검증

### E. 정산 결과 품질
- Pre 총합 vs Post 총합 보전성
- Pool 합 vs 배분 합 일치
- 복수 의원 재배분 가중치 합 = 1.0
- overlap OFF 기본 경로에서 불필요한 중첩 처리 없음

### F. trace 운영 품질
- 미포착 케이스 로그 생성 규칙 충족 여부
- 상태 전이 유효성(`Unverified -> Inquired -> Confirmed/Rejected`)
- 미해결 케이스 누락 여부

### G. 승인 패키지 품질
- `prescription_result_asset.json` 생성 여부
- `prescription_builder_payload.json` 생성 여부
- `prescription_ops_handoff.json` 생성 여부
- 승인 메타 존재 여부
- `handoff_ready` 상태 검증

## 3) 최소 테스트 케이스
- TC1: 룰 없는 구간 -> Post=Pre
- TC2: 종병1+의원1 -> ratio대로 배분
- TC3: 종병1+의원3 -> 의원 몫을 의원 Base 비례로 재배분
- TC4: 룰 누락 + 전분기 룰 존재 -> 전분기 연장 적용
- TC5: unknown wholesaler 존재 -> LOG 생성 및 추적 루프 검증
- TC6: 승인 패키지 생성 -> handoff 메타 검증

## 4) 품질 게이트 판정
`PASS`
- 필수 테스트 통과
- 보전성 위배 0건
- 승인 패키지 3종 생성 성공

`FAIL`
- 필수 산출물 누락
- 치명 validation 이슈 미해결
- 승인 메타 누락

## 5) 한 줄 원칙
`상세 검증이 끝난 뒤에만 승인 패키지를 만든다.`
