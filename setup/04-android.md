# 4. 안드로이드 폰 세팅 (문자·통화 → 서버)

원장 폰에 오는 **문자**(그리고 원하면 **통화 녹음**)를 서버 수신함으로 자동 전송합니다.
앱은 **MacroDroid**(무료 버전으로 충분)를 씁니다. 원리는 하나입니다:

> "문자가 오면 → 서버 주소로 HTTP POST 한 번"

3단계에서 비서가 알려준 두 값이 필요합니다: **터널 주소**(`https://xxxx.trycloudflare.com`)와 **INBOX_TOKEN**.

## 4-1. 문자 전달 매크로

MacroDroid → 매크로 추가:

| 항목 | 설정 |
|---|---|
| **트리거** | SMS 수신 → 발신자: 아무나 |
| **액션** | HTTP 요청 (HTTP Request) |
| · 방법 | POST |
| · URL | `https://<터널주소>/sms` |
| · 헤더 | `X-Internal-Token` = `<INBOX_TOKEN>` |
| · 본문 형식 | Form(x-www-form-urlencoded) |
| · 파라미터 | `from` = `{sms_number}` / `text` = `{sms_message}` / `ts` = `{hour}:{minute}` |

저장하고, 다른 폰에서 원장 폰으로 문자를 하나 보내보세요.
서버에서 `python3 scripts/inbox-ack.py --status` 를 치면 1건이 보이고, 1분 안에 비서가 텔레그램으로 그 문자를 정리해 보고합니다.

## 4-2. 카톡 알림도 받기 (선택)

| 항목 | 설정 |
|---|---|
| **트리거** | 알림 수신 → 앱: 카카오톡 |
| **액션** | 위와 같은 HTTP POST, 파라미터에 `app` = `kakao` 추가, `from` = `{notification_title}`, `text` = `{notification}` |

서버는 `app` 에 kakao 가 있으면 문자와 구분해 `kakao` 로 기록합니다.
⚠️ 카톡은 알림에 뜨는 만큼만 옵니다(사진은 "사진을 보냈습니다"로만). 잠금화면 알림 내용 숨김이 켜져 있으면 본문이 안 옵니다.

## 4-3. 통화 녹음 전달 (선택 — STT 키 필요)

통화 내용까지 비서가 요약하게 하려면 `.env` 에 `SONIOX_API_KEY` 를 넣고(soniox.com, 종량제) 매크로를 하나 더 만듭니다.

| 항목 | 설정 |
|---|---|
| **트리거** | 통화 종료 |
| **액션 1** | 대기 10초 (녹음 파일이 저장될 시간) |
| **액션 2** | HTTP 요청 POST `https://<터널주소>/call?number={call_number}&name={call_name}` , 헤더 `X-Internal-Token`, 본문 = **파일 업로드**(통화 녹음 폴더의 최신 파일, 파라미터 이름 `file`) |

통화 자동 녹음은 폰 기종·통신사에 따라 되는 곳과 안 되는 곳이 있습니다. 안 되면 문자만으로 시작해도 충분히 쓸모 있습니다.

## 4-4. 잘 안 될 때

- 서버 `data/poll-trigger.log` 와 `journalctl -u inbox-server -n 50` 을 보면 도착했는지, 토큰이 틀렸는지(401) 바로 보입니다.
- 같은 문자가 두 번 오면 서버가 60초 안 중복은 알아서 버립니다.
- 터널 주소가 바뀌었으면(quick tunnel 재시작) 매크로 URL 만 바꾸면 됩니다.

다음 → [05-solapi.md](05-solapi.md)
