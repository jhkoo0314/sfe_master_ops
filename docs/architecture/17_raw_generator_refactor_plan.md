# 17. Raw Generator Refactor Plan

## 문서 목적

이 문서는 Sales Data OS의 테스트용 raw 생성 구조를 단순화하기 위한 설계 초안이다.

중요:

- 이 문서는 **테스트용 raw 생성기** 기준 문서다.
- 실제 운영의 공통 입구는 이제 `modules/intake`의 `공통 intake/onboarding engine`이 맡는다.
- 즉 생성기는 테스트 데이터를 만들고, 실제 운영과 테스트의 공통 입구는 별도 intake/onboarding engine이 맡는 방향을 전제로 한다.
- 현재 전략에서는 raw 생성기를 **일단 유지**한다.
- 따라서 이 문서의 항목은 **지금 당장 구현해야 하는 필수 작업이 아니다.**
- 이 문서는 향후 테스트용 생성기가 과도하게 늘어나거나 정리가 필요할 때 참고하는 **후순위 보조 설계 문서**로만 본다.

현재 상태 기준 해석:

- 운영 쪽의 intake/onboarding 공통화는 이미 완료된 상태다.
- 따라서 지금 이 문서가 다루는 실제 정리 대상은 `테스트용 raw generator 공통화`로 좁혀진다.
- 즉 현재 남은 질문은 운영 입구가 아니라, 회사별 raw 생성기를 공통 생성 엔진으로 어떻게 줄일지다.

현재 구조는 회사별 raw 생성기 파일이 늘어나는 방향으로 가고 있다.  
이 방식은 단기적으로는 빠르지만, 회사가 늘수록 유지보수 비용이 커진다.

이번 리팩토링의 목표는 아래 3가지다.

1. 회사별 raw 생성기를 계속 새로 만들지 않도록 공통 생성 엔진으로 정리한다.
2. 회사별 차이와 생성 방식 차이를 코드가 아니라 설정으로 관리한다.
3. 월별 생성 후 병합 같은 시나리오를 별도 회사 스크립트가 아니라 옵션으로 처리한다.

이 문서는 Part2 진행 상태 문서가 아니라 구조 설계 문서다.  
진행 상태 단일 기준은 계속 `docs/architecture/12_part2_status_source_of_truth.md`를 따른다.

현재 적용 해석:

- `17번 문서 미구현`은 현재 상태에서 진행 차질이나 운영 미완성을 뜻하지 않는다.
- 현재 운영 가능성 판단은 `18`, `19`, `20` 문서 기준의 공통 intake/onboarding engine 준비 상태를 우선 본다.
- 현재 기준에서 이 문서는 `운영 필수 문서`가 아니라 `테스트 데이터 생성기 정리 문서`다.
- 2026-03-22 기준으로 1차/2차 정리는 실제로 완료됐다.
- 따라서 이 문서는 이제 “향후 방향 제안”보다는 “현재 raw generator 구조 기록 + 추가 회사 생성 기준” 문서로 읽는 것이 맞다.

---

## 1. 현재 구조 점검

### 1.1 현재 확인된 관련 파일

- `scripts/generate_source_raw.py`
- `scripts/raw_generators/templates/daon_like_helpers.py`
- `scripts/raw_generators/templates/hangyeol_like_helpers.py`
- `common/company_profile.py`

현재 확인된 구조 해석:

- 실제 raw generator 구현 본체는 템플릿 helper로 이동했다.
- `generate_source_raw.py`는 공통 진입점이고, 실제 본체는 `config -> engine -> template -> helper` 구조를 따른다.
- 운영용 공통 입구(`modules/intake`)와 테스트 raw generator는 이제 역할이 더 분리된 상태다.

### 1.2 현재 구조의 동작 방식

현재는 `generate_source_raw.py`가 실제 공통 진입점이고, `company_profile.py`를 거치지 않는다.

즉 구조는 아래와 같다.

`공통 진입점 -> config -> engine -> template -> helper -> writer -> company_source 저장`

### 1.3 현재 구조의 문제

#### 문제 1. 회사별 파일이 계속 늘어난다

지금 구조에서는 새 회사가 들어올 때마다 `generate_xxx_source_raw.py` 같은 파일이 생기기 쉽다.

이 방식은 아래 문제를 만든다.

- 같은 로직 복사 증가
- 버그 수정이 여러 파일로 퍼짐
- 설정 변경이 코드 수정으로 바뀜

#### 문제 2. 회사 차이와 생성 방식 차이가 섞여 있다

예를 들어 `monthly_merge_pharma`는 완전히 다른 회사 생성 엔진이라기보다 아래에 가깝다.

- 다온형 생성 규칙 사용
- 기간 6개월
- 월별 raw 저장
- 마지막에 병합

즉 이 케이스는 “새 회사 엔진”이 아니라 “생성 옵션이 다른 시나리오”다.

#### 문제 3. 설정값이 코드 안에 박혀 있다

현재 생성기들에는 아래 값들이 config 또는 template helper 상수로 들어가 있다.

- 회사 키
- 회사명
- 시작/종료 기간
- 지점 수
- 의원 담당자 수
- 종합병원 담당자 수
- 포트폴리오 경로
- 월별 저장 여부

이 값들은 코드가 아니라 설정으로 관리하는 편이 맞다.

#### 문제 4. 포트폴리오 기준표가 왜 필요한지 설명이 약했다

현재 생성기는 `docs/part1/hangyeol-pharma-portfolio-draft.csv`를 공통 제품 기준표로 사용한다.

이 파일을 보는 이유는 단순히 제품명을 고정하기 위해서만이 아니다.

- CRM에서 어떤 브랜드를 언급할지 맞추기 위해
- Sales / Target에서 같은 브랜드 체계를 쓰기 위해
- Prescription에서 SKU / 제형 / 포장단위를 같은 체계로 맞추기 위해
- 제품별 전략 비중(`strategic_weight`)과 채널 적합성(`care_setting`)을 반영하기 위해

즉 이 CSV는 “제품명 목록”이라기보다 raw generator용 공통 제품 기준표로 보는 것이 맞다.

이 방식은 아래 문제를 만든다.

- 파일명/경로 규칙이 생성기마다 달라질 위험
- 월별 저장 로직이 반복됨
- 병합 summary 형식이 일관되지 않을 수 있음

#### 현재 시점의 냉정한 판단

지금은 운영 입구 공통화가 이미 끝난 상태이므로, raw generator는 아래 정도로만 정리하면 충분하다.

- 공통 generation engine 1개
- config
- template
- writer
- 생성 함수 본체는 helper로 이동

즉 현재는 운영 전체 구조 재설계가 아니라, 테스트 데이터 생성기만 공통 엔진으로 수렴시키는 작업으로 보는 것이 맞다.

---

## 2. 리팩토링 목표 구조

### 2.1 핵심 원칙

앞으로 raw 생성은 아래 원칙을 따른다.

1. 공통 생성 로직은 한 군데에 둔다.
2. 회사별 차이는 설정으로 관리한다.
3. 월별 생성 여부도 설정으로 관리한다.
4. 최종 저장 형식은 공통 writer가 책임진다.
5. 기존 파이프라인과 파일 경로는 최대한 유지한다.

추가 원칙:

6. 운영 공통 입구는 이미 `modules/intake`가 맡고 있으므로, raw generator는 테스트 데이터 생성 책임만 가진다.
7. raw generator 리팩토링이 intake/onboarding 구조를 다시 흔들면 안 된다.

### 2.2 목표 구조

목표 구조는 아래와 같다.

`generate_source_raw.py -> generation config 로드 -> 공통 generation engine 실행 -> 공통 writer 저장`

### 2.3 목표 디렉토리 구조

예상 구조는 아래와 같다.

```text
scripts/
  generate_source_raw.py
  raw_generators/
    engine.py
    configs.py
    writers.py
    templates/
      daon_like.py
      hangyeol_like.py
```

### 2.4 각 파일의 책임

#### `scripts/generate_source_raw.py`

- 공통 진입점
- 현재 활성 회사 키를 읽음
- 회사별 generation config를 로드함
- 공통 엔진을 실행함

현재 상태 기준 메모:

- 장기적으로는 `company_profile.py`의 회사별 generator 모듈 경유를 줄이고, config 기반으로 직접 공통 engine을 부르는 방향이 맞다.

#### `scripts/raw_generators/configs.py`

- 회사별 raw 생성 설정 정의
- 회사별 설정 조회 함수 제공
- “회사 차이”와 “생성 방식 차이”를 모두 설정으로 표현

#### `scripts/raw_generators/engine.py`

- raw 생성 전체 흐름 제어
- 설정값을 받아 공통 생성 흐름 실행
- 템플릿별 함수 호출
- 월별 생성/병합 여부 판단

#### `scripts/raw_generators/writers.py`

- 최종 source 파일 저장
- `monthly_raw/YYYYMM` 저장
- generation summary 저장
- 월별 병합 결과 저장

#### `scripts/raw_generators/templates/daon_like.py`

- 다온형 생성 규칙
- 담당자 생성, 거래처 배정, CRM, Sales, Target, Prescription 생성 규칙 보유

#### `scripts/raw_generators/templates/hangyeol_like.py`

- 한결형 생성 규칙
- 다온형과 다른 분포/배정/원본 형태 차이만 담당

---

## 3. 설정 중심 구조 설계

### 3.1 공통 설정 모델

아래와 같은 설정 모델을 기준으로 한다.

```python
RawGenerationConfig(
    company_key="monthly_merge_pharma",
    company_name="월별검증제약",
    template_type="daon_like",
    start_month="2025-01",
    end_month="2025-06",
    branch_count=10,
    clinic_rep_count=50,
    hospital_rep_count=25,
    portfolio_source="hangyeol_portfolio",
    output_mode="monthly_and_merged",
)
```

### 3.2 설정 필드 정의

#### 회사 식별

- `company_key`
- `company_name`

#### 생성 템플릿 선택

- `template_type`
  - `daon_like`
  - `hangyeol_like`

#### 기간 설정

- `start_month`
- `end_month`

#### 조직 규모 설정

- `branch_count`
- `clinic_rep_count`
- `hospital_rep_count`

#### 포트폴리오 설정

- `portfolio_source`

#### 출력 방식 설정

- `output_mode`
  - `merged_only`
  - `monthly_and_merged`

### 3.3 왜 이 구조가 필요한가

이 구조를 쓰면 아래가 가능해진다.

- 새 회사 추가 시 코드 복사 없이 설정만 추가
- 월별 생성 여부를 새 스크립트 없이 처리
- 테스트 시나리오를 회사와 분리해 관리

예를 들어 `monthly_merge_pharma`는 아래처럼 정의할 수 있다.

- `template_type = daon_like`
- `output_mode = monthly_and_merged`
- `start_month = 2025-01`
- `end_month = 2025-06`

즉 “별도 생성기”가 아니라 “설정 케이스”가 된다.

---

## 4. 실제 리팩토링 작업 순서표

### Phase 1. 설계 고정

#### 목표

공통화 범위와 설정 모델을 먼저 고정한다.

#### 작업

1. 다온/한결/월별검증제약 생성기의 공통점과 차이점을 분리 정리
2. `RawGenerationConfig` 초안 정의
3. `template_type`, `output_mode` 기준 확정

#### 완료 기준

- 공통 엔진에서 받아야 할 입력값 목록 확정
- 월별 생성이 “옵션”이라는 기준 확정
- 현재 상태 기준으로 “운영 입구 공통화는 제외, raw generator 공통화만 대상”이라는 범위 확정

현재 진행 메모 (`2026-03-22`):

- `scripts/raw_generators/configs.py` 추가
- `RawGenerationConfig` dataclass 추가
- 현재 회사 3개(`daon_pharma`, `hangyeol_pharma`, `monthly_merge_pharma`) 설정 등록
- `generate_source_raw.py`는 이제 공통 config를 먼저 읽고, 기존 회사별 generator wrapper를 호출할 준비가 된 상태
- 즉 Phase 1은 “공통 설정 모델 + 공통 진입 준비”까지 완료된 것으로 본다

### Phase 2. 저장 로직 공통화

#### 목표

생성기마다 따로 저장하던 파일 쓰기 로직을 공통 writer로 분리한다.

#### 작업

1. 최종 source raw 저장 함수 분리
2. `monthly_raw/YYYYMM` 저장 함수 분리
3. generation summary 저장 함수 분리

#### 완료 기준

- 어떤 템플릿을 써도 writer는 동일 모듈을 사용

현재 진행 메모 (`2026-03-22`):

- `scripts/raw_generators/writers.py` 추가
- 공통 writer가 아래 책임을 먼저 가져갔다
  - 최종 source raw 저장
  - `monthly_raw/YYYYMM` 저장
  - json summary 저장
  - csv breakdown 저장
- 기존 `daon`, `hangyeol`, `monthly_merge` 생성기는 이제 직접 파일을 쓰지 않고 공통 writer를 호출한다

### Phase 3. 다온형 공통 엔진 추출

#### 목표

다온 생성기를 첫 번째 공통 템플릿으로 만든다.

#### 작업

1. 다온 생성기의 공통 함수 추출
2. 공통 엔진에서 `daon_like` 템플릿 호출
3. 기존 다온 생성기는 thin wrapper로 축소

#### 완료 기준

- `daon_pharma`가 공통 엔진으로도 동일 출력 생성

현재 진행 메모 (`2026-03-22`):

- `scripts/raw_generators/engine.py` 추가
- `scripts/raw_generators/templates/daon_like.py` 추가
- 다온 생성 본체는 `templates/daon_like_helpers.py`로 이동
- 즉 다온 생성기는 공통 템플릿/helper 경로로 정리됐다

### Phase 4. 월별검증제약을 설정형으로 전환

#### 목표

월별검증제약을 독립 생성기에서 설정 케이스로 바꾼다.

#### 작업

1. `monthly_and_merged` 모드 구현
2. 월별 저장 및 병합을 공통 engine/writer로 이동
3. `monthly_merge_pharma`를 config로만 정의

#### 완료 기준

- 별도 월별 회사 생성기 없이 6개월 월별 생성 가능

현재 진행 메모 (`2026-03-22`):

- `monthly_merge_pharma`는 이제 공통 engine이 `output_mode="monthly_and_merged"`를 보고 처리한다
- 월별 생성/병합 본체는 `templates/daon_like.py` 안의 월별 경로로 이동
- 별도 월별 wrapper 없이 설정 옵션으로 해석하는 구조로 정리됐다

### Phase 5. 한결형 템플릿 흡수

#### 목표

한결 생성기를 두 번째 템플릿으로 흡수한다.

#### 작업

1. 한결 전용 차이 규칙 정리
2. `hangyeol_like` 템플릿 파일로 이전
3. 기존 한결 생성기를 thin wrapper로 축소

#### 완료 기준

- `hangyeol_pharma`도 공통 엔진으로 생성 가능

현재 진행 메모 (`2026-03-22`):

- `scripts/raw_generators/templates/hangyeol_like.py` 추가
- 한결 생성 본체는 `templates/hangyeol_like_helpers.py`로 이동
- 즉 한결 생성기도 공통 템플릿/helper 경로로 정리됐다

### Phase 6. profile 연결 단순화

#### 목표

`company_profile.py`가 회사별 파이썬 생성기 파일을 직접 가리키지 않게 만든다.

#### 작업

1. raw generator를 `company_profile.py`와 분리할지 검토
2. 필요 시 config 조회 구조만으로 실행 가능하게 단순화
3. `generate_source_raw.py`가 설정 기반으로 직접 실행하도록 정리

#### 완료 기준

- 회사 등록 시 “모듈 경로”보다 “설정 키” 중심으로 관리 가능

현재 진행 메모 (`2026-03-22`):

- 1차에서는 `generation_profile_key`를 거쳤지만
- 2차에서는 raw generator 실행이 `company_profile.py`와 분리됐다
- 즉 이제 raw generator는 profile 정보 없이도 `config -> engine`만으로 실행된다

2차 정리 메모 (`2026-03-22`):

- raw generator는 운영 핵심이 아니라 실험용이므로, 2차에서는 더 보수적으로 유지하지 않기로 했다.
- `generate_source_raw.py`는 이제 `company_profile.py`를 거치지 않고 바로 generation config를 읽어 공통 engine을 실행한다.
- `company_profile.py`에서는 raw generator 전용 필드를 제거했다.
- 즉 raw generator 실행 경로는 이제 `config -> engine -> template -> writer` 한 줄로 보는 것이 맞다.

### Phase 7. 안정화 및 정리

#### 목표

기존 호환성을 유지한 채 레거시 생성기 파일을 정리한다.

#### 작업

1. 기존 생성기 파일을 thin wrapper 상태로 유지
2. 검증 완료 후 단계적으로 정리
3. README / RUNBOOK / STRUCTURE 문서 업데이트

#### 완료 기준

- 실행 경로 혼동이 줄고 문서 설명도 새 구조와 일치
- legacy generator 파일 정리까지 끝나면 완료

현재 진행 메모 (`2026-03-22`):

- `README.md`, `RUNBOOK.md`, `STRUCTURE.md` 설명을 현재 구조 기준으로 정리
- 현재 공개 설명 기준은 아래로 통일
  - `generate_source_raw.py` = 공통 진입점
  - `configs.py` = 생성 설정
  - `engine.py` = 공통 실행
  - `templates/daon_like.py`, `templates/hangyeol_like.py` = 템플릿
  - `writers.py` = 공통 저장
  - template helper = 실제 함수 본체
- legacy generator 파일 삭제 완료
  - `generate_daon_source_raw.py`
  - `generate_hangyeol_source_raw.py`
  - `generate_monthly_merge_source_raw.py`
- `tera_pharma` 테스트 회사 추가 및 실제 raw 생성 완료
  - 기간 `2025-01 ~ 2025-12`
  - 지점 `6개`
  - 담당자: 의원 `30명`, 종합병원 `30명`
- 즉 Phase 7은 문서 정렬뿐 아니라 실제 legacy generator 제거와 새 테스트 회사 생성 검증까지 마무리된 상태로 본다

---

## 5. 어떤 파일을 어떻게 바꿀지

### 5.1 새로 만들 파일

#### `scripts/raw_generators/configs.py`

역할:

- 회사별 raw 생성 설정 정의
- config 조회 함수 제공

예상 내용:

- `RawGenerationConfig` dataclass
- `get_raw_generation_config(company_key)`
- `DAON_PHARMA_CONFIG`
- `HANGYEOL_PHARMA_CONFIG`
- `MONTHLY_MERGE_PHARMA_CONFIG`

#### `scripts/raw_generators/engine.py`

역할:

- 공통 raw 생성 흐름 실행

예상 내용:

- 설정 로드
- 템플릿 선택
- 월별/일괄 생성 분기
- writer 호출

#### `scripts/raw_generators/writers.py`

역할:

- 공통 저장 전용

예상 내용:

- `write_merged_outputs(...)`
- `write_monthly_outputs(...)`
- `write_generation_summary(...)`

#### `scripts/raw_generators/templates/daon_like.py`

역할:

- 다온형 생성 규칙 보유

예상 내용:

- 포트폴리오 로드
- 거래처 선택
- 담당자 생성
- account master 생성
- assignment 생성
- crm 생성
- sales/target 생성
- fact ship 생성

#### `scripts/raw_generators/templates/hangyeol_like.py`

역할:

- 한결형 생성 규칙 보유

예상 내용:

- 한결 전용 분포/배정/변형 규칙

### 5.2 수정할 파일

#### `scripts/generate_source_raw.py`

현재:

- generation config를 읽어 공통 engine 실행

변경:

- 공통 config 조회
- 공통 engine 직접 실행

#### `common/company_profile.py`

현재:

- 운영용 source target과 adapter 설정만 관리

변경:

- raw generator 전용 연결 정보 제거 완료

주의:

- 운영용 profile 책임과 테스트용 raw generator 책임을 다시 섞지 않는다.

#### `scripts/raw_generators/templates/daon_like_helpers.py`

현재:

- 다온 전체 생성 로직 직접 포함

변경:

- 다온형 실제 생성 함수 보관
- `templates/daon_like.py`가 직접 사용

#### `scripts/raw_generators/templates/hangyeol_like_helpers.py`

현재:

- 한결 전체 생성 로직 직접 포함

변경:

- 한결형 실제 생성 함수 보관
- `templates/hangyeol_like.py`가 직접 사용

#### `monthly_merge_pharma` 설정 케이스

현재:

- 별도 generator 파일이 아니라 `daon_like + monthly_and_merged` 옵션으로 처리

변경:

- 독립 엔진 역할 제거 완료
- config 기반 공통 엔진 경로로 수렴

### 5.3 유지할 파일

#### `scripts/normalize_*`

이 파일들은 raw 생성기가 아니라 Adapter/정규화 단계이므로 이번 리팩토링의 직접 대상이 아니다.

#### `scripts/validate_*`

이 파일들은 Validation Layer(OPS) 검증 단계이므로 이번 리팩토링의 직접 대상이 아니다.

#### `ops_core/workflow/monthly_source_merge.py`

이 파일은 운영콘솔에서 월별 raw를 자동 병합하는 실행 경로다.  
raw 생성기 리팩토링과는 연결되지만, 바로 제거 대상은 아니다.

---

## 6. 실행 검증 계획

리팩토링은 코드 정리보다 검증이 더 중요하다.  
아래 순서로 검증한다.

### 6.1 1차 검증

대상:

- `daon_pharma`
- `monthly_merge_pharma`

검증 항목:

1. raw 생성 성공 여부
2. 월별 파일 저장 여부
3. 병합 파일 생성 여부
4. row count 일치 여부
5. `crm_to_sandbox` 실행 결과
6. `integrated_full` 실행 결과

### 6.2 2차 검증

대상:

- `hangyeol_pharma`

검증 항목:

1. 기존 생성 결과와 구조 차이 확인
2. Validation Layer(OPS) 결과 비교
3. Builder 결과 생성 여부

### 6.3 성공 기준

아래 조건을 만족하면 성공으로 본다.

- 기존 회사 raw 생성이 깨지지 않는다.
- 월별 생성 + 병합 구조가 유지된다.
- 실행 모드별 파이프라인 결과가 기존과 동등하거나 더 명확해진다.
- 새 회사 추가 시 새 파이썬 파일 없이 설정 추가만으로 처리 가능하다.

---

## 7. 최종 판단

현재 raw 생성 구조는 동작은 하지만 확장성이 약하다.  
특히 `monthly_merge_pharma` 사례는 “회사별 생성기 추가”보다 “공통 엔진 + 설정 기반 구조”로 가야 한다는 점을 분명하게 보여준다.

현재 상태 기준 최종 판단은 더 단순하다.

- 운영 공통화는 이미 intake/onboarding이 맡고 있다.
- 따라서 지금 정리 대상은 raw generator뿐이다.
- 즉 “raw 생성기만 공통 생성기로 남기면 되는가?”라는 질문에는 그렇다고 답하는 것이 맞다.
- 다만 실제 구현 순서는 여전히 `공통 engine -> wrapper 유지 -> 마지막에 profile 단순화`가 안전하다.

따라서 다음 원칙으로 정리하는 것이 맞다.

1. raw 생성기는 회사별 파일 추가 방식에서 벗어난다.
2. 공통 생성 엔진을 중심으로 재구성한다.
3. 회사별 차이는 설정으로 분리한다.
4. 월별 생성/병합은 생성기 종류가 아니라 옵션으로 처리한다.
5. 기존 실행 경로는 정리 완료됐고, 새 테스트 회사는 config 추가 중심으로 확장한다.

이 문서를 기준으로 실제 구현은 아래 순서로 들어간다.

1. config 모델 추가
2. writer 분리
3. daon_like 공통 엔진 추출
4. monthly_merge 설정형 전환
5. hangyeol_like 흡수
6. profile 연결 단순화
7. 문서/실행 경로 정리
