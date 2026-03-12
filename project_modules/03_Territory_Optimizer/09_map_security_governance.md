# Territory Independent Build Security Governance

## 목적
Territory 독립 실행 환경에서 권한, 승인, 감사, 데이터 보호 기준을 정의한다.

## 데이터 보호
- 실험 데이터와 OPS 반영 데이터를 분리 저장한다.
- 승인 전 결과를 OPS 공식 폴더에 직접 쓰지 않는다.
- 기존 승인 버전 삭제 금지

## 접근 권한
- `analyst`: 시나리오 생성/실행
- `reviewer`: 품질 검토
- `approver`: 승인 버전 발행 및 handoff
- `ops_receiver`: 승인 패키지 수신만 가능

## 감사/추적
- `run_id`, `scenario_id`, `approved_version`, `approved_by`, `approved_at` 기록
- 무엇을 바꿨는지와 왜 바꿨는지 기록
- handoff 실패 이력 보관

## 민감정보 처리
- 병원/좌표 데이터는 최소 범위로 공유
- 외부 반출 시 식별 정보 마스킹 정책 적용

## 인코딩/문자 정책
- UTF-8 고정
- 승인 메타와 로그 파일도 UTF-8로 관리
