# Part 2 모듈 스튜디오 기획안

상태: `legacy`
현재 기준 문서: `docs/architecture/12_part2_status_source_of_truth.md`

작성일: 2026-03-12

## 0. 문서 목적

이 문서는 Part 2에서 검토하는 `모듈 스튜디오` 개념을 다시 정리한 기획안이다.

핵심 질문은 하나다.

`Sandbox, TO, PDF를 하나의 OPS 생태계 안에 두면서도, 공식 지표를 흔들지 않고 실험과 검토를 어떻게 할 것인가`

이 문서는 그 해답으로 `3층 구조`를 제안한다.

중요:

- 이 문서에서 말하는 `모듈 스튜디오`는 `Sandbox / TO / PDF`를 뜻한다.
- `Builder`는 모듈이 아니다.
- `Builder`는 외부 템플릿을 주입해 HTML을 만드는 마지막 표현 단계다.
- 현재 Builder는 `보여줄 미리보기`가 먼저 정해지고, 그 템플릿 계약에 맞춰 데이터가 생산되는 구조다.
- 따라서 `HTML Studio`는 이 문서의 핵심 범위에서 제외한다.

---

## 1. 한 줄 결론

공식 파이프라인은 그대로 유지하고,
그 앞단에 `모듈별 Studio`를 두어 `승인안`을 만든 뒤,
승인된 안으로만 공식 실행을 다시 돌린다.

쉽게 말하면:

- Studio = 실험실
- Official Module = 공식 계산기
- OPS = 관제실
- Builder = 템플릿 주도형 주입기

---

## 2. 왜 모듈 스튜디오가 필요한가

현재 OPS 구조는 안정적이지만,
모든 모듈이 같은 방식으로 끝나는 것은 아니다.

특히 아래 모듈은 `한 번 실행해서 끝`보다 `여러 번 비교/검토`가 더 중요하다.

- `Sandbox`
  - 조인 조건, 지표 조합, 시나리오 비교
- `TO`
  - 권역안, 담당자 배치안, 예외 케이스 검토
- `PDF`
  - 쉐어 룰, 전분기 연장, 예외 처리 검토

이런 성격의 일을 공식 OPS 흐름 안에서 바로 해버리면 문제가 생긴다.

1. 실험 중인 값이 공식 결과처럼 보일 수 있다.
2. 아직 확정되지 않은 설정이 OPS 평가까지 전파될 수 있다.
3. 운영자는 무엇이 실험 결과인지 공식 결과인지 헷갈릴 수 있다.

그래서 `실험 공간`과 `공식 반영 공간`을 나누는 구조가 필요하다.

---

## 3. 3층 구조

```text
1층: Studio Layer
원천데이터/참조데이터 -> 모듈별 Studio -> 승인안 생성

2층: Official Execution Layer
원천데이터 -> Adapter -> Module -> Result Asset

3층: OPS Delivery Layer
Result Asset -> OPS -> Template Contract -> Builder(Template Injection) -> 최종 HTML/보고서
```

### 3.1 1층 Studio Layer

이 층은 `실험실`이다.

여기서 하는 일:

- 여러 시나리오 실행
- 비교 결과 확인
- 예외안 검토
- 승인 후보안 선택

여기서 만들 결과:

- 공식 Result Asset이 아니라 `승인안 패키지`

즉 Studio 결과는 아직 `공식 숫자`가 아니다.

### 3.2 2층 Official Execution Layer

이 층은 `공식 계산층`이다.

여기서 하는 일:

- 승인된 설정안/룰안/시나리오안을 입력으로 사용
- 공용 파이프라인으로 다시 계산
- 공식 Result Asset 생성

중요:

- 공식 결과는 반드시 여기서 다시 만든다.
- Studio에서 본 결과를 그대로 공식 결과로 간주하지 않는다.

### 3.3 3층 OPS Delivery Layer

이 층은 `관제 + 전달 + 표현` 층이다.

여기서 하는 일:

- Result Asset 검증
- 품질 상태 확인
- 다음 단계 연결 판단
- Builder가 외부 템플릿에 데이터를 주입해 HTML 생성

중요:

- OPS는 Studio 실험을 직접 하지 않는다.
- Builder는 승인된 Result Asset만 읽는다.
- Builder는 계산 모듈이 아니므로 자기 Result Asset을 만들지 않는다.
- Part 1에서도 `Builder 전용 Result Asset`은 없었고, Part 2에서도 같은 원칙을 유지한다.
- 현재 Builder 구간은 `데이터가 먼저이고 템플릿이 나중`이 아니라, `미리보기 목표와 템플릿이 먼저`인 구조다.

---

## 4. 전체 흐름

핵심 공식 흐름은 계속 유지한다.

```text
원천데이터 -> Adapter -> Module -> Result Asset -> OPS -> Builder
```

여기서 Builder는 `외부 템플릿 주입 단계`로 이해한다.
더 정확히는 아래처럼 본다.

```text
원천데이터 -> Adapter -> Module -> Result Asset -> OPS -> Template Contract -> Template Injection -> HTML
```

Studio를 붙이면 앞단에 아래 흐름이 하나 더 생긴다.

```text
원천데이터/참조데이터 -> Module Studio -> 승인안 확정
```

그래서 실제 전체 흐름은 이렇게 이해하면 된다.

```text
원천데이터/참조데이터
-> Module Studio
-> 승인안 확정
-> 원천데이터 -> Adapter -> Module -> Result Asset
-> OPS
-> Template Contract
-> Builder(Template Injection)
```

핵심 포인트:

- Studio는 `승인안`을 만든다.
- Official Layer는 `공식 Result Asset`을 만든다.
- OPS는 `공식 Result Asset`만 읽는다.
- Builder는 `공식 Result Asset을 HTML로 보여주는 단계`일 뿐이다.
- 현재는 `보여주고 싶은 화면 계약`이 먼저 있고, 데이터가 그 계약에 맞게 정리된다.

---

## 5. 모듈별 Studio 역할

## 5.1 Sandbox Studio

### 목적

분석 시나리오를 여러 번 돌려보고, 어떤 분석 조건을 공식 실행에 넣을지 정한다.

### Studio에서 하는 일

- 입력 자산 조합 선택
- 조인 조건 조정
- 지표 조합 변경
- 시나리오 비교
- 품질 상태 확인

### 승인안 산출물 예시

- `approved_sandbox_scenario.json`

### 공식 실행으로 넘기는 것

- 승인된 시나리오 정의
- 입력 자산 목록
- 품질 임계치

---

## 5.2 TO Studio

### 목적

권역안과 담당자 배치안을 여러 번 비교해보고, 공식 권역안을 정한다.

### Studio에서 하는 일

- 권역 경계 조정
- 담당자 재배치 시나리오 비교
- 예외 병원/약국 처리
- 커버리지 비교
- 승인 후보안 선택

### 승인안 산출물 예시

- `approved_territory_plan.json`

### 공식 실행으로 넘기는 것

- 권역안 버전
- 담당자 배치안
- 예외 규칙
- 기준 시나리오 ID

---

## 5.3 PDF Studio

### 목적

쉐어 룰과 예외 처리안을 여러 번 검토해보고, 공식 정산 룰셋을 정한다.

### Studio에서 하는 일

- 분기별 쉐어 룰 조정
- 전분기 연장 여부 검토
- 미포착/예외 케이스 검토
- 정산 결과 비교
- 승인 후보 룰셋 선택

### 승인안 산출물 예시

- `approved_prescription_ruleset.json`

### 공식 실행으로 넘기는 것

- 룰 버전
- 예외 처리 규칙
- 승인된 기준일
- 검토 메모

---

## 6. Builder의 위치 재정의

Builder는 `모듈 스튜디오 대상`이 아니다.

왜냐하면:

- Builder는 계산 모듈이 아니다.
- Builder는 독립 Result Asset을 만들지 않는다.
- Builder는 외부 템플릿을 받아 최종 HTML에 데이터를 주입하는 단계다.
- 현재는 `보여줄 미리보기 기준`으로 템플릿을 먼저 만들고, 데이터도 그 템플릿 계약에 맞춰 생산한다.

즉 Builder는 아래처럼 이해하는 것이 맞다.

```text
Result Asset -> Template Contract -> Builder Input Mapping -> Template Injection -> HTML
```

이 뜻은 다음과 같다.

1. 먼저 어떤 미리보기를 보여줄지 정한다.
2. 그 기준으로 템플릿을 만든다.
3. 각 모듈 데이터도 그 템플릿이 요구하는 형태로 맞춘다.
4. 마지막에 HTML을 만든다.

정리하면:

- `Sandbox / TO / PDF` = Studio 대상
- `Builder` = Studio 대상 아님

템플릿 작업공간이 필요하면 둘 수는 있지만,
그것은 `모듈 스튜디오`가 아니라 `템플릿 작업공간`으로 따로 보는 것이 맞다.

---

## 7. 승인안의 공통 규격

모듈마다 이름은 달라도, 승인안은 공통 메타를 가져가는 것이 좋다.

권장 공통 필드:

- `module_name`
- `scenario_id`
- `approved_version`
- `approved_by`
- `approved_at`
- `approval_note`
- `source_snapshot_ref`
- `input_refs`
- `quality_status`
- `publish_ready`

한 줄로 말하면,
Studio는 각자 달라도 `승인 메타`는 공통 틀을 써야 OPS 생태계가 덜 흔들린다.

---

## 8. 화면 구조 제안

하나의 OPS 안에 아래 메뉴 구조를 두는 방식을 권장한다.

### 8.1 공통 메뉴

- `Official OPS`
- `Studio Home`
- `Scenario Compare`
- `Approve / Publish`
- `Run History`

### 8.2 모듈별 Studio 메뉴

- `Sandbox Studio`
- `TO Studio`
- `PDF Studio`

### 8.3 화면 역할 구분

- Studio 화면
  - 실험
  - 비교
  - 승인안 생성
- Official 화면
  - 공식 실행
  - Result Asset 확인
  - OPS 평가 확인
- Builder 화면
  - 승인된 Result Asset 기반 최종 HTML 미리보기

---

## 9. 데이터 경계 원칙

## 9.1 Studio가 해도 되는 일

- 원천/참조데이터 기반 시나리오 실행
- 임시 비교 결과 생성
- 승인안 저장

## 9.2 Studio가 하면 안 되는 일

- 공식 Result Asset 직접 확정
- OPS 평가 결과 직접 수정
- Builder 최종 결과를 공식 결과처럼 대체

## 9.3 Official Layer가 해야 하는 일

- 승인된 안을 넣고 다시 공식 실행
- 공식 Result Asset 생성

## 9.4 OPS가 해야 하는 일

- 공식 Result Asset 검증
- 승인 메타 확인
- 최종 전달 판단

## 9.5 Builder가 해야 하는 일

- 승인된 결과만 읽기
- 템플릿 계약 확인
- 외부 템플릿에 데이터 주입
- 최종 HTML 생성

---

## 10. 왜 이 구조가 좋은가

### 장점 1. 하나의 시스템으로 유지할 수 있다

별도 툴이 여러 개 흩어지지 않는다.

### 장점 2. 실험과 공식 지표를 분리할 수 있다

아직 검토 중인 값이 공식 숫자를 흔들지 않는다.

### 장점 3. 재현성이 높아진다

`원천데이터 + 승인안 + 공식 모듈`로 다시 돌릴 수 있어
왜 이런 결과가 나왔는지 추적하기 쉽다.

### 장점 4. Builder를 과하게 키우지 않는다

표현 단계를 계산 단계와 분리하므로,
Builder가 다시 무거운 엔진처럼 커지는 것을 막을 수 있다.

또한 현재처럼 `템플릿 계약을 먼저 고정`하면,
보고서마다 필요한 데이터 범위를 더 분명하게 통제할 수 있다.

---

## 11. 주요 리스크와 대응

### 리스크 1. Studio가 공식 실행을 대체해버릴 수 있음

대응:

- Studio는 승인안까지만 만든다고 문서와 UI에서 분명히 표시

### 리스크 2. 승인 절차가 모듈마다 제각각 될 수 있음

대응:

- 승인 메타 공통 필드 사용
- `approved_version`, `approved_by`, `approved_at` 표준화

### 리스크 3. 운영자가 Studio와 Official을 헷갈릴 수 있음

대응:

- 메뉴와 화면 색/배지/문구를 분리
- `Experimental` / `Official` 표시 고정

### 리스크 4. Builder가 다시 엔진처럼 비대해질 수 있음

대응:

- Builder는 템플릿 주입 단계라는 점을 문서와 코드에서 계속 유지
- 템플릿 계약은 강하게 가져가되, 계산 로직이 Builder 안으로 들어오지 않게 막는다

---

## 12. 권장 구현 순서

Part 2에서 Studio를 붙인다면 아래 순서를 권장한다.

1. 공통 Studio Shell
2. TO Studio
3. PDF Studio
4. Sandbox Studio

이 순서가 좋은 이유:

- TO와 PDF가 가장 먼저 `반복 실험 공간`의 필요가 크고
- Sandbox는 그 다음 분석 시나리오 고도화에 맞다
- Builder는 계산 모듈이 아니므로 Studio 구현 순서에 넣지 않는다

---

## 13. 완료 기준

모듈 스튜디오 기획이 제대로 반영됐다고 보려면 아래가 맞아야 한다.

1. 공식 파이프라인은 그대로 유지된다.
2. Studio 결과와 공식 Result Asset이 분리된다.
3. 승인안 공통 메타가 정의된다.
4. OPS는 공식 Result Asset만 읽는다.
5. Builder는 승인된 공식 결과만 읽고 템플릿 주입만 한다.
6. Builder 전용 Result Asset을 새로 만들지 않는다.
7. 템플릿 계약이 먼저 정해지고, 데이터는 그 계약에 맞게 정리된다.
8. 운영자가 Studio와 Official을 화면에서 쉽게 구분할 수 있다.

---

## 14. 최종 정리

모듈 스튜디오는
`기존 OPS 구조를 깨는 기능`이 아니라,
`OPS 생태계 안에서 실험과 공식 반영을 분리해 주는 앞단 계층`이다.

가장 중요한 문장은 이것이다.

`Studio는 승인안을 만들고, 공식 결과는 공용 파이프라인이 다시 만든다. Builder는 템플릿 계약에 맞춰 그 공식 결과를 주입해 보여준다.`
