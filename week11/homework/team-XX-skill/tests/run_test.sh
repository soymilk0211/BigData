#!/usr/bin/env bash
# 用法：tests/run_test.sh <測試ID> "<提示詞>" [max_turns]
# 在乾淨的暫存目錄安裝本 Skill，以 Claude Code 非互動模式執行，存 stream-json log（已去除絕對路徑）。
set -euo pipefail
ID="$1"; PROMPT="$2"; MAXT="${3:-}"
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$(mktemp -d)"
mkdir -p "$WORK/.claude/skills" "$SKILL_DIR/test-logs"
mkdir -p "$WORK/.claude/skills/student-rental-check"
tar -C "$SKILL_DIR" --exclude ./test-logs --exclude ./tests --exclude ./output --exclude '__pycache__' -cf - . | tar -C "$WORK/.claude/skills/student-rental-check" -xf -
mkdir -p "$WORK/data"
# 可選：LVR_CACHE 指向已下載的官方 zip 資料夾（<季別>.zip），避免每次重新下載
[ -n "${LVR_CACHE:-}" ] && ln -s "$LVR_CACHE" "$WORK/data/lvr-cache"
cd "$WORK"
ARGS=(-p "$PROMPT" --setting-sources project,local --output-format stream-json --verbose
      --allowedTools "Skill" "Read" "Write" "Edit" "Glob" "Grep" "Bash")
[ -n "$MAXT" ] && ARGS+=(--max-turns "$MAXT")
claude "${ARGS[@]}" > raw.jsonl 2> stderr.txt || true
# 去除絕對路徑：暫存目錄 → <WORK>，家目錄 → ~
sed -E "s#${WORK}#<WORK>#g; s#/tmp/[^\" ]*#<TMP>#g; s#/home/[^/\"]+/#~/#g; s#/root/#~/#g" raw.jsonl > "$SKILL_DIR/test-logs/${ID}.jsonl"
# 輸出檔（不含 591 即時爬取的原始資料夾）留存供 E3 證據
if [ -d output ]; then
  RUN="$(ls output | tail -1)"
  mkdir -p "$SKILL_DIR/test-logs/${ID}-output"
  tar -C "output/$RUN" --exclude './591_*' --exclude './01_collected*.csv' --exclude './03_inclusion_log.csv' -cf - . | tar -C "$SKILL_DIR/test-logs/${ID}-output" -xf -
fi
echo "$WORK"
