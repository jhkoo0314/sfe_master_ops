# Builder And Outputs

## 목적

이 문서는 HTML Builder의 위치, 입력 원칙, 주요 출력 구조를 정리한다.

## Builder 정의

HTML Builder는 OPS가 허용한 Result Asset을 사람이 읽는 HTML 보고 자산으로 바꾸는 최종 표현 모듈이다.

## Builder 원칙

1. Builder는 계산 중심 모듈이 아니다.
2. Builder는 raw를 직접 해석하지 않는다.
3. Builder는 Result Asset 기반으로만 동작한다.
4. Builder는 마지막 소비 모듈이다.

## 공식 입력 흐름

`Result Asset -> builder_input_standard -> builder_payload_standard -> HTML`

## 모듈별 연결 예시

- CRM  
  `crm_result_asset.json -> crm_builder_payload.json -> crm_analysis_preview.html`
  - CRM KPI는 `crm_result_asset` 값만 주입하고 Builder에서 재계산하지 않는다.

- Prescription  
  `prescription_result_asset.json -> prescription_builder_payload.json -> prescription_flow_preview.html`

- Territory  
  `territory_result_asset.json -> territory_builder_payload.json -> territory_map_preview.html`
  - `territory_map_preview_assets/*.js`와 `territory_map_preview_assets/leaflet/*`를 함께 사용한다.
  - Territory 지도는 로컬 Leaflet 라이브러리 기준으로 열리고, Builder에서 KPI를 재계산하지 않는다.

- Sandbox  
  `sandbox_result_asset.json -> dashboard payload -> sandbox_report_preview.html`
  - Sandbox payload는 CRM KPI 입력값을 사용하며 Sandbox 내부에서 CRM KPI를 재계산하지 않는다.

## 통합 보고서 원칙

`total_valid_preview.html`은 개별 보고서를 묶는 허브다.

원칙:
- 새 계산 엔진이 아니다.
- 이미 생성된 결과를 연결해 보여준다.
- 없는 보고서는 비활성일 수 있다.

## 주요 출력 경로

- `data/ops_validation/{company_key}/crm/`
- `data/ops_validation/{company_key}/prescription/`
- `data/ops_validation/{company_key}/sandbox/`
- `data/ops_validation/{company_key}/territory/`
- `data/ops_validation/{company_key}/builder/`

대표 결과물:
- `crm_analysis_preview.html`
- `sandbox_report_preview.html`
- `territory_map_preview.html`
- `prescription_flow_preview.html`
- `total_valid_preview.html`

대표 보조 asset:
- `builder/territory_map_preview_assets/*.js`
- `builder/territory_map_preview_assets/leaflet/*`
- `builder/sandbox_report_preview_assets/*.js`

## 성능 원칙

- Builder는 payload 주입기에 가깝게 유지한다.
- 무거운 데이터는 분리 asset 구조를 우선한다.
- 첫 화면은 summary 중심으로 가볍게 유지한다.
- Territory는 분리 JS asset + 로컬 Leaflet 라이브러리 번들 기준으로 유지한다.

## 금지할 오해

- Builder가 raw를 읽는다
- Builder가 새 계산을 한다
- 통합 보고서가 새 분석을 한다
- HTML만 생성되면 Result Asset 설명은 필요 없다

## 결론

Builder는 OPS가 허용한 Result Asset을 표준 payload로 바꿔 HTML 결과물로 주입하는 최종 표현 모듈이다.
