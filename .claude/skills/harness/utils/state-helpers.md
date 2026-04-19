# State Helpers

## 개요

태스크와 페이즈 상태를 JSON 파일로 영구 추적한다. `run_phases.py`를 통해 관리하거나 직접 파일을 수정할 수 있다.

## 파일 위치

- `.harness/phases.json` — 페이즈 정의 및 상태
- `.harness/tasks.json` — 태스크 정의, 의존성, 상태

## phases.json 형식

```json
{
  "project": "{프로젝트 이름}",
  "created": "{YYYY-MM-DD}",
  "harness_run_id": "{HARNESS_RUN_ID}",
  "phases": [
    {
      "id": "phase-1",
      "name": "{페이즈 이름}",
      "description": "{설명}",
      "status": "pending | in_progress | completed",
      "tasks": ["task-1", "task-2"]
    }
  ]
}
```

## tasks.json 형식

```json
{
  "tasks": [
    {
      "id": "task-1",
      "wave": 1,
      "phase": "phase-1",
      "title": "{태스크 이름}",
      "description": "{설명}",
      "files": {
        "create": ["{생성할 파일 경로}"],
        "modify": ["{수정할 파일 경로}"]
      },
      "dependencies": [],
      "acceptance_criteria": ["{완료 기준}"],
      "status": "pending | in_progress | completed | failed"
    }
  ]
}
```

## 상태 업데이트 절차

### Phase 3 Plan 완료 후
`phases.json`과 `tasks.json`을 생성하거나 업데이트한다:
1. plan.md의 태스크 목록을 기반으로 tasks.json 작성
2. 페이즈 구조를 phases.json에 반영

### Phase 4 Generate 태스크 시작 시
```json
{"id": "task-N", "status": "in_progress"}
```

### 태스크 완료 시
```json
{"id": "task-N", "status": "completed"}
```

### 페이즈 완료 시
해당 페이즈의 모든 태스크가 completed이면 phase status를 completed로 업데이트한다.

## run_phases.py 명령어

프로젝트 루트에서 실행:

```bash
python .harness/run_phases.py status          # 전체 진행 상황 시각화
python .harness/run_phases.py tasks           # 전체 태스크 목록
python .harness/run_phases.py tasks phase-1   # 특정 페이즈 태스크만
python .harness/run_phases.py complete task-1 # 태스크 완료 처리
python .harness/run_phases.py validate        # 아티팩트 일관성 검증
```
