# Repository Map

## 목적

이 문서는 현재 저장소의 실제 구조와 주요 진입점을 빠르게 파악하기 위한 요약 지도다.
전체 상세 트리는 `STRUCTURE.md`를 우선 참고한다.

## 최상위 역할

- `adapters/`: 회사 raw를 공통 구조로 변환
- `modules/`: 모듈별 계산과 표준화
- `ops_core/`: Validation / Orchestration Layer 구현 패키지
- `result_assets/`: 모듈 간 교환 표준
- `ui/`: 운영 콘솔
- `templates/`: HTML 템플릿
- `scripts/`: 검증 및 실행 진입점
- `common/`: 회사 코드와 공통 설정
- `data/`: 원천/표준/검증 결과 저장
- `docs/`: 설명 문서

## 자주 확인할 위치

- `ui/ops_console.py`
- `ops_core/main.py`
- `common/company_profile.py`
- `scripts/validate_full_pipeline.py`
- 각 모듈의 builder payload 관련 파일

## 데이터 경로 원칙

모든 저장과 실행은 `company_key` 기준으로 움직인다.

- `data/company_source/{company_key}/`
- `data/ops_standard/{company_key}/`
- `data/ops_validation/{company_key}/`

회사명은 표시용이다.
경로와 실행 기준은 항상 `company_key`다.

## 결론

저장소는 adapter, module, validation/orchestration, builder, ui, data가 역할별로 분리된 구조이며, 실행과 산출물 저장은 `company_key` 기준으로 관리된다.
