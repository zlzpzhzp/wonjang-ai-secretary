# 2. Claude CLI 설치·로그인 + 텔레그램 연동

## 2-1. Claude Code 설치

서버(ssh 접속 상태)에서:

```bash
curl -fsSL https://claude.ai/install.sh | bash
claude --version
```

## 2-2. 로그인

```bash
claude
```

처음 실행하면 브라우저 로그인 링크가 뜹니다. 서버엔 브라우저가 없으니
**링크를 복사해서 내 폰/노트북 브라우저에서 열고**, 나오는 코드를 터미널에 붙여넣습니다.
Claude 유료 구독(Pro/Max) 계정으로 로그인하면 됩니다. 로그인 후 `/exit` 로 나옵니다.

## 2-3. 텔레그램 봇 만들기

1. 텔레그램에서 **@BotFather** 검색 → `/newbot` → 이름·아이디 입력 → **토큰**을 받습니다. (`123456:ABC-...` 형태)
2. 만든 봇에게 아무 말이나 한 번 보냅니다.
3. 브라우저에서 `https://api.telegram.org/bot<토큰>/getUpdates` 를 열면 `"chat":{"id":8446…}` 처럼 **내 chat_id** 가 보입니다.

## 2-4. 텔레그램 플러그인 켜기

```bash
claude
```

세션 안에서:

```
/plugin install telegram@claude-plugins-official
/telegram:configure
```

토큰을 물으면 붙여넣고, 접근 정책은 **allowlist(허용 목록)** 로 두고 내 chat_id 만 허용합니다.
(`/telegram:access` 로 나중에 바꿀 수 있습니다.) 끝나면 `/exit`.

## 2-5. 이 레포 받기 + .env 채우기

```bash
cd /root
git clone https://github.com/zlzpzhzp/wonjang-ai-secretary.git
cd wonjang-ai-secretary
cp .env.example .env
nano .env        # TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID 두 줄만 먼저 채웁니다
```

## 2-6. 비서 띄우기

```bash
bash scripts/start-bot.sh
```

tmux 세션 `secretary` 안에서 Claude 가 텔레그램에 붙어 대기합니다.
**이제 폰 텔레그램에서 봇에게 말을 걸어보세요.** 답이 오면 성공입니다.

- 화면 보기: `tmux attach -t secretary` / 나오기: `Ctrl-b` 다음 `d`
- 서버 재부팅 후에도 뜨게 하려면 crontab 에 한 줄:
  `@reboot sleep 20 && bash /root/wonjang-ai-secretary/scripts/start-bot.sh`

다음 → [03-give-this-repo.md](03-give-this-repo.md)
