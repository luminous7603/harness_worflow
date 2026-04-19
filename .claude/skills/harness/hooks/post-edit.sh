#!/bin/bash
# 파일 수정 후 언어별 포맷터/린터 자동 실행
# 도구가 없으면 조용히 통과

FILE="$1"
if [ -z "$FILE" ]; then exit 0; fi

EXT="${FILE##*.}"

case "$EXT" in
  py)
    command -v ruff    >/dev/null 2>&1 && ruff format "$FILE" || true
    command -v black   >/dev/null 2>&1 && black --quiet "$FILE" || true
    command -v isort   >/dev/null 2>&1 && isort --quiet "$FILE" || true
    ;;
  js|jsx|ts|tsx|mjs|cjs)
    command -v prettier >/dev/null 2>&1 && prettier --write --log-level silent "$FILE" || true
    command -v eslint   >/dev/null 2>&1 && eslint --fix --quiet "$FILE" || true
    ;;
  go)
    command -v gofmt     >/dev/null 2>&1 && gofmt -w "$FILE" || true
    command -v goimports >/dev/null 2>&1 && goimports -w "$FILE" || true
    ;;
  rs)
    command -v rustfmt >/dev/null 2>&1 && rustfmt "$FILE" || true
    ;;
  css|scss|less)
    command -v prettier >/dev/null 2>&1 && prettier --write --log-level silent "$FILE" || true
    ;;
  html|htm)
    command -v prettier >/dev/null 2>&1 && prettier --write --log-level silent "$FILE" || true
    ;;
  json)
    command -v prettier >/dev/null 2>&1 && prettier --write --log-level silent "$FILE" || true
    command -v jq       >/dev/null 2>&1 && jq . "$FILE" > "$FILE.tmp" && mv "$FILE.tmp" "$FILE" || true
    ;;
  yml|yaml)
    command -v prettier >/dev/null 2>&1 && prettier --write --log-level silent "$FILE" || true
    ;;
  rb)
    command -v rubocop >/dev/null 2>&1 && rubocop --autocorrect --no-color -q "$FILE" || true
    ;;
  sh|bash)
    command -v shfmt >/dev/null 2>&1 && shfmt -w "$FILE" || true
    ;;
  java)
    command -v google-java-format >/dev/null 2>&1 && google-java-format --replace "$FILE" || true
    ;;
  kt)
    command -v ktlint >/dev/null 2>&1 && ktlint --format "$FILE" || true
    ;;
  c|cpp|h|hpp)
    command -v clang-format >/dev/null 2>&1 && clang-format -i "$FILE" || true
    ;;
  php)
    command -v php-cs-fixer >/dev/null 2>&1 && php-cs-fixer fix "$FILE" --quiet || true
    ;;
esac

exit 0
