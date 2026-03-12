# Next Session Engineering Roadmap

작성일: 2026-03-11

## 0. 이 문서의 목적

이 문서는 새 세션에서 바로 이어서 작업할 수 있게

- 지금까지 무엇이 끝났는지
- 왜 다음 단계가 필요한지
- 무엇을 어떤 순서로 구현해야 하는지

를 한 번에 정리한 handoff 문서다.

이 문서는 특히 `다음 리팩터링 우선순위`를 고정하는 데 목적이 있다.

---

## 1. 현재까지 끝난 상태

현재 프로젝트는 1차 목표였던 `5개 모듈 실행 안정화`는 달성한 상태로 본다.

이미 끝난 큰 정리는 아래와 같다.

- CRM / Prescription / Sandbox / Territory / Builder 실행 가능
- OPS 콘솔에서 실제 파이프라인 실행 가능
- `CRM -> Territory` 실행모드 연결 완료
- Territory는 `담당자 미선택 기본값 + 분리 asset 로딩` 구조로 최적화 완료
- 결과 HTML 5종 생성 가능
- 스크립트 진입점은 회사명 없는 공통 이름으로 정리 완료
- `company_profile.py` 기준으로 회사별 raw 경로와 adapter 설정 관리
- `data/company_source/{company_key}` 안 원천 파일 이름도 공통 이름으로 정리 완료
- `scripts/` 루트에는 공통 진입점만 남기고, 회사별 raw 생성 구현은 `scripts/raw_generators/` 아래로 이동 완료
- 예전 `normalize_hangyeol_*`, `validate_hangyeol_*`, `render_hangyeol_*` wrapper 삭제 완료

즉 지금 상태는

`기능이 없는 상태`가 아니라  
`기능은 돌아가지만, 다음 유지보수 단계로 넘어가기 전에 엔진 구조를 더 굳혀야 하는 상태`

로 이해하면 된다.

---

## 2. 왜 다음 단계가 필요한가

지금은 잘 동작한다.

하지만 아래 5가지 구조 리스크가 남아 있다.

1. 실행 순서를 정하는 로직이 아직 여러 곳에 나뉘어 있다.  
   콘솔, 수동 실행 스크립트, 테스트가 완전히 같은 엔진을 보지 않는다.

2. 모듈 입출력에 버전이 없다.  
   지금은 맞지만, payload가 더 커지고 바뀌기 시작하면 `이 파일이 어떤 규격인지` 추적이 어려워진다.

3. 성능 회귀를 자동으로 막는 장치가 약하다.  
   Territory에서 실제로 한 번 겪었듯이, 파일 크기와 로딩 시간이 갑자기 커져도 늦게 발견될 수 있다.

4. `ui/console_shared.py`에 책임이 많이 모여 있다.  
   지금은 버티지만, 더 커지면 수정 한 번에 영향 범위를 읽기가 어려워진다.

5. CRM / Prescription은 아직 Territory만큼 `필요할 때만 읽는 구조`로 정리되지 않았다.  
   지금은 돌아가도, 데이터가 더 커지면 다시 같은 문제가 생길 가능성이 높다.

그래서 다음 단계는 `새 기능 추가`보다

`같은 기능을 더 덜 흔들리는 구조로 굳히는 작업`

이 우선이다.

---

## 3. 다음 우선순위

이 문서는 아래 순서를 다음 세션의 공식 우선순위로 본다.

### Priority 1. 실행 오케스트레이션을 스크립트 밖 공용 서비스로 올리기

쉬운 뜻:
- 지금은 `무슨 순서로 어떤 모듈을 실행할지`를 여러 파일이 조금씩 알고 있다.
- 이걸 한 군데 공용 실행 엔진으로 올려야 한다.

이 작업을 먼저 하는 이유:
- 콘솔, 수동 실행, 테스트가 같은 엔진을 보게 해야 한다.
- 그래야 실행 흐름 수정이 한 군데에서 끝난다.
- 이후 `console_shared.py` 분리도 더 쉬워진다.

권장 구현 방향:
- 새 공용 서비스 후보:
  - `ops_core/workflow/execution_service.py`
  - `ops_core/workflow/execution_registry.py`
  - `ops_core/workflow/execution_models.py`
- 여기서 맡을 역할:
  - 실행모드 정의
  - 단계 순서 정의
  - 단계 실행
  - 결과 summary 읽기
  - 전체 run result 조립

현재 옮겨야 할 로직 후보:
- [console_shared.py](/C:/sfe_master_ops/ui/console_shared.py)
  - `get_mode_pipeline_steps()`
  - `run_actual_pipeline()`
  - `_build_step_result()`
  - `_get_summary_path()`
- [validate_full_pipeline.py](/C:/sfe_master_ops/scripts/validate_full_pipeline.py)

완료 기준:
- 콘솔이 새 공용 서비스만 호출한다.
- 수동 실행 스크립트도 같은 서비스를 호출한다.
- 테스트도 같은 서비스 기준으로 검증한다.

---

### Priority 2. 모듈별 입출력 규격에 버전 붙이기

쉬운 뜻:
- `이 JSON이 어떤 형식 버전인지` 파일 안에 직접 적어두자는 뜻이다.

이 작업을 지금 해야 하는 이유:
- Territory처럼 payload가 커지면 구조가 자주 바뀐다.
- 버전이 없으면 예전 HTML과 새 payload가 안 맞을 때 원인 추적이 어려워진다.

권장 적용 대상:
- `crm_result_asset.json`
- `prescription_result_asset.json`
- `sandbox_result_asset.json`
- `territory_result_asset.json`
- `crm_builder_payload.json`
- `prescription_builder_payload.json`
- `territory_builder_payload.json`
- `*_input_standard.json`
- `*_payload_standard.json`

권장 필드 이름:
- `schema_version`
- `payload_version`
- `builder_contract_version`

권장 시작 방식:
- 먼저 모든 JSON 루트에 버전 문자열 추가
- 예: `v1`, `v1.1`, `territory_chunked_v1`
- 그 다음 Builder와 템플릿이 버전 체크를 읽게 확장

완료 기준:
- 핵심 JSON 산출물 루트에 버전 필드가 있다.
- Builder는 자기 입력 버전을 기록한다.
- 문서에 현재 버전 규칙이 정리된다.

---

### Priority 3. 파일 크기 / 로딩 시간 회귀 테스트 넣기

쉬운 뜻:
- `파일이 너무 커지거나 느려졌는지`를 테스트가 자동으로 잡게 하자는 뜻이다.

이 작업이 필요한 이유:
- Territory에서 실제로 HTML과 payload가 너무 커져서 로딩이 느려진 적이 있다.
- 이런 문제는 기능 테스트만으로는 잘 안 잡힌다.

권장 측정 항목:
- Builder HTML 파일 크기
- payload JSON 파일 크기
- chunk asset 총 개수
- chunk asset 총 크기
- 특정 스크립트 실행 시간
- 첫 화면 로딩용 seed payload 크기

우선 적용 모듈:
1. Territory
2. CRM
3. Prescription

권장 테스트 예시:
- `territory_map_preview.html` 크기 상한
- `territory_builder_payload.json` 크기 상한
- `crm_analysis_preview.html` 크기 추적
- `prescription_flow_preview.html` 크기 추적

완료 기준:
- 최소 Territory는 크기/성능 회귀 테스트가 있다.
- CRM / Prescription도 같은 방식으로 확장할 준비가 된다.

---

### Priority 4. `console_shared.py` 분리

쉬운 뜻:
- 지금 `console_shared.py`는 한 파일 안에 너무 많은 역할이 들어 있다.
- 이걸 역할별로 나누자는 뜻이다.

이 작업을 Priority 1 뒤에 두는 이유:
- 실행 오케스트레이션을 먼저 밖으로 빼야
- 남는 역할을 더 깔끔하게 나눌 수 있다.

권장 분리 방향:
- `ui/console_state.py`
  - session state 초기화
- `ui/console_paths.py`
  - 경로, source target, artifact path
- `ui/console_runner.py`
  - 실제 실행 호출, run history 저장
- `ui/console_artifacts.py`
  - 산출물 탐색, 미리보기, 다운로드
- `ui/console_display.py`
  - badge, hero, 공통 표시 컴포넌트

주의:
- 먼저 로직을 바깥 서비스로 빼고
- 그 다음 UI 전용 역할만 나누는 순서가 맞다.

완료 기준:
- `console_shared.py`는 최소한 공통 표시 유틸 수준으로 줄어든다.
- 실행, 경로, 상태, 산출물 로직이 파일별로 분리된다.

---

### Priority 5. CRM / Prescription도 Territory처럼 필요할 때만 읽는 구조 검토

쉬운 뜻:
- 지금 Territory는 필요한 담당자/월 데이터만 나중에 읽는다.
- CRM / Prescription도 같은 생각으로 `처음부터 모든 상세 데이터를 HTML에 싣지 않게` 하자는 뜻이다.

이 작업이 마지막인 이유:
- 먼저 실행 엔진과 버전, 성능 측정 기준이 안정돼야
- 그 다음 payload 구조를 더 과감하게 바꿔도 안전하다.

검토 방향:

CRM:
- 월별 / 담당자별 drill-down 상세를 chunk asset으로 분리
- 첫 화면에는 overview + KPI + top summary만 싣기
- 세부 activity table은 선택 시 로드

Prescription:
- claim validation 전체 표를 외부 asset으로 분리
- hospital trace / rep KPI / gap table도 선택 시 로드
- HTML 미리보기는 summary 중심으로 유지

주의:
- 이 단계는 `무조건 Territory 복제`가 아니라
- 각 모듈에 맞는 최소 로딩 구조를 다시 설계하는 작업이다.

완료 기준:
- CRM / Prescription 중 최소 1개는 chunk 또는 lazy loading 시범 적용
- 성능 테스트에 바로 연결 가능

---

## 4. 추천 실행 순서

새 세션에서는 아래 순서로 시작하는 것을 권장한다.

1. Priority 1 착수
   - 공용 실행 서비스 뼈대 만들기
   - 콘솔 실행 로직 이관
   - `validate_full_pipeline.py` 이관

2. Priority 2 착수
   - Result Asset / Builder payload 루트에 버전 필드 추가
   - Builder가 버전 기록하게 변경

3. Priority 3 최소선 적용
   - Territory 크기/성능 회귀 테스트 추가

4. Priority 4 착수
   - `console_shared.py` 분리

5. Priority 5 설계
   - CRM / Prescription lazy loading 초안 작성

즉 다음 세션의 첫 실작업은

`새 기능 추가`가 아니라  
`실행 공용 엔진 만들기`

부터 시작하는 것이 맞다.

---

## 5. 다음 세션에서 먼저 열 파일

새 세션에서 바로 보기 좋은 파일 순서는 아래다.

1. [console_shared.py](/C:/sfe_master_ops/ui/console_shared.py)
2. [validate_full_pipeline.py](/C:/sfe_master_ops/scripts/validate_full_pipeline.py)
3. [generate_source_raw.py](/C:/sfe_master_ops/scripts/generate_source_raw.py)
4. [company_profile.py](/C:/sfe_master_ops/common/company_profile.py)
5. [territory builder payload](/C:/sfe_master_ops/modules/territory/builder_payload.py)
6. [Template Payload Spec](/C:/sfe_master_ops/docs/09_Template_Payload_Spec.md)

이 순서로 보면

- 현재 실행 흐름
- 공통 진입점
- 회사별 설정
- payload 구조

를 한 번에 다시 잡을 수 있다.

---

## 6. 주의 메모

### 6.1 지금 바로 하지 말 것

- CRM / Prescription payload를 먼저 크게 뜯지 않는다.
- 콘솔 UI 파일만 먼저 쪼개지 않는다.
- 성능 테스트 없이 큰 payload 구조 변경부터 하지 않는다.

이유:
- 순서가 뒤집히면 다시 중복 로직이 생길 가능성이 높다.

### 6.2 현재 환경 메모

- `pytest`는 테스트 본문이 통과해도 임시 폴더 정리 권한 문제로 마지막 종료 단계에서 실패할 수 있다.
- 그래서 다음 세션에서도
  - 단위 테스트
  - 실제 다온파마 실행
  - 산출물 크기/경로 직접 확인

을 같이 보는 방식이 안전하다.

---

## 7. 한 줄 결론

다음 단계의 핵심은

`기능 추가`보다 `실행 엔진 통합 -> 버전 규격화 -> 성능 회귀 방지 -> 콘솔 분리 -> CRM/Prescription 경량화`

순서로 구조를 더 단단하게 만드는 것이다.
