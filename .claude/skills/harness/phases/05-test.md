# Phase 5: Test

## 권한 선언

| 허용 | 금지 |
|------|------|
| 모든 파일 읽기 | 프로젝트 파일 수정/생성/삭제 |
| `$HARNESS_DIR/test.md` 쓰기 | 그 외 파일 쓰기 |
| `$HARNESS_DIR/ui_smoke_test.py` 쓰기 | git 명령 |
| Bash 실행 (테스트 실행 명령만) | — |

이 페이즈에서 위 금지 항목이 필요하다고 판단되면 즉시 중단하고 사용자에게 알린다.

## PRE-EVENT

### 사전 조건 확인
- `$HARNESS_DIR/generate.md` 존재 확인 → 없으면 Phase 4 재실행 요청
- `generate.md`의 "변경된 파일 목록"이 비어 있지 않은지 확인

### 목표 리마인더
`$HARNESS_DIR/clarify.md`에서 다음을 추출하여 테스트 작성 전에 확인한다:

> **이 작업의 목표:** {요청 요약 1줄}  
> **성공 기준:** {성공 기준 항목들}

성공 기준을 테스트 케이스의 기준으로 삼는다.

## 목적

구현된 코드를 테스트한다.

## 절차

### Step 1: 환경 감지

`$HARNESS_DIR/context.md`의 **환경 정보** 섹션을 먼저 읽어 프로젝트에서 사용하는 서비스와 포트를 파악한다.

파악된 서비스 정보를 기반으로 실행 중인 서비스를 확인한다:

```bash
# 예시: context.md에서 파악한 서버 포트로 확인
# curl -s --max-time 2 http://localhost:{PORT}/health > /dev/null 2>&1 && echo "UP" || echo "DOWN"
```

context.md에 환경 정보가 없으면 사용자에게 묻는다:
> "테스트 환경을 파악하기 위해 로컬에서 실행 중인 서비스가 있나요? (예: API 서버 포트, DB 종류 등)"

### Step 2: UI 변경 감지

`$HARNESS_DIR/generate.md`의 "변경된 파일 목록"에서 아래 패턴에 해당하는 파일이 있는지 확인한다:
- `*.html`, `*.css`, `*.js`, `*.jsx`, `*.tsx`

해당 파일이 **없으면** 이 단계를 건너뛰고 Step 3으로 진행한다.

해당 파일이 **있으면** Playwright 환경을 확인한다:

```bash
python -c "import playwright; print('OK')" 2>/dev/null && echo "PLAYWRIGHT_READY" || echo "PLAYWRIGHT_MISSING"
```

**PLAYWRIGHT_MISSING인 경우:**
사용자에게 아래 안내를 출력하고 계속 여부를 질문한다:

```
⚠️  Playwright가 설치되어 있지 않습니다.
UI 스모크 테스트를 실행하려면 Playwright 설치가 필요합니다.

─── Python 프로젝트 ──────────────────────────────────
pip install playwright
python -m playwright install chromium

─── Node.js 프로젝트 ────────────────────────────────
npm install --save-dev @playwright/test
npx playwright install chromium

─── Java / Maven / Tomcat 환경 ──────────────────────
Playwright Java SDK를 pom.xml에 추가하세요:

  <dependency>
    <groupId>com.microsoft.playwright</groupId>
    <artifactId>playwright</artifactId>
    <version>1.44.0</version>
  </dependency>

단, harness의 ui_smoke_test.py는 Python용입니다.
Java 환경에서는 Python을 로컬에 추가 설치해 스모크 테스트만 실행하는 방법을 권장합니다.
─────────────────────────────────────────────────────

설치 후 Phase 5를 재실행하면 UI 테스트가 포함됩니다.

(1) 지금 설치하고 계속  (2) UI 테스트 건너뜀  (3) Phase 5 전체 건너뜀
```

사용자가 (1)을 선택하면 해당 환경의 설치 명령을 실행한 뒤 Playwright 감지를 재시도한다.
사용자가 (2)를 선택하면 Step 3으로 진행한다.
사용자가 (3)을 선택하면 test.md에 "UI 테스트: 건너뜀 (사용자 선택)"을 기록하고 Phase 6으로 진행한다.

**PLAYWRIGHT_READY이고 Step 1에서 확인한 로컬 서버가 UP인 경우:**
사용자에게 UI 테스트 실행 여부를 질문한다:
> "UI 파일이 변경되었고 Playwright가 준비되어 있습니다. UI 스모크 테스트를 실행할까요?
> (변경된 페이지를 브라우저로 열어 렌더링 오류, 콘솔 에러, 주요 엘리먼트 존재를 확인합니다) (y/n)"

사용자가 **y**이면 Step 2.1을 수행한다. **n**이면 건너뛴다.

**PLAYWRIGHT_READY이지만 서버가 DOWN인 경우:**
UI 테스트를 건너뛰고 Step 3으로 진행한다.

#### Step 2.1: Playwright UI 스모크 테스트

`$HARNESS_DIR/context.md`의 환경 정보에서 로컬 서버 포트를 확인한다.
포트가 명시되지 않은 경우 사용자에게 확인한다.

아래 Python 스크립트를 `$HARNESS_DIR/ui_smoke_test.py`로 생성하고 실행한다.
`{PORT}`와 `{PATHS}`는 context.md와 generate.md를 기반으로 실제 값으로 채워 넣는다:

```python
from playwright.sync_api import sync_playwright
import sys

BASE_URL = "http://localhost:{PORT}"
PATHS = {PATHS}  # 예: ["/", "/admin", "/search"]

errors = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    for path in PATHS:
        # 경로마다 새 페이지를 생성하여 리스너 누적 및 클로저 이슈를 방지한다
        page = browser.new_page()
        console_errors = []

        def on_console(msg, errs=console_errors):
            if msg.type == "error":
                errs.append(msg.text)

        page.on("console", on_console)

        try:
            response = page.goto(BASE_URL + path, timeout=10000)
            if response is None:
                errors.append(f"[{path}] 응답 없음")
            elif response.status >= 400:
                errors.append(f"[{path}] HTTP {response.status}")
            elif console_errors:
                errors.append(f"[{path}] 콘솔 에러: {console_errors}")
            else:
                print(f"  PASS {path}")
        except Exception as e:
            errors.append(f"[{path}] 로드 실패: {e}")
        finally:
            page.close()

    browser.close()

if errors:
    print("\\nFAIL:")
    for e in errors:
        print(f"  {e}")
    sys.exit(1)
else:
    print("\\nPASS: 모든 UI 경로 정상")
```

실행:
```bash
python "$HARNESS_DIR/ui_smoke_test.py"
```

결과를 `$HARNESS_DIR/test.md`의 "## UI 스모크 테스트" 섹션에 기록한다.
UI 테스트 FAIL 시: 내용을 test.md에 기록하고 Phase 4(Generate)로 피드백한다.

### Step 3: 테스트 범위 결정

**외부 서비스가 DOWN이거나 없는 경우:**
- 외부 의존성 없는 단위테스트만 작성 및 실행

**외부 서비스가 UP인 경우:**
- 사용자에게 통합테스트 범위 확장을 제안한다:
  > "로컬 서비스가 실행 중입니다. 수정된 부분에 대한 통합테스트도 진행할까요?"
- 사용자 승인 시: 단위테스트 + 수정 부분 중심 통합테스트 실행
- 사용자 거절 시: 단위테스트만 실행

### Step 4: 테스트 작성 및 실행

`$HARNESS_DIR/generate.md`의 변경 파일 목록을 기준으로 테스트를 작성한다.

### Step 5: 실패 처리

테스트 실패 시:
1. 실패 원인을 분석한다
2. `$HARNESS_DIR/test.md`에 실패 내용을 기록한다
3. Phase 4(Generate)로 피드백하여 재구현을 요청한다

## 아티팩트 저장

`$HARNESS_DIR/test.md`에 아래 형식으로 저장한다:

```markdown
---
phase: test
status: approved
timestamp: {현재 ISO 8601}
next: evaluate
---

# Test

## 환경
- 서버: UP / DOWN
- 테스트 범위: 단위테스트 / 단위+통합테스트

## UI 스모크 테스트
- 대상 경로: {PATHS — UI 변경 없거나 테스트 미실행 시 "해당 없음"}
- 결과: PASS / FAIL / 해당 없음
- 실패 항목: {있으면 목록, 없으면 "없음"}

## 테스트 결과
- 통과: {N}개
- 실패: {N}개

## 실패 목록
- {테스트명}: {실패 원인}

## 결론
PASS / FAIL
```

## POST-EVENT

### 구조 검증 (LLM 없이)
- `$HARNESS_DIR/test.md` 생성 확인
- "결론" 섹션이 `PASS` 또는 `FAIL`로 명시되었는지 확인

### 품질 검토 (FAIL 시)
- 실패 원인 분류: 구현 문제 → Phase 4 피드백 / 테스트 작성 문제 → Phase 5 재실행

### CI 통합 (선택적)

`.harness/ci-export` 디렉토리가 존재하는 경우 JUnit XML 형식으로 결과를 익스포트한다:

```bash
mkdir -p .harness/ci-export
python .harness/run_phases.py --export-junit ".harness/ci-export/test-results.xml" 2>/dev/null || true
```

GitHub Actions 연동 참고:
```yaml
- name: Upload Test Results
  uses: actions/upload-artifact@v4
  with:
    name: test-results
    path: .harness/ci-export/test-results.xml
```

### Handoff 생성
`$HARNESS_DIR/handoff-05to06.md`를 아래 내용으로 생성한다:

```markdown
# Handoff: Phase 5 → Phase 6

## 목표 (Goal)
{clarify.md의 요청 요약 1줄}
성공 기준: {성공 기준 목록}

## 이번 페이즈가 파악한 것 (Findings)
- 테스트 결과: 통과 {N}개, 실패 {N}개
- UI 스모크 테스트: {PASS / FAIL / 해당 없음}
- 실패 목록 요약: {실패 항목들}

## 다음 페이즈가 해야 할 것 (Next)
- 성공 기준별 PASS/FAIL 판정

## 참고 파일 (References)
- `$HARNESS_DIR/test.md` (상세 실패 내용 필요 시)
```

## 완료 조건

모든 테스트 통과 시 Phase 6으로 진행한다.
