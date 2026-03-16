# Sandbox Dashboard Refactor Summary
작성일: 2026-03-16  
대상 모듈: `modules/sandbox/`

---

# 1. 리팩토링 배경

초기 Sandbox 대시보드는 다음 구조였다.
Sandbox service
→ template_payload (단일 dict)
→ report_template.html


문제점

- 템플릿과 계산 구조 강한 결합
- 차트 교체 시 payload 구조도 변경 필요
- chunk lazy-load 구조가 템플릿 로직과 혼합
- Builder/에이전트가 분석 자산을 재사용하기 어려움
- 테스트 단위가 템플릿 전체 수준에 머무름

즉

**"분석 데이터 구조"와 "렌더링 구조"가 분리되지 않은 상태였다.**

---

# 2. 리팩토링 목표

리팩토링의 목표는 **템플릿 교체가 가능한 분석 구조**를 만드는 것이었다.

핵심 목표

1. 분석 결과를 **block 단위 자산**으로 정의
2. 템플릿이 **block을 소비하는 구조**로 전환
3. 기존 preview 및 lazy-load 구조 **깨지지 않게 유지**
4. 점진 리팩토링을 위해 **fallback 전략 유지**
5. 구조 전환 안정성을 위해 **테스트 추가**

---

# 3. Stage 1 – Block Contract 정의

Stage 1에서는 **Sandbox 결과 payload를 블록 단위 계약으로 정의**했다.

대표 Block 목록

| block_id | 목적 |
|--------|------|
| official_kpi_6 | 공식 KPI 공급 |
| total_summary | 전사 KPI 요약 |
| total_trend | 전사 시계열 |
| branch_summary | 지점 요약 |
| branch_member_summary | 지점 담당자 목록 |
| member_performance | 개인 KPI |
| product_analysis | 품목 분석 |
| activity_analysis | 활동 분석 |
| data_health | 데이터 정합 |
| missing_data | 결측 데이터 |
| executive_insight | 운영 인사이트 |
| template_runtime_manifest | chunk runtime 정보 |

이 단계에서는 구조만 정의하고 **기존 template_payload는 유지**했다.

---

# 4. Stage 2 – Block Resolver 도입

템플릿에서 block을 조회할 수 있도록 **resolver 계층**을 도입했다.

Resolver 함수
resolveBlock()
resolveSlot()
resolveBranchBlock()


역할

- block registry 기반 데이터 조회
- fallback 처리
- chunk lazy-load 대응

이 단계부터 템플릿은 점진적으로
db.xxx

직접 접근 대신
resolveBlock("block_id")

구조로 전환되기 시작했다.

---

# 5. Stage 3 – Renderer 점진 전환

Renderer 함수가 resolver를 경유하도록 변경했다.

대표 변경 영역

Group View

- KPI cards
- Trend chart
- Radar
- Tornado
- Correlation matrix

Individual View

- Branch selector
- Member performance

Product View

- Product selector
- Product scatter

이 단계에서는 **기존 fallback 로직을 유지하여 preview 안정성을 확보**했다.

---

# 6. Stage 4 – 안정화 및 관측 가능성 추가

Stage 4에서는 구조 안정화와 테스트 강화가 이루어졌다.

## Resolver Counter 추가

fallback 발생을 추적할 수 있도록 counter를 추가했다.

block_missing
slot_missing
chunk_pending
fallback_used

렌더 완료 후 콘솔 출력
Sandbox Block Resolver Report
blocks resolved
fallback used
pending chunk


## Chunk Cache 구조 추가

branch lazy-load 안정화를 위해 cache 계층을 추가했다.
branchCache = {
branch_key : payload
}

resolver는 cache → chunk → fallback 순으로 데이터 조회한다.

## Snapshot 테스트 추가

새로운 테스트
tests/test_sandbox_renderer_snapshot.py

검증 항목

- KPI card count
- chart data length
- product selector
- branch/member rendering

---

# 7. 현재 구조

최종 Sandbox 구조
raw data
↓
sandbox_engine
↓
sandbox_service
↓
block_payload
↓
block_resolver
↓
slot renderer
↓
HTML dashboard

추가 계층
fallback counter
snapshot test
chunk cache


---

# 8. 리팩토링 결과

핵심 개선

- 템플릿 결합도 감소
- 분석 결과를 block 단위로 소비 가능
- lazy-load 구조 유지
- fallback 기반 점진 전환
- renderer 테스트 가능 구조 확보

resolver coverage
약 88%

---

# 9. 남은 기술 부채

현재 구조는 **운영 가능한 상태**지만 일부 직접 접근이 남아 있다.

대표 위치
report_template.html:506
report_template.html:553
report_template.html:731
report_template.html:748


이 접근은 caching / 옵션 로직에서 사용되며 renderer 핵심 로직에는 영향이 없다.

---

# 10. 설계 의사결정

중요한 설계 선택

### template_payload 유지

기존 preview 안정성을 위해 payload 구조를 유지하고  
block_payload를 병행 도입했다.

### fallback 전략 유지

대규모 템플릿 전환 대신 점진 전환 전략을 사용했다.

### 계산 구조는 service 중심 유지

포트폴리오 단계에서 과도한 계산 분해보다  
운영 가능한 구조와 안정성을 우선했다.

---

# 11. 향후 확장 가능성

현재 구조는 다음 확장을 자연스럽게 지원한다.

- 차트 조립형 대시보드
- 보고서 자동 생성
- AI 인사이트 생성
- RADAR Decision Agent
- Agent 기반 분석 OS

---

# 결론

이번 리팩토링은 Sandbox 대시보드를

**"고정 템플릿 기반 분석 화면"**

에서

**"block payload + resolver 기반 분석 대시보드 구조"**

로 전환한 작업이다.

기존 preview 안정성을 유지하면서 구조적 확장을 가능하게 만든 것이 핵심 성과다.