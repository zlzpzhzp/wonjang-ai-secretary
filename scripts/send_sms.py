#!/usr/bin/env python3
"""send_sms.py — 솔라피(SOLAPI)로 문자 1통 발송. 성공 여부를 숨기지 않는다.

  python3 scripts/send_sms.py 010-1234-5678 - <<< "문안"
  python3 scripts/send_sms.py 010-1234-5678 문안.txt

⚠️ 이 스크립트는 원장이 "ㄱ" 로 승인한 뒤에만 부른다 (CLAUDE.md 발송 규칙).
- 90바이트(한글 45자) 넘으면 LMS 로 자동 전환.
- 응답의 successCount>0 일 때만 exit 0. 아니면 exit≠0 + 이유 출력 → 비서는 "발송했어요"라고 말하면 안 된다.
- 나간 문안은 data/sent-sms.jsonl 에 원문 그대로 남긴다.
"""
import hashlib
import hmac
import json
import os
import secrets
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE = ROOT / "data" / "sent-sms.jsonl"
KST = timezone(timedelta(hours=9))


def auth_header(api_key: str, api_secret: str) -> str:
    date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    salt = secrets.token_hex(16)
    sig = hmac.new(api_secret.encode(), (date + salt).encode(), hashlib.sha256).hexdigest()
    return f"HMAC-SHA256 apiKey={api_key}, date={date}, salt={salt}, signature={sig}"


def euc_kr_bytes(s: str) -> int:
    return sum(2 if ord(ch) > 0x7F else 1 for ch in s)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    to = "".join(c for c in sys.argv[1] if c.isdigit())
    src = sys.argv[2] if len(sys.argv) > 2 else "-"
    text = sys.stdin.read() if src == "-" else Path(src).read_text(encoding="utf-8")
    text = text.rstrip("\n")
    if not text.strip():
        print("ERR: 빈 문안", file=sys.stderr)
        return 1
    key, sec, frm = os.environ.get("SOLAPI_API_KEY"), os.environ.get("SOLAPI_API_SECRET"), os.environ.get("SOLAPI_FROM")
    if not (key and sec and frm):
        print("ERR: SOLAPI_API_KEY / SOLAPI_API_SECRET / SOLAPI_FROM 이 .env 에 없다", file=sys.stderr)
        return 1
    mtype = "SMS" if euc_kr_bytes(text) <= 90 else "LMS"
    body = {"messages": [{"to": to, "from": "".join(c for c in frm if c.isdigit()), "text": text, "type": mtype}]}
    try:
        r = httpx.post("https://api.solapi.com/messages/v4/send-many",
                       headers={"Authorization": auth_header(key, sec), "Content-Type": "application/json"},
                       json=body, timeout=30)
    except Exception as e:
        print(f"ERR: 솔라피 연결 실패 — {e}. **문자 안 나갔다.**", file=sys.stderr)
        return 3
    try:
        res = r.json()
    except Exception:
        print(f"ERR: 응답 해석 실패 HTTP {r.status_code}: {r.text[:200]}", file=sys.stderr)
        return 2
    if r.status_code != 200:
        print(f"ERR: HTTP {r.status_code} — {res.get('errorMessage') or res}", file=sys.stderr)
        return 2
    # 응답: { _id(또는 groupId), count: { total, registeredSuccess, registeredFailed, ... } }
    gid = res.get("groupId") or res.get("_id") or (res.get("groupInfo") or {}).get("_id")
    cnt = res.get("count") or (res.get("groupInfo") or {}).get("count") or {}
    total = int(cnt.get("total", 1) or 1)
    fail = int(cnt.get("registeredFailed", 0) or 0)
    ok = int(cnt.get("registeredSuccess", total - fail) or 0)
    out = {"groupId": gid, "successCount": ok, "failCount": fail, "type": mtype}
    print(json.dumps(out, ensure_ascii=False))
    if ok <= 0:
        print("ERR: successCount 0 — 문자 안 나갔다. 발신번호 인증·잔액·번호 형식을 확인.", file=sys.stderr)
        return 2
    ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
    with open(ARCHIVE, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now(KST).isoformat(), "to": to, "type": mtype, "text": text,
                            "groupId": gid}, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
