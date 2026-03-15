# Refactor Plan: Sales Data OS Alignment

작성일: 2026-03-16

## 변경 목표

- 시스템 전체 정의를 `Sales Data OS`로 정렬
- OPS를 `Validation / Orchestration Layer`로 재정의
- KPI single source 원칙을 문서/주석/UI까지 일관 반영
- 작동 중 파이프라인을 깨지 않고 점진 정렬

## 비목표

- 대규모 폴더 rename
- API 경로(`/ops/*`) 재설계
- working module 로직 재작성
- KPI 계산 위치 이동(엔진 외부로 확장)

## 영향 범위

- 문서: README/RUNBOOK/STRUCTURE + architecture 문서
- 주석/docstring: ops_core, builder, module service 일부
- UI 라벨: 콘솔/템플릿 표시 문구

## 리스크

- 용어 교체 중 운영자가 익숙한 표현과 충돌 가능
- 템플릿 문구 변경 시 화면 문맥 불일치 가능
- 파일명/경로 rename 시 import/API 깨질 가능성

## 롤백 포인트

- Phase 단위 커밋으로 역추적 가능하게 유지
- 본 작업은 로직 변경 없이 텍스트/문서 중심이므로 파일 단위 되돌리기 용이

## 테스트 항목

- `uv run pytest` 주요 회귀
- 콘솔 실행 확인
- 파이프라인 실행 (`scripts/validate_full_pipeline.py`) smoke check
- 템플릿 라벨 렌더링 확인

## 단계별 계획

## Phase 1: Documentation Alignment (안전, 우선 실행)

- `docs/architecture/current_state_audit.md` 작성
- `docs/architecture/sales_data_os_architecture.md` 작성
- `docs/architecture/refactor_plan_sales_data_os.md` 작성
- README/RUNBOOK/STRUCTURE/문서 허브 소개 문구 정렬

완료 기준:
- 시스템 설명이 Sales Data OS 기준으로 읽힘
- OPS는 Validation Layer로만 설명됨

## Phase 2: Comments & Docstrings Alignment

- `ops_core/*` 설명에서 OPS 중심 시스템 문구 제거
- `modules/builder/*`에 render-only 원칙 명시
- `modules/*/service.py` 문구를 책임 경계 중심으로 정렬

완료 기준:
- 계산/검증/표현 경계가 주석만 읽어도 구분됨

## Phase 3: UI & Label Adjustments

안전한 텍스트만 교체:
- `Sales Data OS Console`
- `Validation Layer (OPS)`
- `OPS Validation Result`

회피:
- path, key, API prefix, script filename 변경

완료 기준:
- 사용자에게 OPS가 전체 시스템으로 보이지 않음

## Phase 4: Optional Safe Module Restructuring (선택)

조건:
- 테스트 안정성 확보
- 운영 자동화 영향 분석 완료

검토 대상:
- alias 수준의 네이밍 보조
- 아키텍처 문서와 코드 디렉터리 설명 매핑 보강
- RADAR 입력 계약 스키마 초안 추가(구현은 별도)

## RADAR Readiness 체크

RADAR를 Intelligence Layer 위치로 고정하고 다음 입력 계약을 준비한다.

- KPI engine output
- validation-approved result asset
- sandbox summary metrics

금지 규칙:
- KPI 재계산 금지
- field task 자동 지시 금지
- 원인 확정 금지
