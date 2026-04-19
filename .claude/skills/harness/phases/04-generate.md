# Phase 4: Generate

## 권한 선언

| 허용 | 금지 |
|------|------|
| 모든 파일 읽기 | plan.md 파일 목록 외 프로젝트 파일 수정 |
| plan.md에 명시된 파일만 수정/생성 | 그 외 임의 파일 삭제 |
| `$HARNESS_DIR/generate.md` 쓰기 | 테스트 실행 |
| Bash 실행 (빌드/린트 명령) | git 명령 (Document 페이즈 전용) |

이 페이즈에서 위 금지 항목이 필요하다고 판단되면 즉시 중단하고 사용자에게 알린다.

## PRE-EVENT

### 사전 조건 확인
- `$HARNESS_DIR/plan.md` 존재 확인 → 없으면 Phase 3 재실행 요청
- `.harness/tasks.json` 존재 및 파싱 가능 확인 → 없으면 Phase 3 재실행 요청

### 목표 리마인더
`$HARNESS_DIR/clarify.md`에서 다음을 추출하여 구현 시작 전에 확인한다:

> **이 작업의 목표:** {요청 요약 1줄}  
> **성공 기준:** {성공 기준 항목들}  
> **핵심 제약:** {제약 조건 항목들}

이 목표 범위를 벗어나는 구현은 수행하지 않는다.

### 코드 컨벤션 추출
`$HARNESS_DIR/context.md`에서 코드 컨벤션 핵심 3줄을 추출한다.  
각 병렬 에이전트 프롬프트에 이 요약을 포함하여 컨벤션 일관성을 유지한다.

### 훅 등록 안내 (1회)
`.claude/.harness/hooks/.registered` 파일이 없으면 사용자에게 안내한다:

> "`.claude/.harness/hooks/post-edit.sh`를 사용하면 파일 수정 시 자동으로 포맷팅됩니다.  
> `utils/hooks-helpers.md`를 참조하여 `.claude/settings.json`에 훅을 등록할까요? (y/n)"

등록 완료 후 `.claude/.harness/hooks/.registered` 파일을 생성한다.

## 목적

Plan에 따라 코드를 구현한다.

## 절차

1. `$HARNESS_DIR/plan.md`를 읽는다
2. `.harness/tasks.json`에서 태스크를 로드하고 Wave를 분류한다:

### Wave 분류 알고리즘

```
1. tasks.json에서 모든 태스크 로드
2. 진입차수(in-degree) 계산: in_degree[task] = len(task.dependencies)
3. Wave 1: in_degree = 0인 태스크 → 병렬 실행 대상
4. Wave 1 완료 후: 완료된 태스크를 의존성으로 가진 태스크의 in_degree -= 1
5. Wave 2: 새로 in_degree = 0이 된 태스크 → 병렬 실행 대상
6. 반복 → 모든 태스크 완료까지
```

tasks.json의 `wave` 필드 예시:
```json
{
  "tasks": [
    {"id": "task-1", "wave": 1, "dependencies": [], "files": {"modify": [...]}},
    {"id": "task-2", "wave": 1, "dependencies": [], "files": {"create": [...]}},
    {"id": "task-3", "wave": 2, "dependencies": ["task-1"], "files": {"modify": [...]}}
  ]
}
```

### 병렬 실행 금지 조건

다음 중 하나라도 해당하면 해당 태스크는 순차 실행한다:
- 두 태스크가 동일 파일을 수정하는 경우
- 한 태스크의 출력이 다른 태스크의 입력인 경우
- 에러가 서로 연관된 경우 (한 쪽 실패가 다른 쪽에 영향)
- 현재 무엇이 잘못됐는지 탐색 중인 경우 (exploratory 디버깅)

### Wave 단위 병렬 실행

각 Wave 내의 병렬 가능 태스크는 Agent 도구를 한 메시지에 여러 개 동시 호출하여 실행한다.  
각 에이전트 프롬프트는 `${CLAUDE_SKILL_DIR}/implementer-prompt.md`의 템플릿을 사용한다.

아래 변수를 채워서 Agent 도구에 전달한다:
- `{TASK_ID}`, `{TASK_NAME}` — tasks.json에서 추출
- `{TASK_DESCRIPTION}` — plan.md의 해당 태스크 전문 (서브에이전트에게 파일 읽기 금지 — 전문 붙여넣기)
- `{WAVE_NUMBER}` — 현재 Wave 번호
- `{FILE_SCOPE}` — tasks.json의 해당 태스크 파일 목록
- `{CODE_CONVENTIONS}` — context.md 코드 컨벤션 핵심 요약
- `{SUCCESS_CRITERIA}` — clarify.md의 성공 기준 항목들

**Wave 완료 후 검증 및 리뷰:**

### Step A: 구조 검증 (기존 유지)
1. **파일 중복 수정 확인:** 두 에이전트가 같은 파일을 수정했는지 확인. 중복 발견 시 수동 병합.
2. **누락 파일 확인:** plan.md의 파일 목록과 실제 변경 파일 목록을 대조. 누락 시 해당 태스크 재실행.
3. **인터페이스 일관성 확인:** 공유 타입, 함수 시그니처, import 경로 일치 여부 확인.

### Step B: Implementer 상태 처리

Implementer가 보고한 Status에 따라 처리한다:

- **DONE** → Step C(Spec 리뷰)로 진행
- **DONE_WITH_CONCERNS** → 우려 사항을 검토한다. 정확성/범위 문제면 Step C 전에 처리. 관찰 사항(예: "파일이 커지고 있음")이면 메모하고 Step C로 진행
- **NEEDS_CONTEXT** → 누락된 정보를 제공하고 Implementer 재디스패치 (`implementer-prompt.md` 재사용)
- **BLOCKED** → 원인을 평가한다:
  1. 컨텍스트 문제 → 추가 컨텍스트 제공 후 재디스패치
  2. 태스크가 너무 큼 → 더 작은 단위로 분할 후 재디스패치
  3. 플랜 자체가 잘못됨 → 사용자에게 에스컬레이션

BLOCKED 에스컬레이션을 변경 없이 같은 모델로 재시도하지 않는다. 막혔다면 무언가가 바뀌어야 한다.

### Step C: Spec 준수 리뷰

`${CLAUDE_SKILL_DIR}/spec-reviewer-prompt.md`의 템플릿으로 Spec 리뷰어 서브에이전트를 디스패치한다.

아래 변수를 채워서 전달한다:
- `{TASK_ID}`, `{TASK_NAME}` — 해당 태스크 식별자
- `{TASK_DESCRIPTION}` — plan.md의 태스크 요건 전문
- `{SUCCESS_CRITERIA}` — clarify.md의 성공 기준
- `{EXPECTED_FILES}` — plan.md의 해당 태스크 파일 목록
- `{IMPLEMENTER_REPORT}` — Implementer가 보고한 전체 내용

**결과 처리:**
- ✅ Spec 준수 → Step D(Quality 리뷰)로 진행
- ❌ 이슈 발견 → Implementer 재디스패치하여 수정 → Spec 리뷰 재실행 (✅ 될 때까지 반복)

Spec 리뷰에서 이슈가 발견되면 "충분히 가까움"으로 넘어가지 않는다. 수정 후 재검토한다.

### Step D: 코드 품질 리뷰

**Spec 준수 리뷰가 ✅ 통과한 후에만 진행한다.**

`${CLAUDE_SKILL_DIR}/code-quality-reviewer-prompt.md`의 템플릿으로 Quality 리뷰어 서브에이전트를 디스패치한다.

아래 변수를 채워서 전달한다:
- `{TASK_ID}`, `{TASK_NAME}`, `{TASK_DESCRIPTION}` — 태스크 정보
- `{IMPLEMENTER_REPORT}` — Implementer 보고 내용
- `{BASE_SHA}` — 이 태스크 구현 시작 전 커밋 SHA (`git log --oneline`으로 확인)
- `{HEAD_SHA}` — 현재 커밋 SHA (`git rev-parse HEAD`로 확인)
- `{CODE_CONVENTIONS}` — context.md 컨벤션 요약

**결과 처리:**
- ✅ 승인 → 다음 Wave로 진행
- ❌ 이슈(Critical/Important) → Implementer 재디스패치하여 수정 → Quality 리뷰 재실행
- Minor 이슈 → 메모하고 진행 (블로커 아님)

## Skill Dispatch 테이블

태스크에서 수정/생성하는 파일 유형을 확인하고 아래 테이블에 따라 스킬을 조건부 호출한다.

| 파일 패턴 | 조건 | 호출 스킬 |
|-----------|------|-----------|
| `*.html`, `*.css`, `*.js`, `*.jsx`, `*.tsx` | UI 구현 포함 | `frontend-design` |
| `*.test.*`, `*.spec.*`, `*_test.*` | 테스트 파일 신규 생성 | `superpowers:test-driven-development` |
| `*.py` (Anthropic SDK import 포함) | LLM API 코드 | `claude-api` |
| `*.docx`, `*.pdf`, `*.pptx`, `*.xlsx` | 문서 파일 | 해당 `anthropic-skills` (docx/pdf/pptx/xlsx) |
| 그 외 | — | 직접 구현 |

**우선순위:** 여러 패턴이 동시에 해당하면 위 순서대로 첫 번째 매칭을 적용한다.

**스킬 미호출 조건:**
- 태스크가 단순 리팩토링/수정이고 신규 UI 설계가 없는 경우
- 스킬 호출이 현재 작업 범위를 벗어나는 경우

스킬 호출 여부를 판단하기 어려우면 사용자에게 확인한다.

## 아티팩트 저장

`$HARNESS_DIR/generate.md`에 아래 형식으로 저장한다:

```markdown
---
phase: generate
status: in-review
timestamp: {현재 ISO 8601}
next: test
---

# Generate

## 변경된 파일 목록
- 생성: {파일 경로}
- 수정: {파일 경로}

## 태스크별 결과 요약
- Task 1: {결과 요약}
- Task 2: {결과 요약}
```

## POST-EVENT

### 구조 검증 (LLM 없이)
- `$HARNESS_DIR/generate.md`의 "변경된 파일 목록"과 `plan.md`의 파일 목록 대조
- 누락 파일이 있으면 해당 태스크 재실행
- 에이전트 간 동일 파일 중복 수정 여부 확인

### Handoff 생성
`$HARNESS_DIR/handoff-04to05.md`를 아래 내용으로 생성한다:

```markdown
# Handoff: Phase 4 → Phase 5

## 목표 (Goal)
{clarify.md의 요청 요약 1줄}
성공 기준: {성공 기준 목록}

## 이번 페이즈가 파악한 것 (Findings)
- 변경된 파일: {파일명 + 변경 내용 1줄}

## 다음 페이즈가 해야 할 것 (Next)
- 테스트해야 할 시나리오: {성공 기준 기반 시나리오 목록}

## 참고 파일 (References)
- `$HARNESS_DIR/generate.md` (변경 상세 내용 필요 시)
```

## 승인 게이트

구현 완료 후 사용자에게 결과를 보여주고 승인을 요청한다:

> "Phase 4 Generate가 완료되었습니다. 변경된 파일을 검토해주세요. 테스트를 진행할까요?"

사용자가 승인하면 `generate.md`의 frontmatter `status`를 `approved`로, `timestamp`를 현재 시각으로 갱신한 후 Phase 5로 진행한다.
