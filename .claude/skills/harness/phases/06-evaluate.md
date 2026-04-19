# Phase 6: Evaluate

## 권한 선언

| 허용 | 금지 |
|------|------|
| 모든 파일 읽기 | 프로젝트 파일 수정/생성/삭제 |
| `$HARNESS_DIR/evaluate.md` 쓰기 | 그 외 파일 쓰기 |
| (Bash 실행 없음) | Bash 명령 실행 |

이 페이즈에서 위 금지 항목이 필요하다고 판단되면 즉시 중단하고 사용자에게 알린다.

## PRE-EVENT

### 사전 조건 확인
- `$HARNESS_DIR/test.md` 존재 확인 → 없으면 Phase 5 재실행 요청
- `test.md`의 결론이 `PASS`인지 확인 → `FAIL`이면 Phase 5 재실행 요청 (Evaluate로 오면 안 됨)

### 목표 리마인더
`$HARNESS_DIR/clarify.md`에서 다음을 추출하여 평가 전에 확인한다:

> **이 작업의 목표:** {요청 요약 1줄}  
> **성공 기준:** {성공 기준 항목들 전체}

성공 기준 전체를 평가 기준으로 삼는다.

## 목적

Clarify에서 정의한 성공 기준 대비 최종 결과물을 검증한다.

## 절차

1. `$HARNESS_DIR/clarify.md`의 성공 기준을 읽는다
2. `$HARNESS_DIR/test.md`의 테스트 결과를 읽는다
3. `$HARNESS_DIR/generate.md`의 변경 파일 목록을 읽는다
4. 각 성공 기준 항목에 대해 통과/실패를 판정한다
5. 미달 항목이 있으면 해당 페이즈로 피드백한다:
   - 구현 문제 → Phase 4(Generate)로 피드백
   - 테스트 문제 → Phase 5(Test)로 피드백

## 아티팩트 저장

`$HARNESS_DIR/evaluate.md`에 아래 형식으로 저장한다:

```markdown
---
phase: evaluate
status: approved
timestamp: {현재 ISO 8601}
next: document
---

# Evaluate

## 성공 기준 검증

| 기준 | 결과 | 비고 |
|---|---|---|
| {기준 1} | PASS / FAIL | {비고} |
| {기준 2} | PASS / FAIL | {비고} |

## 종합 결과
PASS / FAIL

## 미달 항목 및 피드백
- {미달 기준}: {피드백 내용} → Phase {N}으로 재실행
```

## POST-EVENT

### 구조 검증 (LLM 없이)
- `$HARNESS_DIR/evaluate.md` 생성 확인
- 모든 성공 기준 항목에 `PASS`/`FAIL`이 기재되었는지 확인

### 품질 검토 (FAIL 시)
- FAIL 항목 원인 분류 후 적절한 페이즈로 피드백

### Handoff 생성
`$HARNESS_DIR/handoff-06to07.md`를 아래 내용으로 생성한다:

```markdown
# Handoff: Phase 6 → Phase 7

## 목표 (Goal)
{clarify.md의 요청 요약 1줄}
성공 기준: {성공 기준 목록}

## 이번 페이즈가 파악한 것 (Findings)
- 성공 기준 검증 결과: {PASS/FAIL 요약}

## 다음 페이즈가 해야 할 것 (Next)
- 업데이트해야 할 문서 목록: {파일 목록}

## 참고 파일 (References)
- `$HARNESS_DIR/generate.md` (변경 파일 목록)
- `$HARNESS_DIR/evaluate.md` (상세 결과)
```

## 완료 조건

모든 성공 기준 PASS 시 Phase 7로 진행한다.
