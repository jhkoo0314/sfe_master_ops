# AI Start Here

## 목적

이 폴더는 Sales Data OS의 공식 세계관, 실행 순서, 현재 범위를 Codex가 바로 작업에 사용할 수 있게 압축한 작업 레이어다.

이 폴더는 마스터 문서를 대체하지 않는다.
충돌 시 우선순위는 다음과 같다.

1. 마스터 문서
2. 루트 `AGENTS.md`
3. `ai/` 폴더
4. 구현 코드와 보조 문서

## 먼저 읽는 순서

1. `00_start_here.md`
2. `01_worldview.md`
3. `03_execution_rules.md`
4. `04_module_map.md`
5. `05_crm_rules.md`
6. `06_builder_and_outputs.md`
7. `02_repo_map.md`
8. `../architecture/12_part2_status_source_of_truth.md`
9. `07_current_phase.md`

## 가장 중요한 기준

시스템 전체 이름은 `Sales Data OS`다.
`OPS`는 시스템 전체가 아니라 `Validation / Orchestration Layer`다.

공식 흐름:

`raw -> adapter -> module/core engine -> Result Asset -> Validation Layer(OPS) -> Intelligence(RADAR) -> Builder`

Part2 우선순위/진행 상태 단일 기준:

`docs/architecture/12_part2_status_source_of_truth.md`

## 이 폴더에서 하지 않는 일

- Part 2를 먼저 반영하지 않는다.
- 세계관을 새로 정의하지 않는다.
- 저장소 실제 구조와 다른 이상적 구조를 만들지 않는다.
- Builder를 계산 엔진처럼 다루지 않는다.
- OPS를 시스템 전체 중심으로 설명하지 않는다.

## 작성 원칙

- 짧고 명확하게 쓴다.
- 역할과 순서를 먼저 쓴다.
- 현재 범위 밖 내용은 넣지 않는다.
- 코드 구조가 바뀌면 관련 문서도 같이 갱신한다.
