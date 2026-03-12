# HTML Output Utility Decision Log

작성일: 2026-03-12

## 1. 문서 목적

이 문서는 HTML Builder를 `독립 서비스`가 아니라 `공통 출력 유틸`로 다시 정리하면서,
꼭 고정해야 하는 핵심 결정을 남기는 기록이다.

## 2. 기록 방식

- 번호: `DEC-XXX`
- 상태: `Accepted | Deprecated`
- 필수 항목:
  - Context
  - Decision
  - Consequences

## 3. 결정 로그

### DEC-001: Builder는 독립 제품이 아니다
- Status: Accepted
- Context:
  - 현재 역할은 계산보다 출력 자동화에 가깝다.
- Decision:
  - Builder를 독립 제품이나 독립 서비스로 키우지 않는다.
- Consequences:
  - 문서는 공통 출력 계층 기준으로 유지한다.
  - 과도한 API/운영 문서는 범위 밖으로 둔다.

### DEC-002: Builder는 독립 Result Asset을 만들지 않는다
- Status: Accepted
- Context:
  - 공식 결과는 계산 모듈이 만든다.
- Decision:
  - Builder 전용 Result Asset을 두지 않는다.
- Consequences:
  - Builder는 승인된 결과나 payload만 읽는다.
  - 공식 결과 책임은 모듈에 남는다.

### DEC-003: 템플릿이 먼저이고 데이터는 그 계약에 맞춘다
- Status: Accepted
- Context:
  - 현재도 보여줄 화면 기준으로 템플릿을 정하고 데이터 구조를 맞춘다.
- Decision:
  - Builder를 `템플릿 주도형 출력 단계`로 본다.
- Consequences:
  - Template Contract 문서를 유지한다.
  - 새 출력 유형은 계약부터 정의한다.

### DEC-004: Builder 안에서 새 계산을 하지 않는다
- Status: Accepted
- Context:
  - 계산이 Builder 안으로 들어오면 역할이 커지고 유지보수가 어려워진다.
- Decision:
  - Builder는 주입과 표현만 담당한다.
- Consequences:
  - 계산은 모듈 또는 OPS 이전 단계에서 끝낸다.
  - 무거운 상세는 다운로드 참조로 뺀다.

### DEC-005: Template Pack은 선택적으로 관리한다
- Status: Accepted
- Context:
  - 출력물 종류가 늘어나면 템플릿 관리 기준이 필요하다.
- Decision:
  - 템플릿은 파일/팩 단위로 관리하되 별도 플랫폼으로 키우지 않는다.
- Consequences:
  - 버전은 단순하게 유지한다.
  - 템플릿 변경은 계약 문서와 같이 업데이트한다.

