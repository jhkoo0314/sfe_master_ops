# 22. OPS Core Location Migration Review

## 문서 목적

이 문서는 [`21_ops_core_refactor_plan.md`](/C:/sfe_master_ops/docs/architecture/21_ops_core_refactor_plan.md)의  
`Step 7 마지막 위치 이동 검토` 결과를 정리한 문서다.

핵심 질문은 하나다.

- 지금 `ops_core/`를 실제로 `modules/validation/`으로 옮겨도 되는가?

결론부터 말하면:

**개념적으로는 거의 준비됐지만, 운영 경로까지 지금 즉시 rename/move 하는 것은 아직 이르다.**

즉 현재 판단은 아래와 같다.

- 개념 판단: `이동 방향 맞음`
- 운영 판단: `지금 즉시 물리 이동은 보류`
- 다음 안전한 단계: `modules/validation bridge 추가 후 점진 전환`

---

## 1. 현재 상태 요약

Step 1~6을 거치면서 아래 책임은 이미 `ops_core` 밖으로 빠졌다.

- monthly merge 본체 -> `modules/intake/merge.py`
- staged source root 준비 -> `modules/intake/runtime.py`
- script import/cache reset -> `common/runtime_helpers/import_cache.py`

즉 `ops_core` 안에 남아 있는 것은 대부분 아래 성격이다.

- Validation API
- Result Asset 평가 오케스트레이션
- 실행 모드 정의
- 실제 실행 조정
- FastAPI 진입점

쉽게 말하면:

- 예전보다 훨씬 얇아졌다.
- 지금은 `Validation / Orchestration Layer 구현 패키지`라고 설명해도 어색하지 않다.

---

## 2. 현재 남아 있는 실제 파일

현재 `ops_core`의 실제 Python 파일은 아래 수준으로 줄어 있다.

```text
ops_core/
  __init__.py
  main.py
  api/
    crm_router.py
    prescription_router.py
    sandbox_router.py
    territory_router.py
    pipeline_router.py
  workflow/
    orchestrator.py
    schemas.py
    execution_models.py
    execution_registry.py
    execution_runtime.py
    execution_service.py
    monthly_source_merge.py   # thin wrapper
```

평가:

- `api/*`는 남아도 된다.
- `workflow/orchestrator.py`, `schemas.py`, `execution_models.py`도 남아도 된다.
- `monthly_source_merge.py`는 이미 wrapper라 실제 본체로 보지 않아도 된다.

즉 폴더 안의 내용은 이제 대부분 `validation/orchestration`이라고 말할 수 있다.

---

## 3. 지금 바로 못 옮기는 이유

문제는 `폴더 내부 책임`보다 `바깥 연결 수`다.

### 3.1 외부 Python 의존 개수

현재 `ops_core`를 직접 참조하는 Python 파일은  
`ops_core` 바깥에 **20개** 있다.

대표 범위:

- `scripts/*`
- `ui/console/*`
- `tests/*`
- `modules/intake/*`
- `common/runtime_helpers/*`

즉 폴더를 지금 바로 옮기면,
실제 운영 코드와 테스트 코드가 한 번에 많이 흔들린다.

### 3.2 문서/운영 명령 의존 개수

`ops_core` 경로를 직접 언급하는 Markdown 문서도 **22개** 있다.

또 실제 실행 명령도 아직 이렇게 되어 있다.

```bash
uv run uvicorn ops_core.main:app --reload --host 0.0.0.0 --port 8000
```

즉 지금 바로 물리 이동하면 같이 손봐야 하는 범위가 넓다.

### 3.3 FastAPI 진입점 결합

현재 API 서버 진입점은 [`ops_core/main.py`](/C:/sfe_master_ops/ops_core/main.py)다.

이건 단순 import 하나가 아니라:

- 실행 명령
- README
- RUNBOOK
- 문서 예시

까지 같이 묶여 있다.

그래서 “폴더만 옮기고 끝”이 아니다.

---

## 4. 냉정한 판단

### 4.1 개념 기준

개념 기준으로는:

- `ops_core`의 최종 목적지가 `modules/validation`이라는 판단이 맞다.

이유:

- 이름이 역할을 더 정확히 설명한다.
- `OPS`를 시스템 전체처럼 오해할 가능성이 줄어든다.
- `modules/intake`, `modules/kpi`, `modules/builder`와 나란히 놓였을 때 구조 설명이 더 자연스럽다.

### 4.2 운영 기준

운영 기준으로는:

- **지금 즉시 hard rename은 비추천**이다.

이유:

- 외부 의존이 아직 많다.
- 실행 명령과 문서 경로가 아직 `ops_core` 기준이다.
- 얻는 이득보다 깨질 수 있는 범위가 더 크다.

---

## 5. Step 7 최종 결론

Step 7의 최종 결론은 아래다.

### 결론

**현재 상태는 “이동 검토 완료” 단계이며, “즉시 물리 이동 승인” 단계는 아니다.**

즉:

- `ops_core -> modules/validation` 방향은 확정해도 된다.
- 하지만 실제 rename/move는 다음 라운드에서 `bridge 방식`으로 하는 것이 맞다.

---

## 6. 다음 안전한 실행안

지금 바로 rename 대신, 다음 순서가 가장 안전하다.

### Phase A. bridge 패키지 추가

새 패키지를 먼저 만든다.

```text
modules/
  validation/
```

여기에는 처음부터 전부 옮기지 말고,
우선 아래처럼 bridge를 둔다.

- `modules/validation/__init__.py`
- `modules/validation/api/`
- `modules/validation/workflow/`

초기에는 `ops_core`를 그대로 re-export 해도 된다.

### Phase B. 새 import를 점진 전환

바깥 코드에서 새로 손대는 파일부터:

- `ops_core...`
대신
- `modules.validation...`

를 쓰게 바꾼다.

이 단계에서는 기존 `ops_core`도 유지한다.

### Phase C. 실행 진입점 이중 지원

운영 명령도 바로 바꾸지 말고 잠시 둘 다 허용한다.

예:

- `uvicorn ops_core.main:app`
- `uvicorn modules.validation.main:app`

둘 다 잠시 동작하게 만든다.

### Phase D. 마지막 정리

실제 참조가 충분히 줄어든 뒤에만:

- 문서 기본 진입점을 `modules.validation.main:app`으로 바꾸고
- `ops_core`는 thin compatibility package로 남길지
- 완전히 제거할지

판단한다.

---

## 7. 추천 판단

냉정하게 추천하면,
다음 실제 작업은 아래가 맞다.

1. 지금은 `Step 7 검토 완료`로 종료한다.
2. 다음 작업으로 `modules/validation bridge 패키지`를 만든다.
3. 그 다음에만 import 전환을 시작한다.

한 줄 요약:

**지금 `ops_core`는 개념상 `modules/validation`으로 가도 맞지만, 운영 안정성을 생각하면 이번 턴에서 바로 옮기지 말고 bridge를 먼저 만드는 것이 최선이다.**
