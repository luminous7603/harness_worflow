# Harness Skill

Claude Code용 범용 구현 워크플로우 스킬. 요구사항 명확화부터 코드 생성, 테스트, 문서화, 커밋까지 8개 페이즈를 체계적으로 실행한다.

## 원리

### 왜 Harness인가

LLM 기반 코드 생성의 가장 큰 문제는 **컨텍스트 드리프트**다. 작업 도중 초기 요구사항을 잊거나, 코드베이스 컨벤션을 무시하거나, 어디까지 했는지 놓치는 현상이 발생한다. Harness는 이를 구조로 해결한다.

핵심 원칙은 세 가지다:

1. **페이즈 격리** — 각 페이즈는 읽기/쓰기 권한을 명시적으로 선언하고, 허용되지 않은 작업을 수행해야 한다고 판단되면 즉시 중단하고 사용자에게 알린다. 한 페이즈가 다른 페이즈의 역할을 침범하지 않는다.

2. **아티팩트 기반 인수인계(Handoff)** — 페이즈 간 정보 전달은 마크다운 파일로만 이루어진다. 각 페이즈는 다음 페이즈를 위한 `handoff-NNtoNN.md`를 생성하며, 이 파일에는 목표, 발견한 사실, 다음 페이즈가 해야 할 일이 명시된다. LLM의 맥락 의존을 줄이고 재실행과 디버깅을 쉽게 한다.

3. **병렬 실행** — Phase 4(Generate)는 의존성이 없는 태스크를 Wave 단위로 분류하여 여러 서브에이전트를 동시에 디스패치한다. 각 서브에이전트는 메인 컨텍스트 창을 소모하지 않고 독립적으로 작동한다.

### 아키텍처

```
.claude/
├── settings.json          # 훅 설정 (초기화 후 사용자가 등록)
└── skills/harness/        # 스킬 본체
    ├── SKILL.md           # 스킬 진입점 및 실행 절차
    ├── memory.md          # 프로젝트별 반복 실패/성공 패턴 누적
    ├── run_phases.py      # Stop 훅에서 페이즈 상태 검증
    ├── implementer-prompt.md      # 구현 서브에이전트 프롬프트 템플릿
    ├── spec-reviewer-prompt.md    # Spec 준수 리뷰어 프롬프트 템플릿
    ├── code-quality-reviewer-prompt.md  # 코드 품질 리뷰어 프롬프트 템플릿
    ├── phases/
    │   ├── 01-clarify.md       # 요구사항 명확화
    │   ├── 02-context-gather.md # 코드베이스 탐색
    │   ├── 03-plan.md          # 실행 계획 수립
    │   ├── 04-generate.md      # 코드 생성 (Wave 병렬 실행)
    │   ├── 05-test.md          # 테스트
    │   ├── 06-evaluate.md      # 성공 기준 검증
    │   ├── 07-document.md      # 문서화 및 커밋
    │   └── 08-retrospect.md    # 회고 및 memory.md 업데이트
    ├── hooks/
    │   └── post-edit.sh        # 파일 수정 후 자동 실행 훅 스크립트
    └── utils/
        ├── artifact-helpers.md  # 아티팩트 저장 가이드
        ├── state-helpers.md     # tasks.json / phases.json 관리
        ├── git-helpers.md       # 커밋 규칙
        └── hooks-helpers.md     # 훅 등록 방법
```

런타임에는 `.claude/.harness/`가 생성되며, 여기에 실행 아티팩트와 훅이 배치된다. 이 디렉토리는 `.gitignore`에 포함되어 git에 올라가지 않는다.

---

## 페이즈 상세

### Phase 1: Clarify
요구사항을 명확히 한다. 구현 목적, 제약 조건, 성공 기준을 파악할 때까지 사용자와 대화한다. 요청이 너무 크면 서브태스크 분해를 제안하고, 접근법이 여러 갈래면 선택지를 제시한다. 결과는 `clarify.md`로 저장하고 다음 페이즈에 인계한다.

### Phase 2: Context Gather
코드베이스를 탐색한다. 서브에이전트를 별도로 디스패치하여 메인 컨텍스트 창을 보호한다. 프로젝트 구조, 코드 컨벤션, 관련 기존 파일을 파악하여 `context.md`로 저장한다. 반복 실행 시 `.claude/.harness/context.md` 캐시를 재사용하여 불필요한 탐색을 줄인다.

### Phase 3: Plan
Clarify와 Context Gather 결과를 바탕으로 태스크 목록을 작성한다. 각 태스크에 수정/생성 파일을 명시하고 의존성을 분석하여 Wave를 분류한다. 신규 파일이 5개를 초과하면 복잡도 경고를 표시하고 분할 여부를 확인한다. **사용자 승인 게이트**: 계획 검토 후 승인해야 다음 페이즈로 진행한다.

### Phase 4: Generate
계획에 따라 코드를 구현한다. Wave 단위로 독립 태스크를 병렬 서브에이전트에 위임하고, 각 Wave 완료 후 3단계 검증을 수행한다:
- **구조 검증** — 파일 누락, 중복 수정, 인터페이스 불일치 확인
- **Spec 리뷰** — 별도 서브에이전트가 요건 준수 여부 검토. 이슈 발견 시 수정 후 재검토
- **코드 품질 리뷰** — 별도 서브에이전트가 코드 품질 검토. Critical/Important 이슈는 수정 후 재검토

**사용자 승인 게이트**: 구현 결과 검토 후 승인해야 테스트로 진행한다.

### Phase 5: Test
구현된 코드를 테스트한다. UI 파일 변경이 있으면 Playwright 스모크 테스트를 실행한다. 로컬 서비스가 실행 중이면 통합테스트 확장을 제안한다. 테스트 실패 시 Phase 4로 피드백하여 재구현을 요청한다.

### Phase 6: Evaluate
Clarify에서 정의한 성공 기준 전체를 검증한다. 기준별 PASS/FAIL을 판정하고, 미달 항목은 원인에 따라 Phase 4 또는 Phase 5로 피드백한다. 전체 PASS 후 Phase 7로 진행한다.

### Phase 7: Document
변경된 기능에 맞게 README.md, CLAUDE.md 등을 업데이트한다. CLAUDE.md가 200줄을 초과하면 자동 가지치기를 수행한다. 문서 업데이트 완료 후 `git commit`으로 로컬 커밋한다. **Push는 하지 않는다** — 사용자가 직접 확인 후 push한다.

### Phase 8: Retrospect (선택)
Phase 7 커밋 후 사용자 승인 시 실행한다. 이번 실행의 반복 실패 패턴, 효과적이었던 패턴, 프로젝트 고유 주의사항을 분석하여 `memory.md`에 누적한다. 다음 실행에서 Phase 2와 Phase 3이 이 기억을 참고하여 같은 실수를 반복하지 않도록 한다.

---

## 설치

### 1. 스킬 복사

이 저장소를 Claude Code의 스킬 디렉토리에 복사한다:

```bash
# 전역 설치 (모든 프로젝트에서 사용)
git clone https://github.com/luminous7603/harness_worflow.git ~/.claude/skills/harness

# 또는 프로젝트 로컬 설치
git clone https://github.com/luminous7603/harness_worflow.git /your/project/.claude/skills/harness
```

### 2. 첫 실행 및 훅 초기화

Claude Code에서 `/harness`를 실행하면 자동으로 초기화된다:

```
/harness
```

초기화 시 `.claude/.harness/hooks/post-edit.sh`가 생성된다.

훅을 사용하려면 `.claude/settings.json`에 아래 내용을 추가한다 (`utils/hooks-helpers.md` 참조):

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/.harness/hooks/post-edit.sh \"$CLAUDE_TOOL_INPUT_FILE_PATH\""
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [{
          "type": "command",
          "command": "python \"${CLAUDE_SKILL_DIR}/run_phases.py\" --validate-current 2>/dev/null || true"
        }]
      }
    ]
  }
}
```

---

## 사용법

### 기본 호출

```
/harness [구현할 내용]
```

예시:

```
/harness 사용자 로그인 API에 rate limiting 추가
/harness 검색 결과 페이지 페이지네이션 구현
/harness Qdrant 유사도 검색 정확도 개선
```

### 실행 흐름

```
사용자: /harness [요청]
          ↓
Phase 1: Clarify       — 요구사항 확정, 성공 기준 정의
          ↓
Phase 2: Context Gather — 코드베이스 탐색 (서브에이전트)
          ↓
Phase 3: Plan          — 태스크 목록, Wave 분류
          ↓ [승인 게이트]
Phase 4: Generate      — Wave 병렬 구현 → Spec 리뷰 → Quality 리뷰
          ↓ [승인 게이트]
Phase 5: Test          — 단위/통합/UI 테스트
          ↓
Phase 6: Evaluate      — 성공 기준 전체 검증
          ↓
Phase 7: Document      — 문서 업데이트, 로컬 커밋
          ↓ [사용자 승인 시]
Phase 8: Retrospect    — memory.md 업데이트
```

### 승인 게이트

Phase 3(Plan) 완료 후와 Phase 4(Generate) 완료 후에 각각 사용자 승인을 요청한다. 계획이나 구현 결과가 마음에 들지 않으면 수정 요청을 하면 된다.

### 피드백 루프

- 테스트 실패 → Phase 4 재실행
- 성공 기준 미달 → Phase 4 또는 Phase 5 재실행
- Spec 리뷰 이슈 → 해당 태스크 Implementer 재디스패치

---

## 고도화 절차

### memory.md를 활용한 점진적 개선

Phase 8(Retrospect)을 꾸준히 실행하면 `memory.md`에 프로젝트별 패턴이 누적된다. Phase 2와 Phase 3에서 이 기억을 참고하여 이전에 실패했던 접근법을 반복하지 않는다.

`memory.md` 구조:

```markdown
## [프로젝트명] 반복 실패 패턴
| 유형 | 발생 횟수 | 마지막 발생 | 권고 대응 |
|------|-----------|-------------|-----------|
| SQL 마이그레이션 누락 | 2 | 2025-03-15 | Plan에서 마이그레이션 태스크 별도 Wave 분리 |

## [프로젝트명] 효과적이었던 패턴
- API 엔드포인트와 프론트엔드 호출을 별도 Wave로 분리 → 충돌 없음

## [프로젝트명] 프로젝트 고유 주의사항
- Qdrant 컬렉션 스키마 변경 시 재색인 필요 (2025-03-10)

## 스킬 개선 제안
- [ ] Phase 3에서 DB 스키마 변경 여부를 자동 감지하는 체크 추가
```

### 페이즈 커스터마이징

각 페이즈 파일(`phases/*.md`)은 독립적으로 수정할 수 있다. 예를 들어:

- 팀 코드 리뷰 규칙을 `04-generate.md`의 Quality 리뷰 기준에 추가
- 사내 테스트 프레임워크 명령을 `05-test.md`에 명시
- CI/CD 연동 설정을 `05-test.md`의 CI 통합 섹션에 추가

### 서브에이전트 프롬프트 튜닝

`implementer-prompt.md`, `spec-reviewer-prompt.md`, `code-quality-reviewer-prompt.md`는 각각 구현자, Spec 리뷰어, 품질 리뷰어 서브에이전트의 행동을 정의한다. 팀 표준이나 도메인 특성에 맞게 수정하면 더 정확한 결과를 얻을 수 있다.

---

## 파일 구조 (런타임)

실행 중 생성되는 파일들:

```
.claude/.harness/               # .gitignore 대상 — git에 올라가지 않음
├── context.md                  # 프로젝트 컨텍스트 캐시 (재실행 시 재사용)
├── hooks/
│   ├── post-edit.sh            # 초기화 시 스킬에서 복사된 훅 스크립트
│   └── .registered             # 훅 등록 완료 플래그
└── artifacts/
    └── 2025-01-15-143022/      # 실행 ID별 아티팩트
        ├── clarify.md
        ├── context.md
        ├── plan.md
        ├── generate.md
        ├── test.md
        ├── evaluate.md
        ├── document.md
        ├── handoff-01to02.md
        ├── handoff-02to03.md
        └── ...
```

---

## 라이선스

MIT
