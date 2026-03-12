# HTML Output Utility Docs

이 폴더는 `HTML Builder`를 독립 제품이 아니라  
`템플릿 기반 출력 자동화 유틸`로 다시 정리한 문서 묶음입니다.

핵심 생각은 간단합니다.

- Builder는 계산 모듈이 아닙니다.
- Builder는 독립 Result Asset을 만들지 않습니다.
- Builder는 템플릿 계약에 맞춘 payload를 주입해 HTML을 만듭니다.
- 핵심 가치는 `결과 전달 시간 단축`입니다.

## 이 모듈의 실제 역할

- 대시보드/지도/검증 미리보기를 빨리 만든다
- 반복 보고서 형식을 표준화한다
- 사람이 다시 꾸미는 시간을 줄인다

## 이 모듈의 실제 한계

- 독립 서비스로 크게 키울 가치가 낮다
- 계산 모듈처럼 스스로 의미를 만들지 않는다
- 템플릿 계약이 없으면 범용 렌더러처럼 움직이기 어렵다

## 문서 구성

- `01_REBUILD_PRD.md`: 역할 재정의 PRD
- `02_ADR_GUIDE_AND_LOG.md`: 핵심 결정 로그
- `03_DOMAIN_GLOSSARY.md`: 용어집
- `04_TEMPLATE_CONTRACT.md`: 템플릿 계약
- `05_DATA_MODEL.md`: 렌더 데이터 모델
- `06_BOUNDARY_POLICY.md`: 경계 문서
- `07_TEMPLATE_OUTPUT_POLICY.md`: 출력 원칙
- `08_OPERATIONS_RUNBOOK.md`: 운영 절차
- `09_TEMPLATE_LIBRARY_GUIDE.md`: 템플릿 관리 가이드
- `10_TEST_STRATEGY.md`: 테스트 전략
- `14_BACKLOG_ROADMAP.md`: 로드맵
- `15_REBUILD_BASELINE_AND_IMPROVEMENTS.md`: 재평가 문서

## 추천 읽기 순서

1. `01_REBUILD_PRD.md`
2. `15_REBUILD_BASELINE_AND_IMPROVEMENTS.md`
3. `04_TEMPLATE_CONTRACT.md`
4. `06_BOUNDARY_POLICY.md`
5. `07_TEMPLATE_OUTPUT_POLICY.md`
6. `08_OPERATIONS_RUNBOOK.md`

## 한 줄 흐름

```text
Result Asset -> OPS -> Template Contract -> Template Injection -> HTML
```

## 한 줄 결론

`HTML Builder는 결과를 계산하는 모듈이 아니라, 결과를 빠르게 보여주는 템플릿 기반 출력 유틸이다.`
