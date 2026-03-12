# Territory Independent Build Runbook And Release

## 목적
Territory를 독립 실행형으로 운영할 때의 표준 절차와 승인 후 OPS 반영 절차를 정의한다.

## 일상 운영 절차
1. 기준 입력 확인
2. 시나리오 생성 또는 복제
3. 독립 실행
4. 시나리오 비교
5. 승인안 선택
6. handoff 패키지 생성
7. OPS 전달

## 승인 절차
1. 분석 담당자 초안 생성
2. 검토자가 품질 게이트 확인
3. 승인자가 `approved_version` 부여
4. 승인 패키지 export

## 장애 대응
1. 실패 stage 확인
2. 원인 분류
   - 입력
   - 시나리오 제약조건
   - 권역 기준표
   - payload 생성
   - handoff export
3. 수정 후 동일 시나리오 재실행
4. 변경 이력 기록

## 변경관리 템플릿
```text
[Change ID]
- Date:
- Author:
- Scenario ID:
- Type: scenario | reference | payload | handoff
- Summary:
- Validation Result:
- Approval Status:
- Rollback Plan:
```

## 롤백 원칙
- OPS에 반영된 승인 버전은 덮어쓰지 않는다.
- 새 버전은 이전 승인 버전과 병행 보관한다.
- 실험 결과는 OPS 공식 결과와 분리 보관한다.
