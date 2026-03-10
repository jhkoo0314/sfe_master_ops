# Template Payload Spec

작성일: 2026-03-10

## 0. 문서 목적

이 문서는 `templates` 아래 HTML 템플릿에 어떤 데이터를 어떤 모양으로 넣어야 하는지 정리한 공식 규격 문서다.

핵심 목적은 2가지다.

1. 회사가 바뀌어 템플릿이 바뀌어도 `OPS -> Builder -> Template Payload` 방식은 유지한다.
2. 템플릿마다 필요한 데이터 칸만 바꾸고, 모듈 자산과 OPS 연결 방식은 흔들리지 않게 한다.

---

## 1. 기본 원칙

SFE OPS에서 템플릿 연결은 아래 순서를 따른다.

`Result Asset -> builder_input_standard -> builder_payload_standard -> Template HTML`

중요한 뜻은 아래와 같다.

1. 템플릿은 raw를 직접 읽지 않는다.
2. 템플릿은 모듈 내부 계산 로직을 직접 알지 않는다.
3. Builder가 템플릿이 읽을 수 있는 payload로 번역한다.
4. 회사가 바뀌면 보통 바뀌는 것은 템플릿과 payload 규격이지, OPS 세계관 자체가 아니다.

---

## 2. 공통 Builder 계층

### 2.1 BuilderInputReference

템플릿과 원본 자산의 연결 설명서다.

필수 항목:

- `template_key`
- `template_path`
- `source_module`
- `asset_type`
- `source_asset_path`
- `description`

### 2.2 BuilderInputStandard

Builder가 받는 공통 입력 규격이다.

필수 항목:

- `template_key`
- `template_path`
- `report_title`
- `executive_summary`
- `source_references`
- `payload_seed`
- `source_modules`

### 2.3 BuilderPayloadStandard

템플릿이 실제로 읽는 최종 주입 데이터다.

필수 항목:

- `template_key`
- `template_path`
- `report_title`
- `payload`
- `source_modules`
- `output_name`
- `render_mode`

---

## 3. 템플릿별 규격

## 3.1 `report_template.html`

대상 파일:

- `templates/report_template.html`

용도:

- Sandbox 중심의 성과 보고서
- 지점 / 담당자 / 품목 / KPI / 정합성 상태를 한 화면에서 보여줌

현재 `render_mode`:

- `report_data_json`

주입 방식:

- 템플릿 내부 `const db = ...` 자리에 JSON 전체를 넣는다.

payload 필수 키:

- `branches`
- `products`
- `total_prod_analysis`
- `total`
- `total_avg`
- `data_health`
- `missing_data`

### `branches`

설명:

- 지점별 담당자 묶음

형태:

```json
{
  "서울지점": {
    "members": [ ... ],
    "avg": { ... },
    "achieve": 98.7,
    "monthly_actual": [ ... ],
    "monthly_target": [ ... ],
    "analysis": { ... },
    "prod_analysis": {}
  }
}
```

### `branches.{branch}.members[]`

설명:

- 담당자 카드와 개인 분석 화면에 들어가는 핵심 데이터

대표 필드:

- `rep_id`
- `성명`
- `HIR`
- `RTR`
- `BCR`
- `PHR`
- `PI`
- `FGR`
- `처방금액`
- `목표금액`
- `efficiency`
- `sustainability`
- `gini`
- `coach_scenario`
- `coach_action`
- `shap`
- `prod_matrix`
- `monthly_actual`
- `monthly_target`
- `지점순위`

### `products`

설명:

- 품목 선택 드롭다운에 들어가는 값 목록

규칙:

1. 사용자에게 보이는 이름이어야 한다.
2. 현재는 `품목코드`가 아니라 `품목명`을 넣는다.
3. `total_prod_analysis`의 key와 정확히 같아야 한다.

예:

```json
["플라빅스정", "카나브정", "트라젠타정"]
```

### `total_prod_analysis`

설명:

- 품목별 전체 집계 데이터

규칙:

1. key는 `품목명`
2. `products`에 있는 값으로 바로 조회 가능해야 함

예:

```json
{
  "플라빅스정": {
    "achieve": 101.2,
    "avg": {
      "HIR": 83.1,
      "RTR": 71.4,
      "BCR": 79.3,
      "PHR": 68.2,
      "PI": 101.2,
      "FGR": 4.8
    },
    "monthly_actual": [ ... ],
    "monthly_target": [ ... ]
  }
}
```

### `total`

설명:

- 전사 전체 요약

대표 필드:

- `achieve`
- `avg`
- `monthly_actual`
- `monthly_target`
- `analysis`

### `data_health`

설명:

- 데이터 정합성 카드와 매핑 상태 표시용

대표 필드:

- `integrity_score`
- `mapped_fields`
- `missing_fields`

### `missing_data`

설명:

- 목표 누락, orphan 데이터 같은 예외 목록

예:

```json
[
  { "지점": "OPS", "성명": "UNMAPPED", "품목": "orphan_sales_hospitals" }
]
```

---

## 3.2 `Spatial_Preview_260224.html`

대상 파일:

- `templates/Spatial_Preview_260224.html`

용도:

- Territory 지도 미리보기
- 병원 마커 / 담당자 동선 / 기간 필터를 보여줌

현재 `render_mode`:

- `territory_window_vars`

주입 방식:

- `window.__INITIAL_MODE__`
- `window.__INITIAL_MARKERS__`
- `window.__INITIAL_ROUTES__`

payload 필수 키:

- `mode`
- `markers`
- `routes`

### `mode`

설명:

- 지도 초기 표시 모드

예:

- `hospital`
- `routing`

### `markers[]`

설명:

- 지도에 뿌릴 병원 핀 목록

대표 필드:

- `hospital_id`
- `hospital`
- `rep`
- `lat`
- `lon`
- `sales`
- `target`
- `insight`
- `region`
- `sub_region`

### `routes[]`

설명:

- 담당자 방문 동선

대표 필드:

- `rep`
- `month`
- `date`
- `coords`

`coords[]` 대표 필드:

- `seq`
- `hospital`
- `lat`
- `lon`

---

## 4. 새 회사 / 새 템플릿 추가 방법

새 회사가 들어와도 OPS 원칙은 그대로다.

바꾸는 순서는 아래다.

1. 회사 원본형 raw를 adapter가 표준 구조로 변환한다.
2. 각 모듈이 Result Asset을 만든다.
3. OPS가 연결 가능한 자산을 판단한다.
4. Builder가 새 템플릿용 `builder_input_standard`를 만든다.
5. Builder가 새 템플릿용 `builder_payload_standard`를 만든다.
6. 템플릿은 그 payload만 읽는다.

즉 새 회사에서 템플릿이 바뀌어도,
`OPS가 아무 데이터나 직접 HTML에 꽂는 구조`가 아니라
`OPS가 허용한 자산을 Builder가 템플릿 규격으로 번역하는 구조`를 유지해야 한다.

---

## 5. 금지할 방식

아래는 하지 않는다.

1. 템플릿이 raw 파일을 직접 읽게 만드는 것
2. 템플릿이 회사별 컬럼명을 직접 아는 것
3. Builder 없이 모듈 자산을 바로 DOM에 꽂는 것
4. 품목 선택값과 품목 분석 key가 서로 다르게 들어가는 것

---

## 6. 한 줄 결론

`템플릿은 화면 양식이고, Builder payload는 양식에 넣을 값의 규격이며, 회사가 바뀌어도 OPS는 Result Asset 중심 구조를 유지한 채 템플릿별 payload만 바꿔 끼울 수 있어야 한다.`
