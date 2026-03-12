# Template Library Guide

작성일: 2026-03-12

## 1. 목적

이 문서는 템플릿 파일을 어떻게 관리할지 정리한다.

## 2. 관리 단위

- `template_id`
- `template_version`
- `preview_type`
- `module_name`

## 3. 권장 분류

- CRM 요약 템플릿
- Sandbox 대시보드 템플릿
- Territory 지도 템플릿
- Prescription 검증 템플릿
- Total Valid 허브 템플릿

## 4. 변경 원칙

- 템플릿 구조가 바뀌면 계약 문서도 같이 바꾼다.
- 카드 순서만 바뀌어도 payload 영향 여부를 확인한다.
- 템플릿 추가는 가능하지만 플랫폼처럼 복잡하게 키우지 않는다.

## 5. 한 줄 원칙

`템플릿은 자산이지만, 제품 본체는 아니다.`

