# Company Registry / Fixed Company Key Plan

작성일: 2026-03-19  
상태: `draft`

이 문서는 Sales Data OS에서 회사 식별 방식을 `자유 입력 company_key`에서
`회사 등록 + 고정 company_key` 구조로 전환하기 위한 설계/구현 계획서다.

---

## 1. 문제 정의

현재 구조는 사이드바에서 사용자가 직접 `회사 코드`를 입력하고,
그 값이 바로 저장 경로와 실행 기준이 된다.

예:
- 입력: `daon_pharma`
- 저장 경로:
  - `data/company_source/daon_pharma/`
  - `data/ops_standard/daon_pharma/`
  - `data/ops_validation/daon_pharma/`

이 구조는 간단하지만 운영 단계에서는 아래 문제가 생긴다.

- 사람이 코드를 직접 치기 때문에 오타가 난다.
- 회사 이름과 회사 코드가 섞여 입력된다.
- 같은 회사를 다른 표기로 입력할 수 있다.
  - 예: `daon_pharma`, `daon-pharma`, `Daon Pharma`, `다온파마`
- 회사 이름이 바뀌어도 기존 경로는 그대로 유지되어야 하는데, 현재는 그 경계가 약하다.

즉 지금 구조는 개발/검증 단계에는 빠르지만,
운영용 회사 식별 체계로는 불안정하다.

---

## 2. 목표

앞으로는 아래 원칙으로 회사를 다룬다.

1. 사용자는 회사를 `이름`으로 등록하거나 선택한다.
2. 시스템은 내부에서 `고정 company_key`를 발급한다.
3. 저장/실행/경로/DB/run/Agent는 오직 그 `company_key`만 사용한다.
4. 회사 이름은 바뀔 수 있지만 `company_key`는 바뀌지 않는다.

한 줄로 정리하면:

`사람이 쓰는 회사 이름`과 `시스템이 쓰는 company_key`를 분리한다.

---

## 3. 핵심 원칙

### 3-1. 사람용 값과 시스템용 값 분리

- `company_name`
  - 사람용 표시 이름
  - 변경 가능
  - 예: `지원제약`

- `company_key`
  - 시스템 내부 고정 식별자
  - 변경 금지
  - 저장 경로/실행/run/DB 기준

### 3-2. 경로 기준은 항상 company_key

모든 파일 저장 경로는 계속 아래 구조를 따른다.

- `data/company_source/{company_key}/`
- `data/ops_standard/{company_key}/`
- `data/ops_validation/{company_key}/`

회사 이름은 경로에 직접 사용하지 않는다.

### 3-3. 회사 이름 변경과 데이터 보존 분리

- 회사 이름은 운영상 바뀔 수 있다.
- 하지만 이미 생성된 데이터 경로와 run 이력은 유지되어야 한다.
- 따라서 회사 이름 변경은 `company_registry` 메타만 바꾸고,
  기존 `company_key` 기반 저장 구조는 그대로 유지한다.

---

## 4. 권장 company_key 발급 방식

### 권장안

사람이 읽는 이름 기반 키보다,
시스템이 고정 발급하는 내부 키를 권장한다.

예:
- `company_000001`
- `company_000002`

또는
- UUID/short id 기반 내부 키

예:
- `cmp_a8d1b8b8`

### 이름 기반 키를 기본안으로 권장하지 않는 이유

예:
- `jiwon_pharma`

이 방식은 처음에는 보기 쉽지만,
아래 문제가 생긴다.

- 회사 이름 변경 시 키를 바꿀지 말지 애매해진다.
- 비슷한 이름의 회사가 생기면 충돌 위험이 있다.
- 영문/한글 표기 규칙을 계속 맞춰야 한다.

따라서 운영 기준으로는
`사람이 읽기 쉬운 키`보다 `절대 안 바뀌는 키`가 더 중요하다.

---

## 5. 데이터 모델

## 5-1. 회사 등록 테이블

권장 테이블명:
- `company_registry`

권장 컬럼:

- `id`
  - 내부 PK
- `company_key`
  - 고정 시스템 키
- `company_name`
  - 현재 표시 이름
- `company_name_normalized`
  - 검색/중복 확인용 정규화 이름
- `status`
  - `active`, `inactive`
- `created_at`
- `updated_at`

선택 컬럼:

- `company_code_external`
  - 외부 시스템에서 쓰는 회사 코드가 있을 경우 저장
- `aliases_json`
  - 과거 이름, 별칭
- `notes`

---

## 6. 동작 흐름

### 6-1. 회사 등록

1. 사용자가 회사 이름 입력
2. 시스템이 정규화 이름 생성
3. 기존 등록 회사와 중복 확인
4. 중복이 없으면 새 `company_key` 발급
5. `company_registry` 저장

### 6-2. 회사 선택

1. 사용자가 회사 이름 검색 또는 목록 선택
2. 시스템이 해당 회사의 `company_key` 조회
3. 이후 실행/저장은 그 `company_key` 기준으로 진행

### 6-3. 파이프라인 실행

1. 선택된 회사의 `company_key` 확보
2. 실행 컨텍스트 생성
3. 모든 source/standard/validation 경로 계산
4. run 생성 및 저장

즉 실행 단계에서는 더 이상 자유 텍스트 입력을 기준으로 경로를 잡지 않는다.

---

## 7. 현재 코드에 필요한 변경

### 7-1. 공통 조회 레이어 추가

추가 대상 예시:
- `common/company_registry.py`

책임:
- 회사 등록
- 회사 조회
- 이름 -> `company_key`
- `company_key` -> 회사 메타

### 7-2. UI 변경

현재:
- 사이드바에서 `회사 코드`, `회사 이름` 자유 입력

변경 후:
- 등록된 회사 선택 드롭다운
- 필요 시 신규 회사 등록 폼

원칙:
- 실행 전에 반드시 등록된 회사를 선택해야 한다.
- 자유 입력 기반 경로 생성은 점진적으로 제거한다.

### 7-3. 실행 레이어 변경

영향 파일 예시:
- `ui/console_sidebar.py`
- `ui/console_paths.py`
- `ui/console_runner.py`
- `ops_core/workflow/execution_service.py`

핵심 변경:
- 현재 세션에서 직접 입력한 문자열 대신
  등록된 `company_key`를 기준으로 경로 계산

### 7-4. Agent / Builder / Run 조회 변경

영향 범위:
- Agent 탭
- run 조회
- Builder 결과 조회

원칙:
- 회사 이름 기반 fallback를 늘리지 않는다.
- 항상 `company_key`로 바로 찾고,
  화면에는 회사 이름만 표시한다.

---

## 8. 점진 전환 전략

### 1단계

- 기존 자유 입력 구조 유지
- `company_registry` 테이블과 조회 레이어 추가
- 기존 회사(`daon_pharma`, `hangyeol_pharma`)를 registry에 등록

### 2단계

- UI에서 자유 입력 대신 등록 회사 선택 UI 추가
- 내부적으로는 registry의 `company_key` 사용

### 3단계

- Agent / Pipeline / Builder / Run 조회를 registry 기준으로 일원화
- 자유 입력 fallback는 read-only 호환 용도로만 유지

### 4단계

- 안정화 후 자유 입력 기반 실행 제거

---

## 9. 기존 회사 이관 계획

현재 확인된 회사:
- `daon_pharma`
- `hangyeol_pharma`

이관 시 원칙:

- 기존 폴더명은 그대로 사용 가능
- 기존 폴더명을 registry의 `company_key`로 먼저 등록
- 나중에 신규 회사부터는 새 발급 규칙 사용 가능

즉 초기에 무리하게 기존 데이터를 rename하지 않는다.

이유:
- 파이프라인 안정성이 우선이다.
- 먼저 registry를 도입하고,
  rename은 정말 필요할 때만 검토한다.

---

## 10. 완료 기준

아래를 만족하면 회사 등록/고정 key 체계가 완료된 것으로 본다.

- 사용자는 회사를 이름으로 등록/선택할 수 있다.
- 시스템은 고정 `company_key`를 자동 발급/유지한다.
- 저장 경로는 항상 `company_key` 기준이다.
- 회사 이름이 바뀌어도 기존 데이터 경로는 유지된다.
- Agent / Pipeline / Builder / Run 조회가 모두 같은 `company_key`를 기준으로 동작한다.
- 자유 입력 실수(`오타`, `하이픈`, `표기 차이`)가 경로 오류로 바로 이어지지 않는다.

---

## 11. 구현 우선순위

1. `company_registry` 스키마 설계
2. registry 접근 코드 추가
3. 기존 회사 2개 등록
4. UI 회사 선택/등록 화면 추가
5. Pipeline/Agent가 registry 기반 `company_key` 사용
6. 자유 입력 fallback 축소

---

## 12. 한 줄 결론

운영 단계로 가려면 회사 식별은 더 이상 자유 입력 문자열에 맡기면 안 된다.  
`회사 이름은 사람이 쓰고, company_key는 시스템이 고정 발급해 끝까지 유지하는 구조`로 전환해야 한다.
