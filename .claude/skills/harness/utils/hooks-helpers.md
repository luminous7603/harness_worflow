# Hooks Helpers

파일 수정 후 언어별 포맷터/린터를 자동 실행하는 Claude Code 훅 설정 가이드.

## 훅 등록 방법

프로젝트의 `.claude/settings.json`에 다음 훅을 추가한다:

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

## 훅 스크립트

스킬 폴더에서 자동 복사되므로 직접 생성 불필요. 초기화는 SKILL.md 시작 절차가 담당한다.

## 등록 확인 방법

훅 등록 완료 후 `.claude/.harness/hooks/.registered` 파일을 생성하여 중복 안내를 방지한다:

```bash
mkdir -p .claude/.harness/hooks
touch .claude/.harness/hooks/.registered
```

## Stop 훅 (Phase 전환 자동 검증)

에이전트 응답 완료 후 `run_phases.py --validate-current`를 자동 실행한다.  
아티팩트 파일 존재 여부와 frontmatter status를 확인하여 이상 시 경고를 출력한다.

### 설계 원칙
- 검증 실패 시 경고만 출력, 작업을 차단하지 않음 (`|| true` 패턴)
- phases.json 없으면 조용히 종료 (harness 미사용 프로젝트에서도 안전)

## 핵심 설계 원칙

- 도구가 설치된 경우에만 실행 (`command -v ... || true` 패턴)
- 도구가 없으면 조용히 통과 — 훅 실패로 인한 작업 중단 없음
- 파일 경로가 비어 있으면 즉시 종료
