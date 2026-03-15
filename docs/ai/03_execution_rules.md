# Execution Rules

## 목적

이 문서는 Codex가 구현이나 수정 작업을 할 때 따라야 할 공식 작업 순서를 정의한다.

## 기본 실행 순서

1. raw 입력 구조 확인
2. adapter 확인 또는 수정
3. module 로직 확인 또는 수정
4. Result Asset 확인
5. OPS 연결 확인
6. Builder payload 연결
7. UI 반영
8. 문서 갱신

앞단이 정리되지 않았는데 뒷단부터 만들지 않는다.

## 시스템 공식 흐름

`원천데이터 -> Adapter -> Module -> Result Asset -> OPS -> Builder`

## 운영 콘솔 역할

운영 콘솔은 아래를 담당한다.

- 회사 코드 입력
- 실행 모드 선택
- raw 업로드
- 실행 대상 확인
- 파이프라인 실행
- 산출물 확인
- HTML 열기/다운로드

주의:
업로드만 하면 세션 상태다.
실제 반영은 실행 시점이다.

## 기술 역할 분리

- UI: Streamlit 운영 콘솔
- OPS Core: 중앙 판단기
- Module: 계산과 도메인 처리
- DB: 이력과 메타 저장

원칙:
- UI는 판단기를 대신하지 않는다.
- DB는 도메인 계산을 대신하지 않는다.
- Builder는 계산기가 아니다.

## 회사 코드 원칙

새 작업도 항상 아래 구조를 따른다.

- `data/company_source/{company_key}/`
- `data/ops_standard/{company_key}/`
- `data/ops_validation/{company_key}/`

## 문서 갱신 대상

아래가 바뀌면 문서도 같이 수정한다.

- 실행 흐름
- 회사 코드 구조
- 산출물 이름
- Builder 흐름
- 콘솔 구조
- 보고서 구조

## 금지사항

- raw를 OPS로 직접 넘기기
- Builder에서 새 계산 넣기
- UI에서 도메인 판단 수행
- 경로 하드코딩
- 문서 없이 큰 방향 전환

## 결론

모든 구현은 adapter-first와 Result Asset 중심 흐름을 지키고, OPS는 검증 게이트로, Builder는 최종 표현 단계로 유지한다.