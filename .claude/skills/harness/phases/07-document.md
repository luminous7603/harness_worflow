# Phase 7: Document

## 권한 선언

| 허용 | 금지 |
|------|------|
| 모든 파일 읽기 | 소스코드 파일 수정 |
| `$HARNESS_DIR/document.md` 쓰기 | 임의 파일 삭제 |
| 문서 파일(README.md, CLAUDE.md 등) 수정 | git push |
| `git add`, `git commit` 실행 | 그 외 Bash 명령 |

이 페이즈에서 위 금지 항목이 필요하다고 판단되면 즉시 중단하고 사용자에게 알린다.

## PRE-EVENT

### 사전 조건 확인
- `$HARNESS_DIR/evaluate.md` 존재 확인 → 없으면 Phase 6 재실행 요청
- `evaluate.md`의 종합 결과가 `PASS`인지 확인 → `FAIL`이면 Phase 6 재실행 요청
- `$HARNESS_DIR/generate.md`에서 변경 파일 목록 추출 → 문서 업데이트 대상 결정에 사용

## 목적

변경된 기능/API/구조에 맞게 프로젝트 문서를 최신화하고 최종 커밋한다.

## 절차

### Step 1: 문서 파일 구조 파악

프로젝트 내 아래 파일들을 탐색한다:

```bash
find . -name "README.md" -not -path "./.harness/*" -not -path "./node_modules/*"
find . -name "CLAUDE.md" -not -path "./.harness/*"
find . -name "RULES" -o -name "RULES.md" | grep -v ".harness"
```

### Step 2: 수정 위치 결정 및 CLAUDE.md 가지치기

`$HARNESS_DIR/generate.md`의 변경 내용을 기준으로 어느 문서에 무엇을 업데이트해야 하는지 결정한다:

- API 엔드포인트 변경 → `README.md` 또는 관련 API 문서
- 새 기능 추가 → 가장 가까운 상위 `README.md` 또는 `CLAUDE.md`
- 환경 설정 변경 → 루트 `README.md`
- 모듈/컴포넌트 변경 → 해당 디렉토리의 `CLAUDE.md`

#### CLAUDE.md 동기화 및 가지치기

1. **업데이트 대상 결정:**
   - 새 기능/명령어 추가 → CLAUDE.md에 추가
   - 기존 동작 변경 → 해당 섹션만 수정
   - 구현 상세/일회성 메모 → CLAUDE.md에 추가하지 않음

2. **가지치기 조건 (아래 중 하나라도 해당하면 수행):**
   - CLAUDE.md가 200줄 초과
   - 1개월 이상 된 TODO/FIXME 주석 존재
   - 삭제된 파일/기능에 대한 설명 잔존

3. **가지치기 원칙:**
   - WHY(이유)는 유지, WHAT(내용)은 코드에 위임
   - 구현 상세 → 삭제 (코드가 정보 소스)
   - 반복/중복 섹션 → 통합
   - 스타일은 유지, 길이는 줄임

### Step 3: 문서 업데이트

- 기존 문서는 관련 섹션만 수정한다 (전체 재작성 금지)
- 새 문서가 필요한 경우에만 생성한다

### Step 4: 아티팩트 저장

`$HARNESS_DIR/document.md`에 아래 형식으로 저장한다:

```markdown
---
phase: document
status: approved
timestamp: {현재 ISO 8601}
next: ""
---

# Document

## 수정된 문서 목록
- {파일 경로}: {수정 내용 요약}

## 새로 생성된 문서
- {파일 경로}: {생성 이유}
```

### Step 5: 최종 커밋

`utils/git-helpers.md`를 참고하여 커밋한다:

```bash
git add -A
git commit -m "feat: {clarify.md의 요청 요약}"
```

**Push는 절대 하지 않는다.**

### Step 6: 사용자 안내

커밋 완료 후 반드시 아래 메시지를 출력한다:

> "로컬 커밋이 완료되었습니다. 직접 테스트 후 `git push`로 반영해주세요."

### Step 7: Phase 8 안내

커밋 완료 후 아래 메시지를 출력한다:

> "로컬 커밋이 완료되었습니다. 직접 테스트 후 `git push`로 반영해주세요.
>
> 이번 실행을 회고하여 memory.md를 업데이트할까요?
> (권장: 테스트 실패가 있었거나 반복 작업이 있었던 경우) (y/n)"

사용자가 `y`로 승인하면 `phases/08-retrospect.md`를 로드하여 Phase 8을 실행한다.
거절하면 종료한다.

## POST-EVENT

### 구조 검증 (LLM 없이)
- `$HARNESS_DIR/document.md` 생성 확인
- 커밋이 실제로 생성되었는지 `git log --oneline -1`로 확인
