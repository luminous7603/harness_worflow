# Git Helpers

## 최종 커밋 규칙

Document 페이즈 완료 후 아래 절차를 따른다.

### 1. 커밋 메시지 생성

커밋 메시지는 `clarify.md`의 요청 내용 첫 줄을 기반으로 자동 생성한다.

형식:
```
feat: {clarify.md의 요청 요약 한 줄}

Harness run: {HARNESS_RUN_ID}
```

### 2. 커밋 실행

```bash
git add -A
git commit -m "feat: {요청 요약}"
```

### 3. Push 금지

**절대 `git push`를 실행하지 않는다.**

### 4. 사용자 안내

커밋 완료 후 반드시 아래 메시지를 출력한다:

> "로컬 커밋이 완료되었습니다. 직접 테스트 후 `git push`로 반영해주세요."
