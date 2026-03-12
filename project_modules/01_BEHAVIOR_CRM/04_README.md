# CRM

CRM 재구축 전략과 KPI 로직을 정의한 기획/지표 설계 문서 프로젝트입니다.

## 목적
- 활동 강제 입력 중심 CRM에서 실행 지표 중심 운영 모델로 전환
- KPI 체계를 행동-운영-성과 계층으로 재정의
- 지표 계산 로직과 데이터 신뢰도 규칙을 일관되게 관리

## 폴더 구성
- `crm-rebuild-detailed-plan-v2.md`: CRM 재구축 상세 기획
- `crm-rebuild-metrics-logic-v2.md`: KPI/지표 계산 로직 명세

## 핵심 KPI 축
- 행동 계층: HIR, RTR, BCR, PHR
- 운영 계층: NAR, AHS, PV
- 성과 검증 계층: FGR, PI (및 경영 보고 보조 지표)

## 추천 읽기 순서
1. `crm-rebuild-detailed-plan-v2.md`
2. `crm-rebuild-metrics-logic-v2.md`

## 사용 방법
- 지표 정의 변경 시 상세기획 문서와 로직 문서를 동시에 업데이트합니다.
- 신뢰도/검증 규칙(verified/assisted/self_only 등) 수정 시 KPI 영향도를 함께 기록합니다.
- 운영 적용 전 샘플 기간을 지정해 지표 결과를 사전 검증하세요.

## 문서 관리 원칙
- 문서 인코딩: UTF-8 권장
- KPI 공식 변경은 버전 단위로 변경 이력(사유/영향도/검증 결과)을 남깁니다.
