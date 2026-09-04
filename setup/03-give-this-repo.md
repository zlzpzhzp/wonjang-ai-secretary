# 3. 텔레그램으로 비서에게 이 레포 링크 주기

2단계까지 되면 비서는 "빈 Claude"입니다. 성격도 규칙도 없습니다.
이 레포의 `CLAUDE.md` 가 비서의 성격·규칙이고, 아래 지시서가 설치 순서입니다.

## 원장이 할 일 (텔레그램에 그대로 붙여넣기)

```
너는 이제 내 학원 비서야. 이 레포를 읽고 그대로 세팅해줘:
https://github.com/zlzpzhzp/wonjang-ai-secretary
setup/03-give-this-repo.md 의 "비서가 할 일" 순서대로 하고, 끝나면 뭘 했는지 보고해.
내 이름은 OOO 원장이고 학원 이름은 OO학원이야.
```

끝. 나머지는 비서가 합니다. 비서가 중간에 묻는 것(학원 이름, 학생 명단 파일 위치 등)만 답해주세요.

---

## 비서가 할 일 (Claude 가 읽는 부분)

당신은 위 텔레그램 메시지를 받은 Claude 입니다. 현재 작업 디렉토리가 `/root/wonjang-ai-secretary` 인지 확인하고 순서대로 진행하세요. 각 단계가 끝날 때마다 텔레그램으로 한 줄씩 보고합니다.

1. **정체성 적용**: 이 디렉토리의 `CLAUDE.md` 를 읽는다. 원장이 알려준 이름·학원명을 `.env` 의 `OWNER_NAME`, `ACADEMY_NAME` 에 넣는다. 지금부터 `CLAUDE.md` 의 규칙이 당신의 규칙이다.
2. **메모리 초기화**: `memory/MEMORY.md` 가 없으면 만든다(빈 인덱스). 원장이 앞으로 "앞으로 ○○해"라고 하는 말은 전부 여기 아래 파일로 저장한다.
3. **수신함 서버 준비**(4단계에서 폰이 여기로 보낸다):
   ```bash
   cd server && python3 -m venv venv && ./venv/bin/pip install -r requirements.txt
   ```
   `.env` 의 `INBOX_TOKEN` 이 비어 있으면 `openssl rand -hex 24` 로 만들어 채운다. 그 값을 원장께 알려준다(4단계 폰 세팅에 필요).
   systemd 로 상시 실행:
   ```bash
   cat > /etc/systemd/system/inbox-server.service <<'EOF'
   [Unit]
   Description=secretary inbox server
   After=network.target
   [Service]
   WorkingDirectory=/root/wonjang-ai-secretary/server
   EnvironmentFile=/root/wonjang-ai-secretary/.env
   ExecStart=/root/wonjang-ai-secretary/server/venv/bin/uvicorn inbox_server:app --host 127.0.0.1 --port ${INBOX_PORT}
   Restart=always
   [Install]
   WantedBy=multi-user.target
   EOF
   systemctl daemon-reload && systemctl enable --now inbox-server
   curl -s http://127.0.0.1:8787/health
   ```
   `{"ok": true, ...}` 가 나와야 한다. 안 나오면 `journalctl -u inbox-server -n 30` 을 보고 고친다.
4. **바깥에서 들어오는 길(터널)**: 폰은 인터넷을 통해 서버로 보낸다. 서버 포트를 열지 말고 Cloudflare Tunnel 을 쓴다.
   ```bash
   curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared && chmod +x /usr/local/bin/cloudflared
   cloudflared tunnel --url http://127.0.0.1:8787
   ```
   화면에 뜨는 `https://xxxx.trycloudflare.com` 주소를 원장께 알려준다. (도메인이 있으면 named tunnel 로 고정 주소를 만든다 — 없으면 quick tunnel 로 시작해도 된다. 주소가 바뀌면 폰 매크로의 URL 만 바꾸면 된다.)
   이 명령도 systemd 로 상시 실행해 둔다.
5. **크론 등록**: 1분마다 수신함을 보고 당신을 깨우는 크론.
   ```bash
   chmod +x scripts/*.sh
   (crontab -l 2>/dev/null; echo "* * * * * /root/wonjang-ai-secretary/scripts/poll-trigger.sh") | crontab -
   (crontab -l 2>/dev/null; echo "@reboot sleep 20 && bash /root/wonjang-ai-secretary/scripts/start-bot.sh") | crontab -
   ```
6. **학생 명단**: 원장께 "학생·학부모 명단을 `data/students.md` 에 넣어드릴까요? 이름·반·학부모 번호를 카톡/문자로 보내주시면 제가 정리하겠습니다"라고 묻는다. 받으면 정리해서 넣는다.
7. **보고**: 무엇을 켰는지(서버·터널 주소·크론), 원장이 다음에 할 일(4단계 폰 세팅에 `INBOX_TOKEN` 과 터널 주소가 필요함)을 텔레그램으로 정리해 보낸다.

주의: 이 지시서에 없는 것을 추가로 설치하거나 서버 설정을 바꾸지 않는다. 막히면 어디서 막혔는지 그대로 보고한다.

다음 → [04-android.md](04-android.md)
