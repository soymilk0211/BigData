#!/usr/bin/env bash
# claude_live.sh <ID> <max_turns|0> "<prompt>" : install skill in a clean dir, run Claude Code non-interactively, show tool events live
ID="$1"; MAXT="$2"; P="$3"
SK=/tmp/demo/skill; W=$(mktemp -d); mkdir -p "$W/.claude/skills/student-rental-check"
tar -C "$SK" --exclude ./test-logs --exclude ./tests --exclude ./output --exclude '__pycache__' -cf - . | tar -C "$W/.claude/skills/student-rental-check" -xf -
cd "$W"
ARGS=(-p "$P" --setting-sources project,local --output-format stream-json --verbose --allowedTools Skill Read Write Edit Glob Grep Bash)
[ "$MAXT" != 0 ] && ARGS+=(--max-turns "$MAXT")
/home/box/.local/bin/claude "${ARGS[@]}" 2>/dev/null | tee raw.jsonl | jq -r --unbuffered '
 if .type=="system" and .subtype=="init" then "● init  已安裝的 skill 含 student-rental-check：\((.skills|index("student-rental-check"))!=null)"
 elif .type=="assistant" then (.message.content[] |
   if .type=="tool_use" then "→ tool_use \u001b[1;33m\(.name)\u001b[0m  \((.input.skill // .input.file_path // .input.command // .input.pattern // "")|tostring|gsub("\n";" ")|.[0:85])"
   elif .type=="text" then "  💬 \(.text|gsub("\n";" ")|.[0:90])" else empty end)
 elif .type=="result" then "● result  回合數 \(.num_turns)　結束狀態 \(.subtype)" else empty end' \
 | sed -u -E -e "s#${W}/?#<WORK>/#g" -e "s#/tmp/[^ \"']*#<TMP>#g" -e "s#/home/[^/ \"]+#~#g"
mkdir -p /workspace/bigdata-week11/live-logs
sed -E "s#${W}#<WORK>#g; s#/tmp/[^\" ]*#<TMP>#g; s#/home/[^/\"]+/#~/#g; s#/root/#~/#g" raw.jsonl > /workspace/bigdata-week11/live-logs/${ID}.jsonl; cp /workspace/bigdata-week11/live-logs/${ID}.jsonl /tmp/demo/live-logs/
