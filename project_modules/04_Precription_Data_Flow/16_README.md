# Prescription Data Flow Independent Build Docs

이 폴더는 Prescription Data Flow를 `독립 실행형 추적/검증/정산 파이프라인`으로 다시 정리한 문서 묶음입니다.

핵심 생각은 간단합니다.

- Prescription은 OPS 내부 화면이 아닙니다.
- Prescription은 자기 입력을 받아 자기 결과를 만드는 독립 모듈입니다.
- 승인된 결과 패키지만 나중에 OPS에 넘깁니다.

## 이 모듈이 하는 일
- 도매 -> 약국 -> 병원/담당자 흐름을 추적합니다.
- 추적 결과를 검증합니다.
- 분기 기준 쉐어 정산을 적용합니다.
- 월/분기/연 KPI를 발행합니다.
- 승인 가능한 결과 패키지로 export 합니다.

## 이 모듈이 하지 않는 일
- OPS 대신 중앙 허브 역할을 하지 않습니다.
- Builder 대신 화면을 최종 산출물로 삼지 않습니다.
- 업로드 화면이 없어도 핵심 파이프라인은 돌아가야 합니다.

## 문서 구성
- `01_business_rules.md`: 고정 비즈니스 규칙
- `02_data_dictionary.md`: 입력/출력/패키지 데이터 사전
- `03_data_model_erd.md`: 핵심 엔터티 관계
- `04_validation_qa_plan.md`: 품질/검증 기준
- `05_synthetic_data_spec.md`: 합성 데이터 설계
- `06_kpi_output_spec.md`: KPI와 공식 결과 산출물 규격
- `07_source_extraction_sop.md`: 원천 추출 표준
- `08_rebuild_requirements.md`: 독립빌드 요구사항
- `09_source_column_selection.md`: 원천 컬럼 선택 기준
- `10_rep_branch_generation_plan.md`: 담당자/지점 생성 기준
- `11_phase_gate_report.md`: 단계 게이트 템플릿
- `12_PLAN.md`: 독립빌드 전환 계획
- `13_PRD.md`: 제품 요구사항
- `14_Runbook.md`: 독립 실행 runbook
- `15_TODO.md`: 작업 체크리스트
- `17_ops_handoff_contract.md`: OPS 전달 규격
- `18_boundary_policy.md`: Prescription / OPS / Builder 경계

## 추천 읽기 순서
1. `13_PRD.md`
2. `12_PLAN.md`
3. `14_Runbook.md`
4. `06_kpi_output_spec.md`
5. `17_ops_handoff_contract.md`
6. `18_boundary_policy.md`
7. `02_data_dictionary.md` + `04_validation_qa_plan.md`

## 한 줄 실행 흐름
`approved source snapshot -> merge -> mastering -> tracking validation -> share settlement -> KPI publish -> validation/trace -> approval package -> OPS handoff`

## 필수 원칙
- 핵심 실행은 CLI 또는 배치 기준으로 먼저 성립해야 합니다.
- 로컬 화면은 있어도 되지만 없어도 파이프라인은 완결돼야 합니다.
- 승인 전 상세 테이블과 승인 후 공식 패키지를 분리합니다.
- OPS는 승인된 결과만 읽습니다.
