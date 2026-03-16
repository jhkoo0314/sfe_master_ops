# Sales Data OS Runbook

작성일: 2026-03-16

이 문서는 Sales Data OS 관점의 운영 요약 런북이다.
상세 실행 절차와 파일 경로는 루트 `RUNBOOK.md`를 기준으로 사용한다.

## 시스템 정의

- 전체 시스템: `Sales Data OS`
- OPS: `Validation / Orchestration Layer`

## 핵심 흐름

`원천데이터 -> Adapter -> Module/Core Engine -> Result Asset -> Validation Layer (OPS) -> Builder`

## 책임 분리

- KPI 계산: `modules/kpi/*` (단일 소스)
- Validation/Orchestration: `ops_core/*`
- Builder: render-only (재계산 금지)

## 모듈 역할

- Sandbox: 분석/탐색
- Territory: 권역/커버리지 분석
- Prescription: 처방 흐름 검증
- RADAR: signal detection, issue prioritization, decision option templating

## 운영 원칙

- OPS는 검증/전달 판단만 담당
- Builder는 payload 소비/렌더링만 담당
- validation 승인 자산만 Intelligence/Builder로 전달
