# 08 Quality Checklist

## 목적
Sandbox 품질 검증을 실험 단계와 OPS 전달 단계로 나눠 운영한다.

## 실행 전
- [ ] 시나리오 config 존재
- [ ] 입력 자산 파일 존재
- [ ] 필수 컬럼/필수 메타 확인
- [ ] 승인 대상인지 draft인지 상태 확인

## 실행 중
- [ ] 필수 키 null 비율 임계치 이내
- [ ] 조인키 중복 없음
- [ ] 조인 후 행 수 이상치 없음
- [ ] 지표 결측률 임계치 이내
- [ ] orphan record 비율 임계치 이내

## 실행 후
- [ ] `sandbox_result_asset.json` 생성 확인
- [ ] `sandbox_builder_payload.json` 생성 확인
- [ ] 시나리오 비교 가능 상태 확인
- [ ] 승인 전 결과와 승인 완료 결과 분리 확인

## handoff 전
- [ ] `approval_status=approved`
- [ ] `approved_version` 존재
- [ ] `approved_by`, `approved_at` 존재
- [ ] `sandbox_ops_handoff.json` 생성 확인
