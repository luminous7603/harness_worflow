# Artifact Helpers

## 아티팩트 디렉토리 생성

하네스 스킬 실행 시작 시, 아래 규칙으로 아티팩트 디렉토리를 생성한다.

타임스탬프 형식: `YYYY-MM-DD-HHMMSS`

```bash
HARNESS_RUN_ID=$(date +%Y-%m-%d-%H%M%S)
HARNESS_DIR=".claude/.harness/artifacts/$HARNESS_RUN_ID"
mkdir -p "$HARNESS_DIR"
```

이 변수(`HARNESS_RUN_ID`, `HARNESS_DIR`)는 세션 내 모든 페이즈에서 동일하게 사용된다.

## 아티팩트 파일 목록

| 페이즈 완료 후 | 파일명 |
|---|---|
| Phase 1 완료 후 | `$HARNESS_DIR/clarify.md` |
| Phase 1 완료 후 | `$HARNESS_DIR/handoff-01to02.md` |
| Phase 2 완료 후 | `$HARNESS_DIR/context.md` |
| Phase 2 완료 후 | `$HARNESS_DIR/handoff-02to03.md` |
| Phase 3 완료 후 | `$HARNESS_DIR/plan.md` |
| Phase 3 완료 후 | `$HARNESS_DIR/handoff-03to04.md` |
| Phase 4 완료 후 | `$HARNESS_DIR/generate.md` |
| Phase 4 완료 후 | `$HARNESS_DIR/handoff-04to05.md` |
| Phase 5 완료 후 | `$HARNESS_DIR/test.md` |
| Phase 5 완료 후 | `$HARNESS_DIR/handoff-05to06.md` |
| Phase 6 완료 후 | `$HARNESS_DIR/evaluate.md` |
| Phase 6 완료 후 | `$HARNESS_DIR/handoff-06to07.md` |
| Phase 7 완료 후 | `$HARNESS_DIR/document.md` |

## 아티팩트 저장 규칙

- 각 페이즈 완료 시 해당 파일과 handoff 파일을 모두 저장한다
- **다음 페이즈는 `handoff-{N}to{M}.md`를 먼저 읽는다. 상세 내용이 필요한 경우에만 References의 파일을 추가로 읽는다.**
- 덮어쓰기가 필요하면 해당 파일만 덮어쓴다

## Frontmatter 규칙

모든 아티팩트 파일은 최상단에 아래 frontmatter를 포함한다:

```yaml
---
phase: {phase-name}
status: draft | in-review | approved | failed
timestamp: {ISO 8601}
next: {next-phase-name}
---
```

- **draft**: 작성 중
- **in-review**: POST-EVENT 구조 검증 통과, 사용자 확인 대기 (승인 게이트 페이즈)
- **approved**: 사용자 승인 완료 또는 자동 통과
- **failed**: POST-EVENT 검증 실패

| 아티팩트 | phase 값 | next 값 |
|---------|---------|---------|
| clarify.md | clarify | context-gather |
| context.md | context-gather | plan |
| plan.md | plan | generate |
| generate.md | generate | test |
| test.md | test | evaluate |
| evaluate.md | evaluate | document |
| document.md | document | (없음) |

## Handoff 파일 구조

모든 `handoff-{N}to{M}.md` 파일은 다음 4개 섹션을 가진다:

```markdown
# Handoff: Phase {N} → Phase {M}

## 목표 (Goal)
{clarify.md의 요청 요약 1줄 + 성공 기준 목록}

## 이번 페이즈가 파악한 것 (Findings)
{이전 페이즈에서 발견한 핵심 사실만, 3~7줄}

## 다음 페이즈가 해야 할 것 (Next)
{다음 페이즈의 구체적 작업 목록}

## 참고 파일 (References)
{다음 페이즈에서 필요 시 직접 읽어야 할 파일 경로 목록}
```
