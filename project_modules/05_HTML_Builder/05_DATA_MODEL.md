# Render Data Model

작성일: 2026-03-12

## 1. 개요

Builder 데이터 모델은 `job/queue` 중심이 아니라,
`template + payload + html output` 중심으로 보는 것이 맞다.

## 2. 핵심 엔터티

### template_registry
- `template_id`
- `template_name`
- `preview_type`
- `template_version`
- `template_file`
- `active_flag`

### template_contract
- `template_id`
- `module_name`
- `required_sections`
- `required_cards`
- `required_tables`
- `required_map_blocks`
- `download_policy`

### render_payload
- `payload_id`
- `module_name`
- `source_result_asset_ref`
- `template_id`
- `header_summary`
- `section_payload`
- `download_refs`

### render_output
- `output_id`
- `template_id`
- `payload_id`
- `html_file`
- `generated_at`

## 3. 관계 해석

```text
Result Asset
-> Render Payload
-> Template Contract
-> Template Registry
-> Render Output
```

## 4. 모델 원칙

- `Result Asset`은 Builder 밖에서 만들어진다.
- `Render Payload`는 템플릿 계약에 맞춘 입력이다.
- `Render Output`은 공식 결과가 아니라 표현 결과다.

