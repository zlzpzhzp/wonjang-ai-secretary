#!/bin/bash
# start-bot.sh — tmux 안에서 비서 세션을 띄운다(재시작에도 안전).
#   bash scripts/start-bot.sh            # 세션 이름 기본 'secretary'
#   BOT_SESSION=memo bash scripts/start-bot.sh
#
# 규칙 두 가지 (이걸 어기면 텔레그램이 끊기거나 봇이 크래시 루프에 빠진다):
#   1) 반드시 --channels 플래그와 함께 띄운다. 맨몸 `claude` 로 띄우면 유휴 시 종료→크론이 계속 재시작.
#   2) TELEGRAM_STATE_DIR 를 프로젝트 안으로 고정한다. 안 하면 같은 서버의 다른 봇과 토큰이 충돌한다.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SESSION="${BOT_SESSION:-secretary}"
STATE_DIR="$ROOT/.claude/channels/telegram"
mkdir -p "$STATE_DIR"

[[ -f "$ROOT/.env" ]] || { echo ".env 가 없습니다. .env.example 을 복사해 채우세요."; exit 1; }
set -a; source "$ROOT/.env"; set +a
[[ -n "${TELEGRAM_BOT_TOKEN:-}" ]] || { echo "TELEGRAM_BOT_TOKEN 이 비어 있습니다."; exit 1; }

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "세션 '$SESSION' 이 이미 떠 있습니다. 재시작하려면: tmux kill-session -t $SESSION"
  exit 0
fi

unset TMUX TMUX_PANE
tmux new -d -s "$SESSION" -c "$ROOT" \
  "TELEGRAM_STATE_DIR=$STATE_DIR TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN claude --channels plugin:telegram@claude-plugins-official"
echo "세션 '$SESSION' 시작. 화면 보기: tmux attach -t $SESSION (나오기: Ctrl-b d)"
