# 17. Raw Generator Refactor Plan

## 문서 목적

이 문서는 Sales Data OS의 테스트용 raw 생성 구조를 단순화하기 위한 설계 초안이다.

현재 구조는 회사별 raw 생성기 파일이 늘어나는 방향으로 가고 있다.  
이 방식은 단기적으로는 빠르지만, 회사가 늘수록 유지보수 비용이 커진다.

이번 리팩토링의 목표는 아래 3가지다.

1. 회사별 raw 생성기를 계속 새로 만들지 않도록 공통 생성 엔진으로 정리한다.
2. 회사별 차이와 생성 방식 차이를 코드가 아니라 설정으로 관리한다.
3. 월별 생성 후 병합 같은 시나리오를 별도 회사 스크립트가 아니라 옵션으로 처리한다.

이 문서는 Part2 진행 상태 문서가 아니라 구조 설계 문서다.  
진행 상태 단일 기준은 계속 `docs/architecture/12_part2_status_source_of_truth.md`를 따른다.

---

## 1. 현재 구조 점검

### 1.1 현재 확인된 관련 파일

- `scripts/generate_source_raw.py`
- `scripts/raw_generators/generate_daon_source_raw.py`
- `scripts/raw_generators/generate_hangyeol_source_raw.py`
- `scripts/raw_generators/generate_monthly_merge_source_raw.py`
- `common/company_profile.py`

### 1.2 현재 구조의 동작 방식

현재는 `generate_source_raw.py`가 공통 진입점처럼 보이지만, 실제로는 `company_profile.py`에 등록된 회사별 생성 모듈을 다시 호출한다.

즉 구조는 아래와 같다.

`공통 진입점 -> 회사별 생성기 파일 -> 회사별 raw 저장`

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

현재 생성기들에는 아래 값들이 코드 상수로 들어가 있다.

- 회사 키
- 회사명
- 시작/종료 기간
- 지점 수
- 의원 담당자 수
- 종합병원 담당자 수
- 포트폴리오 경로
- 월별 저장 여부

이 값들은 코드가 아니라 설정으로 관리하는 편이 맞다.

#### 문제 4. 저장 방식도 생성기 안에 섞여 있다

현재 생성기마다 직접 파일 저장과 summary 저장을 처리하고 있다.

이 방식은 아래 문제를 만든다.

- 파일명/경로 규칙이 생성기마다 달라질 위험
- 월별 저장 로직이 반복됨
- 병합 summary 형식이 일관되지 않을 수 있음

---

## 2. 리팩토링 목표 구조

### 2.1 핵심 원칙

앞으로 raw 생성은 아래 원칙을 따른다.

1. 공통 생성 로직은 한 군데에 둔다.
2. 회사별 차이는 설정으로 관리한다.
3. 월별 생성 여부도 설정으로 관리한다.
4. 최종 저장 형식은 공통 writer가 책임진다.
5. 기존 파이프라인과 파일 경로는 최대한 유지한다.

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

### Phase 2. 저장 로직 공통화

#### 목표

생성기마다 따로 저장하던 파일 쓰기 로직을 공통 writer로 분리한다.

#### 작업

1. 최종 source raw 저장 함수 분리
2. `monthly_raw/YYYYMM` 저장 함수 분리
3. generation summary 저장 함수 분리

#### 완료 기준

- 어떤 템플릿을 써도 writer는 동일 모듈을 사용

### Phase 3. 다온형 공통 엔진 추출

#### 목표

다온 생성기를 첫 번째 공통 템플릿으로 만든다.

#### 작업

1. 다온 생성기의 공통 함수 추출
2. 공통 엔진에서 `daon_like` 템플릿 호출
3. 기존 다온 생성기는 thin wrapper로 축소

#### 완료 기준

- `daon_pharma`가 공통 엔진으로도 동일 출력 생성

### Phase 4. 월별검증제약을 설정형으로 전환

#### 목표

`generate_monthly_merge_source_raw.py`를 독립 생성기에서 설정 케이스로 바꾼다.

#### 작업

1. `monthly_and_merged` 모드 구현
2. 월별 저장 및 병합을 공통 engine/writer로 이동
3. `monthly_merge_pharma`를 config로만 정의

#### 완료 기준

- 별도 월별 회사 생성기 없이 6개월 월별 생성 가능

### Phase 5. 한결형 템플릿 흡수

#### 목표

한결 생성기를 두 번째 템플릿으로 흡수한다.

#### 작업

1. 한결 전용 차이 규칙 정리
2. `hangyeol_like` 템플릿 파일로 이전
3. 기존 한결 생성기를 thin wrapper로 축소

#### 완료 기준

- `hangyeol_pharma`도 공통 엔진으로 생성 가능

### Phase 6. profile 연결 단순화

#### 목표

`company_profile.py`가 회사별 파이썬 생성기 파일을 직접 가리키지 않게 만든다.

#### 작업

1. `raw_generator_module` 유지 여부 검토
2. 필요 시 `generation_profile_key` 또는 config 조회 구조 도입
3. `generate_source_raw.py`가 설정 기반으로 직접 실행하도록 단순화

#### 완료 기준

- 회사 등록 시 “모듈 경로”보다 “설정 키” 중심으로 관리 가능

### Phase 7. 안정화 및 정리

#### 목표

기존 호환성을 유지한 채 레거시 생성기 파일을 정리한다.

#### 작업

1. 기존 생성기 파일을 thin wrapper 상태로 유지
2. 검증 완료 후 단계적으로 정리
3. README / RUNBOOK / STRUCTURE 문서 업데이트

#### 완료 기준

- 실행 경로 혼동이 줄고 문서 설명도 새 구조와 일치

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

- 회사 profile에서 `raw_generator_module`을 읽어 import 후 실행

변경:

- 공통 config 조회
- 공통 engine 직접 실행

#### `common/company_profile.py`

현재:

- 회사별 `raw_generator_module` 연결

변경:

- 1차 단계에서는 그대로 둘 수 있음
- 2차 단계에서 `generation_profile_key` 같은 더 단순한 구조 검토

주의:

- 기존 실행 경로 안정성을 위해 한 번에 크게 바꾸지 않는다.

#### `scripts/raw_generators/generate_daon_source_raw.py`

현재:

- 다온 전체 생성 로직 직접 포함

변경:

- 공통 엔진 호출용 thin wrapper로 축소
- 또는 템플릿 함수 보관용으로 쪼개기

#### `scripts/raw_generators/generate_hangyeol_source_raw.py`

현재:

- 한결 전체 생성 로직 직접 포함

변경:

- 공통 엔진 호출용 thin wrapper로 축소
- 한결 고유 로직은 `templates/hangyeol_like.py`로 이동

#### `scripts/raw_generators/generate_monthly_merge_source_raw.py`

현재:

- 다온 생성기를 가져와서 월별 생성/병합 처리

변경:

- 독립 엔진 역할 제거
- config 기반 공통 엔진 호출용 thin wrapper 또는 제거 대상

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

따라서 다음 원칙으로 정리하는 것이 맞다.

1. raw 생성기는 회사별 파일 추가 방식에서 벗어난다.
2. 공통 생성 엔진을 중심으로 재구성한다.
3. 회사별 차이는 설정으로 분리한다.
4. 월별 생성/병합은 생성기 종류가 아니라 옵션으로 처리한다.
5. 기존 실행 경로는 thin wrapper로 잠시 유지하며 안전하게 전환한다.

이 문서를 기준으로 실제 구현은 아래 순서로 들어간다.

1. config 모델 추가
2. writer 분리
3. daon_like 공통 엔진 추출
4. monthly_merge 설정형 전환
5. hangyeol_like 흡수
6. profile 연결 단순화
7. 문서/실행 경로 정리
