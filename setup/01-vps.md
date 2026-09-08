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

## 우분투가 아니라 로키(Rocky)·알마(Alma)·CentOS 로 만드셨다면

**다시 안 파셔도 됩니다.** 이 매뉴얼에서 실제로 안 맞는 건 패키지 설치 명령 하나뿐입니다.
Claude CLI·텔레그램 연동·폰 세팅·솔라피는 배포판을 가리지 않습니다.

바꿔 쓰실 것은 이것뿐입니다:

```bash
dnf install -y git tmux curl python3 python3-pip jq
```

(`python3-venv` 는 따로 없습니다. 로키에서는 python3 에 이미 들어 있습니다.)

앞으로 매뉴얼에 `apt install` 이 나오면 `dnf install` 로 읽으시면 됩니다.

한 가지만 미리 알아두세요. 레드햇 계열은 **SELinux** 라는 보안 기능이 기본으로 켜져 있어서,
나중에 웹서버나 터널을 붙일 때 "권한 없음(Permission denied)" 이 한 번 날 수 있습니다.
그때는 서버에서 `sudo ausearch -m avc -ts recent` 를 쳐서 나온 내용을 그대로 Claude 에게 보여주시면
어디를 열어야 하는지 알려줍니다. **SELinux 를 통째로 끄지는 마세요** — 그건 문을 다 열어두는 것과 같습니다.

## 두 가지 약속

1. **서버 프로그램은 127.0.0.1 에만 묶고, 바깥 공개는 터널로.** (4단계에서 cloudflared 로 폰→서버 길을 엽니다. 포트를 0.0.0.0 으로 열면 전 세계에서 두드립니다.)
2. **`.env` 파일 하나에 모든 키를 두고 git 에 올리지 않습니다.** 이 레포의 `.gitignore` 가 이미 막아둡니다.

다음 → [02-claude-telegram.md](02-claude-telegram.md)
