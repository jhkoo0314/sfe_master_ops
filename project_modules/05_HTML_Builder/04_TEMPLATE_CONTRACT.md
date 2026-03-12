# Template Contract

작성일: 2026-03-12

## 1. 문서 목적

이 문서는 Builder가 어떤 데이터를 받아 어떤 HTML을 만드는지 미리 고정하는 `템플릿 계약`을 정의한다.

핵심은 간단하다.

- 먼저 무엇을 보여줄지 정한다.
- 그 다음 템플릿을 정한다.
- 그 템플릿이 요구하는 데이터 구조로 payload를 맞춘다.

## 2. 공통 흐름

```text
Result Asset
-> OPS
-> Template Contract
-> Render Payload
-> Template Injection
-> HTML
```

## 3. 공통 계약 필드

권장 필드:

- `template_id`
- `preview_type`
- `template_version`
- `module_name`
- `page_title`
- `header_summary`
- `section_order`
- `cards`
- `tables`
- `charts`
- `map_blocks`
- `download_refs`

## 4. 모듈별 입력 기준

### CRM
- 입력:
  - `crm_result_asset.json`
  - 또는 `crm_builder_payload.json`
- 출력:
  - `crm_analysis_preview.html`

### Sandbox
- 입력:
  - `sandbox_result_asset.json` 내부 dashboard payload
- 출력:
  - `report_preview.html` 또는 sandbox summary HTML

### Territory
- 입력:
  - `territory_result_asset.json`
  - 또는 `territory_builder_payload.json`
- 출력:
  - `territory_map_preview.html`

### Prescription
- 입력:
  - `prescription_result_asset.json`
  - 또는 `prescription_builder_payload.json`
- 출력:
  - `prescription_flow_preview.html`

## 5. 계약 원칙

1. 템플릿이 요구하지 않는 계산은 Builder에서 하지 않는다.
2. 템플릿이 요구하는 데이터는 앞단에서 미리 맞춰둔다.
3. 무거운 상세 테이블은 `download_refs`로 뺀다.
4. 템플릿 변경 시 payload 계약도 함께 점검한다.

## 6. 한 줄 원칙

`Builder는 범용 API가 아니라, 템플릿 계약을 기준으로 데이터를 주입하는 출력 계층이다.`

