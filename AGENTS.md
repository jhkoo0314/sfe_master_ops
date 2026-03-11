# Project Guardrails

이 저장소에서 작업할 때는 아래 원칙을 계속 지킨다.

이 문서는 단순 메모가 아니라,  
코드 수정, 문서 수정, 운영 검증 때 계속 따라야 하는 기준이다.

---

## 1. 가장 중요한 한 줄

```text
원천데이터 -> Adapter -> Module -> Result Asset -> OPS -> Builder
```

즉:

- raw를 OPS로 바로 보내지 않는다
- adapter가 먼저 정리한다
- module은 자기 Result Asset을 만든다
- OPS는 Result Asset만 보고 판단한다
- Builder는 마지막 표현 단계다

여기서 OPS는 `직접 계산하는 엔진`이 아니라
`중앙 관제 게이트`로 이해한다.

---

## 2. 현재 프로젝트 상태

지금 이 저장소는 `완전 범용 제품`이라기보다  
`회사별로 얇게 커스텀 가능한 공통 틀`에 가깝다.

현재 검증 기준:

- 회사 코드별 동적 폴더 구조 사용
- Streamlit 운영 콘솔에서 실제 파이프라인 실행 가능
- CRM / Prescription / Sandbox / Territory / Builder 검증 가능
- HTML 보고서 5종 생성 가능
  - CRM
  - Sandbox
  - Territory
  - Prescription
  - Total Valid

중요:

- 회사가 바뀌면 `공통 틀 + 얇은 커스텀` 방식으로 간다
- 억지로 100% 범용처럼 보이게 만들지 않는다

---

## 3. OPS 세계관

- 중심은 `Sandbox`가 아니라 `OPS`다
- `Sandbox`는 핵심 분석 모듈이지만 허브는 아니다
- 모듈끼리 직접 raw를 주고받지 않는다
- 모듈 간 교환 단위는 `Result Asset`이다
- 현재 구조는 `유기적 양방향 연결`보다 `단방향 검증 확장`에 가깝다

쉽게 말하면:

- `adapter` = 회사별 차이를 흡수하는 입구
- `module` = 자기 결과를 만드는 처리기
- `OPS` = 중간 매핑 검증 + 품질 게이트 + 다음 전달 판단을 하는 중앙 관제실
- `builder` = 사람이 보는 결과물 생성기

---

## 4. 현재 운영 콘솔 기준

운영 콘솔은 `ui/ops_console.py`를 진입점으로 쓰고, 아래로 분리되어 있다.

- `ui/console_shared.py`
- `ui/console_sidebar.py`
- `ui/console_tabs.py`

운영 콘솔의 현재 역할:

- 회사 코드 입력
- 실행모드 선택
- raw 업로드
- 실행 전 반영 파일 확인
- 실제 파이프라인 실행
- 산출물 확인
- HTML 보고서 열기/다운로드

주의:

- 업로드만 했을 때는 세션 상태다
- 실제 `data/company_source/{company_key}` 반영은 실행 시점이다

---

## 5. 회사 코드 원칙

지금은 모든 실행이 `회사 코드(company_key)` 기준으로 움직인다.

예:

```text
data/company_source/{company_key}/
data/ops_standard/{company_key}/
data/ops_validation/{company_key}/
```

즉:

- 폴더명은 회사 이름이 아니라 `회사 코드`
- 회사 이름은 표시용

새 작업을 만들 때도 이 구조를 먼저 지킨다.

---

## 6. Builder 원칙

Builder는 직접 raw를 보지 않는다.

반드시 아래 흐름을 따른다.

```text
Result Asset -> builder_input_standard -> builder_payload_standard -> HTML
```

현재 모듈별 연결 방식은 이렇게 본다.

- CRM
  - `crm_result_asset.json` 생성
  - `crm_builder_payload.json` 생성
  - Builder는 이 payload만 읽어 `crm_analysis_preview.html` 생성
- Prescription
  - `prescription_result_asset.json` 생성
  - `prescription_builder_payload.json` 생성
  - Builder는 이 payload만 읽어 `prescription_flow_preview.html` 생성
- Territory
  - `territory_result_asset.json` 생성
  - `territory_builder_payload.json` 생성
  - Builder는 이 payload만 읽어 `territory_map_preview.html` 생성
- Sandbox
  - `sandbox_result_asset.json` 안의 `dashboard_payload.template_payload`를 Builder가 사용
  - 별도 `sandbox_builder_payload.json` 파일은 현재 없다

현재 템플릿:

- `templates/report_template.html`
- `templates/crm_analysis_template.html`
- `templates/territory_optimizer_template.html`
- `templates/prescription_flow_template.html`
- `templates/total_valid_templates.html`

현재 상태:

- WebSlide 기능은 제거됨
- Builder는 계산 엔진이 아니라 `payload 주입기`에 가깝다
- 통합 보고서는 슬라이드 도구가 아니라 `개별 HTML 허브`
- 최종 결과 확인은 결국 템플릿이 있어야 가능하므로, 현재 흐름은 템플릿 기반 단방향 검증으로 본다

---

## 7. Prescription 원칙

Prescription은 지금도 가장 무거운 모듈이다.

그래서 아래 원칙을 지킨다.

- 미리보기 HTML은 가볍게 유지
- 전체 원본은 다운로드 파일로 분리
- 미리보기에 원본 전체를 다 싣지 않는다
- `비교표`와 `보조표`는 필요 최소한만 넣는다

즉:

- 미리보기 = 빠르게 확인
- 원본 = 엑셀 다운로드로 확인

---

## 8. 통합 보고서 원칙

`total_valid_preview.html`은 통합 실행 결과를 한 번에 보는 화면이다.

현재 기준:

- 왼쪽 사이드바에 4개 보고서가 항상 보임
- 생성된 보고서는 활성
- 없는 보고서는 비활성
- 오른쪽은 iframe 미리보기

즉 통합 보고서는:

- 새 계산 엔진이 아니라
- 생성된 개별 HTML을 묶는 허브다

---

## 9. 구현 순서 원칙

새 기능을 붙일 때는 가능하면 이 순서를 지킨다.

1. raw 입력 구조 확인
2. adapter 확인 또는 수정
3. module 로직 확인 또는 수정
4. Result Asset 확인
5. OPS 평가 연결
6. Builder payload 연결
7. UI 반영
8. 문서 갱신

앞단이 안 됐는데 뒷단부터 예쁘게 만들지 않는다.

---

## 10. 문서 수정 원칙

문서는 현재 실제 상태를 반영해야 한다.

특히 아래 항목이 바뀌면 같이 갱신한다.

- 실행 파일 경로
- 회사 코드 구조
- 운영 콘솔 구조
- 생성 산출물 이름
- 통합 보고서 구조
- WebSlide 여부

즉:

- 코드만 바꾸고 문서를 방치하지 않는다

---

## 11. 설명 방식

- 비개발자도 이해할 수 있게 아주 쉽게 설명한다
- 어려운 용어보다 역할 중심으로 설명한다
- “왜 이렇게 바꾸는지”를 짧게 같이 말한다
- 현재 상태와 앞으로 할 일을 구분해서 말한다

---

## 12. 금지할 오해

- Sandbox가 전체 허브라고 생각하지 않는다
- OPS가 raw를 직접 읽는다고 생각하지 않는다
- OPS가 직접 분석 계산을 다 하는 엔진이라고 생각하지 않는다
- 회사 데이터가 다 같을 거라고 가정하지 않는다
- Builder가 중심 엔진이라고 생각하지 않는다
- 통합 보고서가 새 분석을 하는 곳이라고 생각하지 않는다

---

## 13. 한 줄 결론

`이 저장소는 회사별 raw를 adapter-first로 흡수하고, OPS는 중간 검증 게이트로 판단하며, 통과한 결과만 Builder 템플릿으로 넘기는 구조로 유지한다.`
