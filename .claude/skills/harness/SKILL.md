---
name: harness
description: 7페이즈 구현 워크플로우. 새 기능 구현, 버그 수정, 리팩토링 등 코드 변경 작업 전반에 사용. /harness로 직접 호출한다.
disable-model-invocation: true
argument-hint: "[구현할 내용]"
allowed-tools: Read Grep Glob Bash Write Edit
---

# Harness Skill

범용 7페이즈 구현 워크플로우 스킬. `/harness` 커맨드로 호출한다.

## 트리거

이 스킬은 `/harness` 슬래시 커맨드로만 호출된다.

## 시작 절차

1. **초기화 확인** — `.claude/.harness/hooks/.registered` 파일이 없으면 초기화를 수행한다:

```bash
# 디렉토리 생성
mkdir -p ".claude/.harness/hooks"
mkdir -p ".claude/.harness/artifacts"

# post-edit.sh 복사
cp "${CLAUDE_SKILL_DIR}/hooks/post-edit.sh" ".claude/.harness/hooks/post-edit.sh"
chmod +x ".claude/.harness/hooks/post-edit.sh"

# 등록 완료 플래그
touch ".claude/.harness/hooks/.registered"
```

   초기화 후 사용자에게 안내한다:
   > "`.claude/.harness/`를 초기화했습니다. `.claude/settings.json`에 훅을 등록해야 합니다. `${CLAUDE_SKILL_DIR}/utils/hooks-helpers.md`를 참조하세요."
   
   `.claude/settings.json`에 훅이 이미 등록되어 있으면 (`".claude/.harness/hooks/post-edit.sh"` 문자열 포함 여부로 확인) 안내를 생략한다.

2. **아티팩트 디렉토리 생성** (`${CLAUDE_SKILL_DIR}/utils/artifact-helpers.md` 참조):

```bash
HARNESS_RUN_ID=$(date +%Y-%m-%d-%H%M%S)
HARNESS_DIR=".claude/.harness/artifacts/$HARNESS_RUN_ID"
mkdir -p "$HARNESS_DIR"
```

3. 사용자에게 시작을 알린다:
   > "Harness 스킬을 시작합니다. Run ID: {HARNESS_RUN_ID}"

4. `$ARGUMENTS`가 있으면 Phase 1 Clarify의 초기 입력으로 전달한다. Phase 1에서 반드시 상세한 clarify를 수행하며, `$ARGUMENTS`는 출발점일 뿐 — 요구사항을 충분히 파악하기 전에 다음 페이즈로 넘어가지 않는다.

5. 아래 순서로 페이즈를 실행한다.

## 페이즈 실행 순서

```
Phase 1: Clarify        → phases/01-clarify.md
Phase 2: Context Gather → phases/02-context-gather.md
Phase 3: Plan           → phases/03-plan.md        [승인 게이트]
Phase 4: Generate       → phases/04-generate.md    [승인 게이트]
Phase 5: Test           → phases/05-test.md
Phase 6: Evaluate       → phases/06-evaluate.md
Phase 7: Document       → phases/07-document.md    → 커밋 후 종료
Phase 8: Retrospect     → phases/08-retrospect.md  [선택적, Phase 7 커밋 후 사용자 승인 시]
```

## 승인 게이트

- **Plan 완료 후:** 사용자 승인 없이 Generate로 진행하지 않는다
- **Generate 완료 후:** 사용자 승인 없이 Test로 진행하지 않는다

## 피드백 루프

- Test 실패 → Generate 재실행
- Evaluate 미달 → 해당 페이즈 재실행

## 유틸리티

- 아티팩트 저장: `${CLAUDE_SKILL_DIR}/utils/artifact-helpers.md`
- 상태 추적 (tasks.json/phases.json): `${CLAUDE_SKILL_DIR}/utils/state-helpers.md`
- 커밋 규칙: `${CLAUDE_SKILL_DIR}/utils/git-helpers.md`
- CLI 상태 관리: `${CLAUDE_SKILL_DIR}/run_phases.py` (`.claude/.harness/`에서 직접 실행)
