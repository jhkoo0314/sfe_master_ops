# SFE OPS Technical Stack

작성일: 2026-03-10

## 0. 이 문서의 역할

이 문서는 SFE OPS의 `공식 기술 스택 문서`다.

이 문서는 아래를 설명한다.

1. 어떤 기술을 쓰는가
2. 왜 그 기술을 쓰는가
3. 그 기술이 OPS 세계관 안에서 어떤 역할을 맡는가
4. 기술 선택이 어떤 구현 원칙을 지켜야 하는가

---

## 1. 공식 기술 선택

SFE OPS의 공식 기술 스택은 아래다.

1. UI Layer: `Streamlit`
2. OPS Core API: `FastAPI`
3. Schema / Validation: `Pydantic`
4. Data Processing: `Polars`
5. Persistence: `Supabase PostgreSQL`
6. Package / Runtime: `uv`
7. Test: `pytest`
8. Excel/Spreadsheet IO: `openpyxl`, `fastexcel`

---

## 2. 기술 스택 한 줄 정의

`SFE OPS는 Streamlit을 운영 콘솔로, FastAPI와 Pydantic을 OPS 공통 엔진으로, Polars를 데이터 처리 엔진으로, Supabase PostgreSQL을 운영 메타 저장소로 사용하는 구조를 공식 기술 스택으로 삼는다.`

---

## 3. 기술 스택 선택 원칙

기술은 멋있어서 고르는 것이 아니다.

아래 원칙으로 고른다.

1. 비개발자 운영 흐름을 해치지 않아야 한다.
2. OPS 세계관과 역할 분리가 맞아야 한다.
3. raw adapter -> module -> Result Asset -> OPS 구조를 뒷받침해야 한다.
4. 나중에 실데이터가 와도 너무 크게 다시 만들지 않아야 한다.
5. 특정 회사 맞춤보다 범용 구조를 먼저 지지해야 한다.

---

## 4. 계층별 역할

### 4.1 UI Layer

기술:

- `Streamlit`

역할:

- 파일 선택
- 실행 요청
- 상태 확인
- 결과 미리보기
- 다운로드
- 운영자 설명 화면

하지 않는 일:

- 공통 상태 판단
- 연결 판단
- 키 거버넌스 판단
- 품질 게이트 판단

쉽게 말하면:

- Streamlit은 `운영 콘솔`
- OPS 엔진은 아님

### 4.2 OPS Core Layer

기술:

- `FastAPI`
- `Pydantic`

역할:

- Result Asset 입력 검증
- 상태 판단
- 연결 판단
- 품질 게이트 적용
- reasoning note 생성
- next action 반환
- 실행 이력과 자산 메타 관리

쉽게 말하면:

- FastAPI/Pydantic 조합은 `중앙 판단기`

### 4.3 Module Processing Layer

기술:

- `Python`
- `Polars`
- 일부 보조 라이브러리

역할:

- adapter 출력 처리
- 표준화
- 집계
- 요약
- Result Asset 생성

중요:

- 계산과 도메인 규칙은 모듈에 있다.
- OPS는 판단과 연결을 맡는다.

### 4.4 Persistence Layer

기술:

- `Supabase PostgreSQL`
- 필요 시 `Supabase Storage`

역할:

- 실행 이력 저장
- 자산 메타 저장
- 상태 저장
- 산출물 참조 저장

하지 않는 일:

- 도메인 계산 로직 수행
- OPS 판단 로직 대체

---

## 5. 각 기술을 쓰는 이유

### 5.1 Streamlit

쓰는 이유:

1. 비개발자 운영 화면을 빠르게 만들기 좋다.
2. 업로드/실행/확인 흐름에 강하다.
3. 운영 콘솔 역할에 집중시키기 좋다.
4. 프론트엔드 재개발 부담을 줄인다.

주의:

- Streamlit이 계산 엔진이 되면 안 된다.

### 5.2 FastAPI

쓰는 이유:

1. OPS Core를 중앙 API로 분리하기 좋다.
2. 상태/연결/평가 API를 명확하게 만들기 쉽다.
3. 테스트와 확장이 비교적 쉽다.

### 5.3 Pydantic

쓰는 이유:

1. Result Asset 계약을 강하게 검증하기 좋다.
2. 모듈 입력/출력을 설명 가능한 구조로 만들기 좋다.
3. 상태값, 연결값, payload 구조를 일관되게 다루기 좋다.

### 5.4 Polars

쓰는 이유:

1. 엑셀/CSV 기반 처리에 강하다.
2. join, aggregation, filtering이 많은 구조에 잘 맞는다.
3. adapter와 standardization 계층을 분명하게 만들기 좋다.

### 5.5 Supabase PostgreSQL

쓰는 이유:

1. 운영 메타와 이력을 저장하기 좋다.
2. Postgres 기반이라 구조가 안정적이다.
3. 로컬 전용 설계보다 실운영 확장성이 좋다.

### 5.6 uv

쓰는 이유:

1. 의존성 관리와 실행 흐름이 단순하다.
2. 프로젝트 실행 명령을 통일하기 쉽다.

### 5.7 pytest

쓰는 이유:

1. fixture 중심 검증이 쉽다.
2. adapter, module, API, handoff를 층별로 나눠 검증하기 좋다.

---

## 6. 기술 스택과 세계관의 연결

기술 스택도 세계관을 따라야 한다.

즉 아래가 중요하다.

1. UI는 엔진이 아니다.
2. DB는 판단기가 아니다.
3. adapter는 회사별 차이를 흡수한다.
4. module은 Result Asset을 만든다.
5. OPS Core는 Result Asset만 검증하고 연결을 판단한다.

기술이 아무리 좋아도 이 역할 분리가 깨지면 SFE OPS가 아니다.

---

## 7. 기술 스택 문서에서 금지할 오해

아래 식으로 이해하면 안 된다.

1. Streamlit이 중앙 허브다
2. Supabase가 OPS를 대신한다
3. FastAPI가 raw를 직접 해석해야 한다
4. Polars만 쓰면 설계가 자동으로 좋아진다
5. 기술 스택이 세계관보다 먼저다

---

## 8. 한 줄 결론

`SFE OPS의 공식 기술 스택은 Streamlit 운영 콘솔, FastAPI/Pydantic 기반 OPS Core, Polars 처리 계층, Supabase PostgreSQL 저장 계층을 중심으로 하며, 이 기술들은 모두 OPS 중심 세계관과 adapter-first 구조를 지키는 방향으로만 사용한다.`
