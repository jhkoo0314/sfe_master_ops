# 10 Security Governance

## 목적
Sandbox 독립 실행 환경에서 승인, 권한, 감사, 데이터 보호 기준을 정의한다.

## 데이터 보호 정책
- 실험 결과와 OPS 전달 결과를 분리 저장한다.
- 승인 전 결과를 OPS 공식 결과로 사용하지 않는다.
- 기존 승인 버전 삭제/초기화 금지

## 접근 권한
- `analyst`: 시나리오 생성/실행
- `reviewer`: 품질 검토
- `approver`: 승인 및 handoff export
- `ops_receiver`: 승인 패키지 수신

## 감사/추적
- `run_id`, `scenario_id`, `approved_version`, `approved_by`, `approved_at` 기록
- 변경 사유와 영향 범위를 기록
- handoff 실패 이력 보관

## 인코딩/문자 정책
- UTF-8 고정
- 승인 메타와 로그도 UTF-8 유지

## 보안 운영 수칙
- 민감정보 마스킹
- 외부 반출 최소화
- 승인 없는 handoff 금지
