# Territory Payload Schema

## 목적
Territory 독립 실행 결과를 사람용 미리보기와 OPS handoff용 공식 산출물로 나눠서 고정한다.

## territory_result_asset 요약 스키마
```json
{
  "scenario_id": "string",
  "scenario_name": "string",
  "approval_status": "draft|approved|rejected",
  "territory_summary": {},
  "coverage_summary": {},
  "optimization_summary": {},
  "handoff_quality_summary": {}
}
```

## territory_builder_payload 요약 스키마
```json
{
  "overview": {},
  "filters": {},
  "rep_index": {},
  "rep_payloads": {},
  "zone_summary": []
}
```

## territory_map_preview 데이터 스키마
### markers
```json
{
  "hospital_id": "string",
  "hospital_name": "string",
  "territory_id": "string",
  "rep_id": "string",
  "month": "YYYY-MM",
  "lat": 0.0,
  "lon": 0.0,
  "sales": 0.0,
  "visits": 0.0
}
```

### routes
```json
{
  "scenario_id": "string",
  "rep_id": "string",
  "month": "YYYY-MM",
  "points": [],
  "coverage_score": 0.0,
  "total_km": 0.0
}
```

## territory_ops_handoff 스키마
```json
{
  "company_key": "string",
  "scenario_id": "string",
  "approved_version": "string",
  "approved_by": "string",
  "approved_at": "ISO datetime",
  "quality_status": "PASS|WARN|FAIL",
  "handoff_ready": true,
  "source_files": {},
  "artifacts": {}
}
```

## 검증 규칙
- 승인 전 결과와 승인 완료 결과를 같은 파일로 덮어쓰지 않는다.
- OPS handoff에는 `approval_status=approved`만 허용한다.
- 지도용 payload는 미리보기용이며, 공식 판단 기준은 `territory_result_asset`이다.
