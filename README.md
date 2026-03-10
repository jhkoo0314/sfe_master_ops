# ⚡ SFE OPS — Sales Force Effectiveness Operations Engine

> **"어떤 데이터가 들어와도 붙여서 분석할 수 있는 범용 영업 효율화 엔진"**
>
> 회사의 원천 데이터 포맷에 종속되지 않는 **Adapter-First, Template-Driven** 설계.  
> CRM · 실적 · 목표 · Prescription 데이터를 표준화하여 최종 HTML 보고서와 지도 대시보드를 자동 생성한다.

---

## 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [설계 원칙](#2-설계-원칙)
3. [아키텍처](#3-아키텍처)
4. [디렉토리 구조](#4-디렉토리-구조)
5. [파이프라인 흐름](#5-파이프라인-흐름)
6. [모듈별 설명](#6-모듈별-설명)
7. [설치 및 실행](#7-설치-및-실행)
8. [API 엔드포인트](#8-api-엔드포인트)
9. [데이터 투입 방법](#9-데이터-투입-방법)
10. [커스텀 분석 템플릿 추가](#10-커스텀-분석-템플릿-추가)
11. [개발 현황](#11-개발-현황)

---

## 1. 프로젝트 개요

SFE OPS는 제약 영업(SFE, Sales Force Effectiveness)을 위한 **데이터 분석 자동화 엔진**입니다.

### 핵심 문제 의식

- 회사마다 CRM, 실적, 목표 데이터의 **컬럼명과 포맷이 다름**
- 매번 분석 코드를 새로 짜거나 엑셀로 수작업 → **비효율**
- 분석 결과를 보고서로 만드는 데 **추가 리소스 소요**

### OPS가 제공하는 것

| 기능                       | 설명                                                |
| -------------------------- | --------------------------------------------------- |
| **유니버설 Adapter**       | 어떤 컬럼명이든 Config 파일로 매핑하면 표준화       |
| **자동 분석 엔진**         | 병원별 매출·달성률·방문수·조인율 자동 계산          |
| **Template-Driven 보고서** | 보고서 틀을 먼저 정의하고 데이터를 역방향 주입      |
| **지도 시각화**            | 권역별 마커·동선·히트맵 자동 생성 (Leaflet)         |
| **WebSlide 제작기**        | WebSlide Architect v3.5 페르소나 내장 슬라이드 제작 |
| **단일 HTML 산출물**       | 브라우저에서 바로 실행 가능한 보고서·지도·슬라이드  |

---

## 2. 설계 원칙

### 원칙 1: Adapter-First (어댑터 우선)

원천 데이터를 엔진이 직접 읽지 않는다.  
반드시 **Adapter Config**를 통해 표준 스키마로 변환한 후 엔진에 투입한다.

```
회사 원천 데이터 (어떤 포맷이든)
    ↓  [Adapter Config — 컬럼 매핑]
표준 도메인 레코드 (hospital_id, product_id, yyyymm ...)
    ↓  [Module Engine]
Result Asset → OPS 평가 → Handoff
```

### 원칙 2: Template-Driven Analysis (역방향 분석)

"데이터가 있으니 뭘 보여줄까?" ❌  
"이 보고서에 무엇이 필요한가? → 그것만 계산하라" ✅

```python
# 템플릿이 먼저 정의됨
SummaryCard(label="평균 달성률", metric_key="avg_attainment_rate")

# 엔진이 metric_key를 읽어 자동으로 값 주입
# → service.py 수정 없이 새 템플릿 추가 가능
```

### 원칙 3: hospital_id 단일 조인 키

모든 도메인(CRM · 실적 · 목표 · Prescription)은 `hospital_id`를 기준으로 조인.  
병원명 기반 역매핑을 fallback으로 지원.

### 원칙 4: OPS가 Handoff를 결정

모듈이 직접 다음 단계로 넘어가지 않는다.  
**OPS 품질 게이트**가 PASS/WARN/FAIL을 판정한 후에만 다음 모듈로 진행.

```
모듈 실행 → Result Asset 생성 → OPS 평가 → PASS → 다음 모듈
                                                 → FAIL → 중단 + 권고사항
```

---

## 3. 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                   SFE OPS Engine                         │
│                                                          │
│  원천데이터                                               │
│  (CRM/실적/목표/Rx)                                      │
│       │                                                  │
│       ▼                                                  │
│  ┌─────────┐    ┌──────────┐    ┌────────────────────┐  │
│  │ Adapter │ → │  Module  │ → │   Result Asset      │  │
│  │ Config  │    │  Engine  │    │  (Pydantic 모델)    │  │
│  └─────────┘    └──────────┘    └────────────────────┘  │
│                                          │               │
│                                 ┌────────▼──────────┐   │
│                                 │   OPS Core API     │   │
│                                 │  품질게이트 평가    │   │
│                                 └────────┬──────────┘   │
│                              PASS        │       FAIL    │
│                         ┌────▼───┐  ┌───▼───────┐      │
│                         │ 다음   │  │  중단 +   │      │
│                         │ 모듈   │  │  권고사항  │      │
│                         └────────┘  └───────────┘      │
└─────────────────────────────────────────────────────────┘
```

### 기술 스택

| 영역               | 기술                                             |
| ------------------ | ------------------------------------------------ |
| 스키마·유효성 검사 | Python · Pydantic v2                             |
| 데이터 처리        | Polars                                           |
| API 서버           | FastAPI                                          |
| 지도 렌더링        | Leaflet.js                                       |
| 차트               | Chart.js                                         |
| 운영 콘솔          | Streamlit                                        |
| HTML 보고서        | Vanilla HTML/CSS/JS                              |
| 공공 데이터        | 건강보험심사평가원 HIRA, 행안부 약국·도매 마스터 |

---

## 4. 디렉토리 구조

```
c:\sfe_master_ops\
│
├── adapters/                   # Adapter Config 및 변환 로직
│   ├── crm/                    # CRM Adapter (HIRA 병원 마스터 매핑)
│   ├── sandbox/                # 실적·목표 Adapter
│   └── territory/              # 권역 Adapter
│
├── modules/                    # 분석 엔진 모듈
│   ├── crm/                    # CRM 행동 분석
│   ├── prescription/           # 처방 흐름 분석
│   ├── sandbox/                # 통합 분석 엔진 (핵심)
│   │   ├── schemas.py          # 입력·출력 스키마
│   │   ├── service.py          # 분석 로직 + Template Injector
│   │   └── templates.py        # 보고서 템플릿 계약 (장차 커스텀 확장)
│   ├── territory/              # 권역 최적화 모듈
│   │   ├── schemas.py          # MapMarker, RepRoute, RegionZone
│   │   ├── service.py          # SlotKey 기반 마커·동선 자동 생성
│   │   └── templates.py        # 지도 템플릿 계약
│   └── builder/                # HTML 보고서 + WebSlide
│       ├── schemas.py          # OpsReportPayload, WebSlideSession
│       └── service.py          # 보고서 변환 로직
│
├── result_assets/              # 최종 산출물 스키마
│   ├── crm_result_asset.py
│   ├── prescription_result_asset.py
│   ├── sandbox_result_asset.py
│   ├── territory_result_asset.py
│   └── html_builder_result_asset.py (예정)
│
├── ops_core/                   # OPS 평가 엔진
│   ├── main.py                 # FastAPI 앱 진입점
│   ├── api/                    # 모듈별 평가 라우터
│   │   ├── crm_router.py           POST /ops/crm/evaluate
│   │   ├── prescription_router.py  POST /ops/prescription/evaluate
│   │   ├── sandbox_router.py       POST /ops/sandbox/evaluate
│   │   ├── territory_router.py     POST /ops/territory/evaluate
│   │   └── pipeline_router.py      POST /ops/pipeline/run
│   └── workflow/
│       ├── schemas.py          # 파이프라인 실행 스키마
│       └── orchestrator.py     # 전체 파이프라인 오케스트레이터
│
├── ui/                         # 사용자 인터페이스
│   ├── ops_console.py          # Streamlit 운영 콘솔 (5탭)
│   └── html_builder.html       # HTML Builder (OPS보고서 + WebSlide Studio)
│
├── common/                     # 공통 유틸
│   ├── types.py                # QualityGateStatus 등 공통 타입
│   ├── exceptions.py           # MissingResultAssetError 등
│   └── validators.py           # 공통 유효성 검사
│
├── data/                       # 공공 원천 데이터 (불변)
│   ├── hospital_master/        # 건강보험심사평가원 병원 정보 서비스
│   ├── phamacy_master/         # 약국 정보 서비스
│   └── wholsale_master/        # 전국 의약품 도매업소 표준데이터
│
├── tests/                      # 단위·통합 테스트
│   ├── fixtures/               # 테스트 픽스처
│   ├── test_sandbox/
│   └── test_territory/
│
└── docs/
    ├── TODO.md                 # 개발 현황 및 체크리스트
    └── Main_WebSlide Architect v3.5.md  # WebSlide 페르소나
```

---

## 5. 파이프라인 흐름

```
POST /ops/pipeline/run
         │
STEP 1   ▼
  ┌─────────────┐
  │  CRM 평가   │ → FAIL → 즉시 중단
  └──────┬──────┘
  PASS / WARN
         │
STEP 2   ▼
  ┌──────────────────────┐
  │  Prescription 평가   │ → FAIL → 경고만 (선택적 모듈, 계속 진행)
  └──────────┬───────────┘
             │
STEP 3       ▼
  ┌─────────────────┐
  │  Sandbox 분석   │ → FAIL → 즉시 중단
  └────────┬────────┘
  PASS → next_modules에 "territory" 추가
           │
STEP 4     ▼
  ┌──────────────────┐
  │  Territory 최적화 │ → FAIL → 권고사항만 (Builder는 계속 eligible)
  └────────┬─────────┘
  PASS → next_modules에 "builder" 추가
           │
STEP 5     ▼
  ┌─────────────────────────────────────────┐
  │  HTML Builder                           │
  │  Layer 1: OPS 분석 보고서 자동 렌더링    │
  │  Layer 2: WebSlide Architect v3.5 제작  │
  └─────────────────────────────────────────┘
```

---

## 6. 모듈별 설명

### Phase 2: CRM (Behavior CRM)

- HIRA 병원 마스터(공공데이터)와 회사 CRM 데이터를 `hospital_id`로 연결
- 병원별 담당자, 방문 이력, 활동 유형 표준화
- 출력: `crm_result_asset`

### Phase 3: Prescription (처방 흐름)

- 도매 → 약국 → 병원 흐름을 `hospital_id` 기준으로 추적
- 공공 약국 마스터·도매 마스터로 실매핑
- 출력: `prescription_result_asset`

### Phase 4: Sandbox (통합 분석 엔진)

- CRM + 실적 + 목표 + (선택) Prescription을 `(hospital_id, yyyymm)` 기준 집계
- **Template-Driven**: `templates.py`에 `metric_key`를 선언하면 자동 주입
- 집계 단위: `monthly` / `quarterly` / `yearly` / `total`
- 사용자 정의 가중치(`weight_config`) 지원
- 출력: `sandbox_result_asset` (분석 요약 + 조인 품질 + Handoff 후보)

### Phase 5: Territory Optimizer (권역 최적화)

- Sandbox 결과를 지도 위에 배치
- **SlotKey 자동 주입**: `color_key`, `size_key`, `tooltip_key`로 마커 스타일 결정
- 담당자 동선(Route) 자동 생성, 권역 히트맵(RegionZone) 집계
- SIDO_CENTROIDS 기반 좌표 (실좌표 없을 시 시도 중심점 사용)
- 출력: `territory_result_asset` (마커 + 동선 + 히트맵 + 갭 목록)

### Phase 6: HTML Builder

**Layer 1 — OPS 분석 보고서**

- Sandbox/Territory/CRM Result Asset → HTML 템플릿 자동 렌더링
- Leaflet.js 기반 인터랙티브 지도
- HTML 파일로 다운로드 (오프라인 실행 가능)

**Layer 2 — WebSlide Studio**

- WebSlide Architect v3.5 페르소나 내장
- 텍스트 붙여넣기 / 파일 업로드 / OPS 데이터 임포트
- PHASE 0~3 상태머신: Intake → Strategy → Blueprint → Build
- 5가지 테마 (A Premium · B Swiss · C Keynote · D Dashboard · E Dark Tech)
- 단일 HTML 슬라이드 다운로드

### Phase 7: OPS Core 통합

- 전체 파이프라인 오케스트레이터 (`run_pipeline`)
- `POST /ops/pipeline/run` — 5단계 순차 평가
- `GET /ops/pipeline/status` — 모듈별 마지막 상태
- `GET /ops/diagram` — 파이프라인 다이어그램
- FAIL 즉시 중단 / WARN 계속 진행 / next_modules 자동 결정

### Phase 8: Streamlit 운영 콘솔

- 비개발자를 위한 그래픽 운영 화면
- **5탭**: 대시보드 / 데이터 투입 / 파이프라인 실행 / 분석 결과 / 보고서 생성
- 파이프라인 흐름 시각화 (모듈별 PASS/WARN/FAIL 상태)
- CSV/XLSX 업로드 + Adapter 컬럼 매핑 UI
- HTML Builder 연동 버튼

---

## 7. 설치 및 실행

### 사전 요구사항

```bash
Python 3.11+
pip install -r requirements.txt
```

### requirements.txt (주요 패키지)

```
fastapi
uvicorn
pydantic>=2.0
polars
streamlit>=1.51
pandas
openpyxl
pytest
```

### OPS API 서버 실행

```bash
cd c:\sfe_master_ops
uvicorn ops_core.main:app --reload --port 8000
```

### Streamlit 운영 콘솔 실행

```bash
cd c:\sfe_master_ops
streamlit run ui/ops_console.py --server.port 8502
# → http://localhost:8502
```

### HTML Builder 실행

브라우저에서 직접 열기:

```
c:\sfe_master_ops\ui\html_builder.html
```

### 테스트 실행

```bash
cd c:\sfe_master_ops
pytest tests/ -v
```

---

## 8. API 엔드포인트

| 메서드 | 경로                         | 설명                           |
| ------ | ---------------------------- | ------------------------------ |
| GET    | `/health`                    | 서버 상태 확인                 |
| GET    | `/ops/diagram`               | 파이프라인 다이어그램          |
| GET    | `/ops/status`                | 전체 모듈 상태                 |
| POST   | `/ops/crm/evaluate`          | CRM Result Asset 평가          |
| POST   | `/ops/prescription/evaluate` | Prescription Result Asset 평가 |
| POST   | `/ops/sandbox/evaluate`      | Sandbox Result Asset 평가      |
| POST   | `/ops/territory/evaluate`    | Territory Result Asset 평가    |
| POST   | `/ops/pipeline/run`          | 전체 파이프라인 실행           |
| GET    | `/ops/pipeline/status`       | 파이프라인 상태 요약           |
| GET    | `/ops/pipeline/modules`      | 활성 모듈 목록                 |

API 문서: `http://localhost:8000/docs` (Swagger UI)

---

## 9. 데이터 투입 방법

### 방법 A: Streamlit 콘솔 업로드

1. `http://localhost:8502` 접속
2. **📂 데이터 투입** 탭 → CRM/실적/목표 파일 업로드
3. 컬럼 매핑 설정 (Adapter Config)
4. **🚀 파이프라인 실행** 탭 → "파이프라인 실행" 버튼

### 방법 B: Adapter Config 파일로 매핑

```python
# adapters/sandbox/adapter_config.py 예시
SalesAdapterConfig(
    hospital_id_col="거래처코드",      # 회사 컬럼명
    hospital_name_col="거래처명",
    product_id_col="제품코드",
    sales_amount_col="매출금액",
    yyyymm_col="실적년월",
    rep_id_col="담당자사번",
)
```

### 방법 C: API 직접 호출

```python
import requests

payload = {
    "scenario": "crm_sales_target",
    "crm_asset": { ... },    # crm_result_asset JSON
    "sandbox_asset": { ... } # sandbox_result_asset JSON
}
resp = requests.post("http://localhost:8000/ops/pipeline/run", json=payload)
print(resp.json())
```

---

## 10. 커스텀 분석 템플릿 추가

### Sandbox 커스텀 보고서 추가

`modules/sandbox/templates.py`에 새 카드를 추가하면 `service.py` 수정 없이 자동 주입됩니다.

```python
# 예: 성과급 계산 보고서용 카드 추가
SummaryCard(label="인센티브 지급 대상", metric_key="fully_joined_hospitals")
SummaryCard(label="전체 달성률",        metric_key="avg_attainment_rate")
```

### Territory 커스텀 지도 템플릿 추가

```python
# modules/territory/templates.py에 추가
@classmethod
def get_incentive_template(cls) -> "TerritoryMapContract":
    return cls(
        map_title="인센티브 대상 병원 지도",
        marker_style=MarkerStyleSlot(
            color_key="attainment_color",   # 달성률 기반 색상
            size_key="sales_size",          # 매출 기반 크기
            tooltip_key="sales_focus",      # 간결한 툴팁
        ),
        show_heatmap=False,
        show_gaps=False,
    )
```

---

## 11. 개발 현황

| Phase | 모듈                | 산출물                        | 상태    |
| ----- | ------------------- | ----------------------------- | ------- |
| 1     | 환경 구성           | 폴더 구조, 의존성, 공공데이터 | ✅ 완료 |
| 2     | Behavior CRM        | `crm_result_asset`            | ✅ 완료 |
| 3     | Prescription        | `prescription_result_asset`   | ✅ 완료 |
| 4     | SFE Sandbox         | `sandbox_result_asset`        | ✅ 완료 |
| 5     | Territory Optimizer | `territory_result_asset`      | ✅ 완료 |
| 6     | HTML Builder        | `html_builder_result_asset`   | ✅ 완료 |
| 7     | OPS Core 통합       | 품질 게이트 + 파이프라인      | ✅ 완료 |
| 8     | Streamlit 운영 콘솔 | 비개발자 운영 화면            | ✅ 완료 |

---

## 공공 데이터 출처

| 데이터                          | 출처                      | 비고         |
| ------------------------------- | ------------------------- | ------------ |
| 병원 정보 서비스                | 건강보험심사평가원 (HIRA) | 2025.12 기준 |
| 약국 정보 서비스                | 건강보험심사평가원 (HIRA) | 2025.12 기준 |
| 전국 의약품 도매업소 표준데이터 | 행정안전부                | 최신 기준    |

공공 데이터는 불변 기준 데이터로 `data/` 폴더에 보관.  
회사 원천 데이터는 Adapter를 통해 이 공공 데이터와 `hospital_id`로 연결됩니다.

---

## 라이선스

내부 프로젝트 — 외부 공개 금지

---

_SFE OPS Engine — Built with Python · FastAPI · Pydantic · Streamlit · Leaflet.js_
# sfe_master_ops
