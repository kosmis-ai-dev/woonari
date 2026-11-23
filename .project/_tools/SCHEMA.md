# .project 데이터 구조

프로젝트의 기획·워크플로·기능 명세·수정 요청을 저장하는 폴더입니다.
**AI는 작업할 때마다 이 파일들을 갱신하고, 대시보드는 이 파일들을 읽기만 합니다.**
파일 하나 = 항목 하나라서, 서로 다른 기능을 동시에 수정해도 git 충돌이 거의 나지 않습니다.

```
.project/
├─ project.json          프로젝트 정보 + 단계(Stage) 목록
├─ plan.md               대화로 확정한 기획서 (사람이 읽는 문서)
├─ tasks/T-001.json      작업 1개 = 파일 1개
├─ features/F01.json     기능 1개 = 파일 1개 (= 기능 명세서)
├─ changes/CR-001.json   수정 요청 1개 = 파일 1개
└─ _tools/               대시보드·검사 도구 (수정 금지)
```

## 공통 규칙
- 날짜는 `YYYY-MM-DD` (Asia/Seoul 기준).
- 파일을 고칠 때마다 `updatedAt`을 오늘 날짜로 바꾸고 `history` 맨 **뒤**에 한 줄 추가한다.
- ID는 한 번 정하면 바꾸지 않는다. 삭제 대신 상태를 `dropped`로 바꾼다.
- 서로를 가리키는 ID는 **양쪽 모두** 기록한다. (작업 ↔ 기능, 수정요청 ↔ 작업/기능)
- 갱신 후 항상 `node .project/_tools/project-dashboard.mjs check`를 실행해 오류가 없게 한다.

`history` 항목 형식 (모든 파일 공통):
```json
{ "date": "2026-10-30", "by": "ai", "change": "CR-001", "text": "무엇이 바뀌었는지 한 줄" }
```
`change`는 수정 요청으로 인한 변경일 때만 넣는다. `by`는 `ai` 또는 사람 이름.

---

## project.json
```json
{
  "name": "캠페인 문자 발송 관리",
  "summary": "한 줄 설명",
  "stack": "Next.js 14 / Spring Boot 3 / MySQL 8",
  "commands": { "test": "npm test", "testOne": "npm test -- <file>", "build": "npm run build" },
  "humanReview": false,
  "stages": [
    { "id": "S1", "name": "기반 구축", "goal": "DB, 인증, 공통 레이아웃" },
    { "id": "S2", "name": "발송 기능", "goal": "대상 선택부터 발송까지" }
  ],
  "updatedAt": "2026-10-30",
  "history": []
}
```
단계 순서 = 배열 순서. 단계를 추가·변경하면 `history`에 기록한다.
`humanReview: true`이면 AI는 작업을 `done`이 아닌 `review`로 두고, 사람이 승인하면 `done`으로 바꾼다.

## tasks/T-001.json
```json
{
  "id": "T-001",
  "title": "캠페인 테이블 및 마이그레이션",
  "stage": "S1",
  "status": "todo",
  "features": ["F01"],
  "dependsOn": [],
  "changes": [],
  "description": "무엇을 만드는지 2~4줄",
  "acceptance": ["완료 조건 1", "완료 조건 2"],
  "tests": ["tests/campaign/schema.test.ts"],
  "commits": [],
  "createdAt": "2026-10-30",
  "updatedAt": "2026-10-30",
  "history": []
}
```
`commits`는 선택 항목이다 (사람이 수동으로 적을 때만). 보통은 `git log --grep "T-001"`로 찾는다.

`status` 값:
| 값 | 의미 |
|---|---|
| `todo` | 대기 |
| `doing` | 진행 중 (한 번에 하나 권장) |
| `review` | 구현·테스트 완료, 사람 리뷰 대기 |
| `done` | 완료 |
| `rework` | 완료됐지만 수정 요청으로 다시 작업 필요 |
| `verify` | 의존 기능이 바뀌어 재검증(테스트만 다시) 필요 |
| `blocked` | 진행 불가 (사유를 history에) |
| `dropped` | 취소 |

## features/F01.json  (기능 명세서)
```json
{
  "id": "F01",
  "name": "캠페인 관리",
  "status": "planned",
  "summary": "한 줄 설명",
  "dependsOn": [],
  "code": ["src/campaign/"],
  "tasks": ["T-001", "T-004"],
  "changes": [],
  "spec": "## 개요\n...\n## 입력/출력\n- ...\n## 규칙\n- ...",
  "createdAt": "2026-10-30",
  "updatedAt": "2026-10-30",
  "history": []
}
```
- `status`: `planned`(기획만) / `building`(구현 중) / `done`(구현 완료) / `changing`(수정 반영 중)
- `dependsOn`: 이 기능이 **사용하는** 기능. 이 기능을 사용하는 쪽(피의존)은 도구가 자동 계산한다.
- `spec`: Markdown. **항상 현재 상태**를 담는다. 과거 내용은 `history`와 git 이력으로 본다.
  구현하면서 실제로 정해진 내용(API 경로, 필드, 규칙, 에러 처리)을 계속 채운다.

## changes/CR-001.json  (수정 요청)
```json
{
  "id": "CR-001",
  "title": "예약 발송 기능 추가",
  "request": "요청 원문 그대로",
  "summary": "AI가 정리한 수정 내용 2~4줄",
  "requestedBy": "운영팀",
  "status": "received",
  "impact": {
    "features": ["F03"],
    "verifyFeatures": ["F04"],
    "tasksAdded": ["T-012"],
    "tasksReworked": ["T-008"],
    "tasksUpdated": ["T-010"],
    "tasksVerify": ["T-011"],
    "planChanged": true
  },
  "createdAt": "2026-10-30",
  "updatedAt": "2026-10-30",
  "history": []
}
```
`tasksAdded` 새로 만든 작업 / `tasksReworked` 완료됐던 작업을 다시 여는 것 / `tasksUpdated` 아직 대기 중인 작업의 내용을 바꾼 것 / `tasksVerify` 코드는 그대로지만 재검증이 필요해진 작업.

`status`: `received`(접수) / `planned`(영향 분석·작업 반영 완료) / `in-progress` / `done` / `rejected`

## 커밋 메시지
```
[T-012][F03] 예약 발송 시간 파라미터 추가 (CR-001)
```
코드와 `.project/` 변경은 **같은 커밋**에 넣는다. 그래야 git 이력에서 코드와 명세가 함께 움직인다.
