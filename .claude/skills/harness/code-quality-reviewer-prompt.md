# Code Quality Reviewer Subagent Prompt Template

Spec 리뷰 통과 후에만 코드 품질 리뷰어 에이전트를 디스패치한다.
`{변수명}` 형식의 자리표시자를 실제 값으로 채운 후 Agent 도구에 전달한다.

**목적:** 구현이 잘 만들어졌는지 (클린하고, 테스트되고, 유지보수 가능한지) 검증한다.

**Spec 준수 리뷰 통과 전에는 디스패치하지 않는다.**

---

## 프롬프트 템플릿

```
Task tool (superpowers:code-reviewer):
  Use template at requesting-code-review/code-reviewer.md

  WHAT_WAS_IMPLEMENTED: {IMPLEMENTER_REPORT}
  PLAN_OR_REQUIREMENTS: 태스크 {TASK_ID} — {TASK_DESCRIPTION}
  BASE_SHA: {BASE_SHA}
  HEAD_SHA: {HEAD_SHA}
  DESCRIPTION: {TASK_NAME}
```

표준 코드 품질 항목 외에 아래를 추가로 검토한다:
- `{CODE_CONVENTIONS}`에 명시된 코드 컨벤션을 준수했는가?
- 각 파일이 하나의 명확한 책임을 가지고 잘 정의된 인터페이스를 가지는가?
- 단위가 독립적으로 이해되고 테스트 가능한가?
- 이 변경으로 이미 큰 파일이 더 커졌는가? (기존 파일 크기가 아닌 이 변경의 기여분에 집중)

### 추가 완성도 검증

Spec Review를 통과했더라도 아래 품질 항목을 추가로 확인한다:

- [ ] Happy path 외 엣지 케이스 처리가 최소 1개 이상 구현됐는가?
- [ ] UI 컴포넌트의 empty state가 명시적으로 렌더링되는가?
- [ ] 코드에 TODO/FIXME/stub 주석이 남아있지 않은가?
- [ ] 타입 오류 및 lint 경고가 없는가?

**리뷰어 반환 형식:** 강점, 이슈 (Critical/Important/Minor), 승인 여부

---

## 주입 변수 설명

| 변수 | 출처 | 설명 |
|------|------|------|
| `{TASK_ID}` | tasks.json | 태스크 식별자 |
| `{TASK_NAME}` | plan.md | 태스크명 |
| `{TASK_DESCRIPTION}` | plan.md | 태스크 요약 |
| `{IMPLEMENTER_REPORT}` | Implementer 보고 | Implementer가 구현한 내용 |
| `{BASE_SHA}` | git log | 태스크 구현 시작 전 커밋 SHA |
| `{HEAD_SHA}` | git log | 태스크 구현 완료 후 현재 커밋 SHA |
| `{CODE_CONVENTIONS}` | context.md | 코드 컨벤션 요약 |
