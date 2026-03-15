# Project Guardrails

## 1. 문서 우선순위

판단 우선순위는 아래 순서를 따른다.

1. 마스터 문서 세트
2. 루트 `AGENTS.md`
3. `docs/ai/` 폴더
4. 구현 코드와 보조 문서

문서 허브 인덱스는 `docs/README.md`다.
OPS 관련 작업 전에는 `docs/ai/00_start_here.md`를 먼저 읽는다.

---

## 2. 가장 중요한 한 줄

`원천데이터 -> Adapter -> Module -> Result Asset -> OPS -> Builder`

원칙:
- raw를 OPS로 바로 보내지 않는다
- adapter가 먼저 정리한다
- module은 자기 Result Asset을 만든다
- OPS는 Result Asset만 보고 판단한다
- Builder는 마지막 표현 단계다

---

## 3. 전역 작업 원칙

- 회사가 바뀌면 `공통 틀 + 얇은 커스텀` 방식으로 간다
- 억지로 100% 범용처럼 보이게 만들지 않는다
- 실제 저장소 구조와 다른 이상적 구조를 상상해 쓰지 않는다
- 큰 방향 전환은 문서 기준 없이 진행하지 않는다

---

## 4. 구현 순서 원칙

1. raw 입력 구조 확인
2. adapter 확인 또는 수정
3. module 로직 확인 또는 수정
4. Result Asset 확인
5. OPS 연결 확인
6. Builder payload 연결
7. UI 반영
8. 문서 갱신

---

## 5. company_key 원칙

모든 실행과 저장은 `company_key` 기준이다.

- `data/company_source/{company_key}/`
- `data/ops_standard/{company_key}/`
- `data/ops_validation/{company_key}/`

회사명은 표시용이다.

---

## 6. 문서 갱신 원칙

아래가 바뀌면 문서도 같이 수정한다.

- 실행 흐름
- 회사 코드 구조
- 산출물 이름
- Builder 흐름
- 콘솔 구조
- 보고서 구조

---

## 7. 설명 방식

- 비개발자도 이해할 수 있게 쉽게 설명한다
- 역할 중심으로 설명한다
- 왜 이렇게 바꾸는지 짧게 같이 말한다
- 현재 상태와 앞으로 할 일을 구분해서 말한다

---

## 8. 금지사항

- raw를 OPS로 직접 넘기기
- Builder를 계산 엔진처럼 사용하기
- UI에서 도메인 판단 수행하기
- company_key 구조를 무시한 경로 하드코딩
- 문서 없는 큰 방향 전환

For OPS-related work, follow the startup procedure in `SKILL.md` first, then read `docs/ai/00_start_here.md`.
