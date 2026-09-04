#!/bin/bash
# poll-trigger.sh — 1분마다 cron. 수신함(data/inbox.jsonl)에 새 줄이 있으면 비서 세션을 깨운다.
#   crontab: * * * * * /path/to/wonjang-ai-secretary/scripts/poll-trigger.sh
# 깨우는 방법 = tmux 세션에 "📱 새 인입 N건…" 메시지를 타이핑해 Enter. 비서는 CLAUDE.md 의
# "인입 처리" 절차대로 읽고, 끝나면 inbox-ack.py 로 처리표시를 올린다(안 올리면 매분 다시 깨운다).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INBOX="$ROOT/data/inbox.jsonl"
STATE="$ROOT/data/.inbox-ack"
LAST="$ROOT/data/.poll-trigger-last"
LOG="$ROOT/data/poll-trigger.log"
SESSION="${BOT_SESSION:-secretary}"

[[ -f "$INBOX" ]] || exit 0
total=$(wc -l < "$INBOX")
ack=0
[[ -f "$STATE" ]] && { read -r ack _ < "$STATE" 2>/dev/null || true; }
[[ "$ack" =~ ^[0-9]+$ ]] || ack=0
pending=$((total - ack))
[[ "$pending" -le 0 ]] && exit 0

tmux has-session -t "$SESSION" 2>/dev/null || { echo "[$(date '+%F %T')] session '$SESSION' not running" >> "$LOG"; exit 0; }

# 비서가 지금 생각/생성 중이면 이번 틱은 건너뛴다 (입력이 섞이지 않게)
pane="$(tmux capture-pane -t "$SESSION" -p 2>/dev/null | tail -n 6 || true)"
if echo "$pane" | grep -qiF "esc to interrupt"; then
  exit 0
fi

# 같은 내용으로 10분 안에 또 깨우지 않는다 (비서가 처리 중일 수 있음)
key="$total"
if [[ -f "$LAST" ]] && [[ "$(cat "$LAST")" == "$key" ]] && [[ $(( $(date +%s) - $(stat -c %Y "$LAST") )) -lt 600 ]]; then
  exit 0
fi

msg="📱 새 인입 ${pending}건 (수신함). 읽고 처리해주세요. 끝나면 python3 scripts/inbox-ack.py --upto <읽은 줄 수> 로 처리표시를 갱신할 것."
tmux send-keys -t "$SESSION" -l -- "$msg"
sleep 0.3
tmux send-keys -t "$SESSION" Enter
echo "$key" > "$LAST"
echo "[$(date '+%F %T')] woke '$SESSION' pending=$pending" >> "$LOG"
