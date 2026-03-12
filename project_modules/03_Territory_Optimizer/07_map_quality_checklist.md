# Territory Independent Build Quality Checklist

## 목적
Territory 독립 실행 시 품질 점검을 실험 단계와 승인 단계로 나눠 운영한다.

## 실행 전
- [ ] 시나리오 YAML 존재
- [ ] `sandbox_result_asset` 준비 완료
- [ ] `territory_reference_master` 준비 완료
- [ ] route activity 또는 동등 입력 준비 완료
- [ ] 승인 대상인지 실험 대상인지 상태 구분 완료

## 실행 중
- [ ] 동일 병원 중복 배정 없음
- [ ] 권역 미배정 병원 비율 임계치 이내
- [ ] 담당자 과부하 임계치 확인
- [ ] 커버리지 공백 병원 비율 확인
- [ ] 잠금 병원/예외 병원 위반 없음

## 실행 후
- [ ] `territory_result_asset.json` 생성 확인
- [ ] `territory_builder_payload.json` 생성 확인
- [ ] 시나리오 비교 결과 확인
- [ ] 승인 메타 입력 전에는 OPS handoff 금지 확인
- [ ] 승인 완료 시 `territory_ops_handoff.json` 생성 확인

## 승인 전 최종 체크
- [ ] 선택한 시나리오가 `approved` 상태인지 확인
- [ ] 품질 상태가 `PASS` 또는 허용 가능한 `WARN`인지 확인
- [ ] 이전 승인 버전과 차이점이 기록됐는지 확인
- [ ] OPS로 넘길 파일 3종이 모두 생성됐는지 확인
