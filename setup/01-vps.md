# 1. 가상 서버(VPS) 구독

비서는 24시간 켜져 있어야 하니 집 컴퓨터 말고 **작은 리눅스 서버 하나**를 빌립니다.

## 고르는 기준

- Ubuntu 22.04 또는 24.04
- RAM 2GB 이상 (4GB 권장 — Claude CLI + 수신 서버 + 터널이 같이 돕니다)
- 디스크 20GB 이상
- 월 1~3만 원대면 충분합니다. 지역은 어디든 상관없습니다(폰·텔레그램·솔라피 전부 HTTPS라 지연 체감 없음).

업체는 아무 데나 괜찮습니다. Vultr, Linode, Hetzner, 국내라면 카페24·가비아 클라우드 등.
계정 만들고 → Ubuntu 인스턴스 하나 생성 → **root 비밀번호 또는 SSH 키**를 받아두면 끝입니다.

## 접속 확인

맥/윈도우 터미널에서:

```bash
ssh root@<서버IP>
```

들어가지면 아래 기본 도구만 깔아둡니다(5분):

```bash
apt update && apt install -y git tmux curl python3 python3-venv python3-pip jq
```

## 두 가지 약속

1. **서버 프로그램은 127.0.0.1 에만 묶고, 바깥 공개는 터널로.** (4단계에서 cloudflared 로 폰→서버 길을 엽니다. 포트를 0.0.0.0 으로 열면 전 세계에서 두드립니다.)
2. **`.env` 파일 하나에 모든 키를 두고 git 에 올리지 않습니다.** 이 레포의 `.gitignore` 가 이미 막아둡니다.

다음 → [02-claude-telegram.md](02-claude-telegram.md)
