#!/usr/bin/env python3
"""inbox_server.py — 폰(MacroDroid)에서 오는 문자·통화·음성을 받아 수신함(data/inbox.jsonl)에 한 줄씩 쌓는다.

판단·답장은 여기서 하지 않는다. 이 서버는 "받아서 줄 세우기"만 하고,
비서(Claude 세션)가 scripts/poll-trigger.sh 로 깨어나 읽는다.

엔드포인트 (전부 헤더 X-Internal-Token 필요):
  POST /sms    form 또는 JSON: from, text, [ts], [app]   — 문자·카톡 알림 텍스트
  POST /call   multipart file=녹음파일, ?number=&name=      — 통화 녹음 (SONIOX_API_KEY 있을 때만)
  POST /voice  multipart file=녹음파일                       — 음성메모 (SONIOX_API_KEY 있을 때만)
  GET  /health

실행:
  cd server && uvicorn inbox_server:app --host 127.0.0.1 --port 8787
  (공개 URL 은 cloudflared 터널로만. 0.0.0.0 으로 열지 마세요.)
"""
import fcntl
import hashlib
import hmac
import json
import os
import time
from pathlib import Path

import httpx
from fastapi import FastAPI, Header, HTTPException, Request

ROOT = Path(__file__).resolve().parent.parent
INBOX = ROOT / "data" / "inbox.jsonl"
LOCK = ROOT / "data" / "inbox.lock"

TOKEN = os.environ.get("INBOX_TOKEN", "")
SONIOX_KEY = os.environ.get("SONIOX_API_KEY", "")
MAX_AUDIO = 60 * 1024 * 1024  # 60MB

if not TOKEN:
    raise SystemExit("INBOX_TOKEN 이 비어 있습니다. .env 를 채우고 `set -a; source .env; set +a` 후 실행하세요.")

app = FastAPI()
_recent_audio: dict = {}  # sha256 -> last seen
_recent: dict[tuple, float] = {}


def _check(token: str | None):
    if not token or not hmac.compare_digest(str(token), TOKEN):
        raise HTTPException(status_code=401, detail="bad token")


def _is_dup(source: str, sender: str, text: str) -> bool:
    """같은 발신자·같은 본문이 60초 안에 또 오면 버린다 (폰 매크로가 2~3번 연속 쏘는 경우)."""
    key = (source, sender, text)
    now = time.time()
    last = _recent.get(key)
    _recent[key] = now
    if len(_recent) > 1000:
        for k in [k for k, v in _recent.items() if now - v > 120]:
            _recent.pop(k, None)
    return last is not None and now - last < 60


def enqueue(source: str, text: str, extra: dict | None = None) -> str | None:
    if _is_dup(source, (extra or {}).get("sender", ""), text):
        return None
    item = {"source": source, "text": text, "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "id": f"{source}-{int(time.time() * 1000)}"}
    if extra:
        item.update(extra)
    INBOX.parent.mkdir(parents=True, exist_ok=True)
    with open(LOCK, "a") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        try:
            with open(INBOX, "a", encoding="utf-8") as f:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        finally:
            fcntl.flock(lk, fcntl.LOCK_UN)
    return item["id"]


def transcribe(audio: bytes, filename: str) -> str:
    """Soniox 비동기 전사. 키가 없으면 빈 문자열."""
    if not SONIOX_KEY:
        return ""
    h = {"Authorization": f"Bearer {SONIOX_KEY}"}
    with httpx.Client(timeout=120) as c:
        up = c.post("https://api.soniox.com/v1/files", headers=h,
                    files={"file": (filename, audio)}).json()
        job = c.post("https://api.soniox.com/v1/transcriptions", headers=h, json={
            "file_id": up["id"], "model": "stt-async-v5", "language_hints": ["ko"],
        }).json()
        for _ in range(120):
            st = c.get(f"https://api.soniox.com/v1/transcriptions/{job['id']}", headers=h).json()
            if st.get("status") == "completed":
                tr = c.get(f"https://api.soniox.com/v1/transcriptions/{job['id']}/transcript", headers=h).json()
                return (tr.get("text") or "").strip()
            if st.get("status") == "error":
                return ""
            time.sleep(2)
    return ""


async def _read_audio(request: Request) -> tuple[bytes, str]:
    ct = request.headers.get("content-type", "")
    if "multipart" in ct:
        form = await request.form()
        f = form.get("file")
        if f is None or isinstance(f, str):
            for v in form.values():
                if hasattr(v, "read"):
                    f = v
                    break
        if hasattr(f, "read"):
            data = await f.read()
            return data[:MAX_AUDIO], getattr(f, "filename", None) or "audio.m4a"
        return b"", "audio.m4a"
    body = await request.body()
    return body[:MAX_AUDIO], "audio.m4a"


@app.get("/health")
def health():
    n = sum(1 for _ in open(INBOX, encoding="utf-8")) if INBOX.exists() else 0
    return {"ok": True, "inbox_lines": n, "stt": bool(SONIOX_KEY)}


@app.post("/sms")
async def sms(request: Request, x_internal_token: str = Header(None)):
    _check(x_internal_token)
    ct = request.headers.get("content-type", "")
    raw = (await request.body()).decode("utf-8", "replace")
    if "json" in ct:
        try:
            d = json.loads(raw or "{}")
        except Exception:
            d = {}
        sender = str(d.get("from") or d.get("sender") or "")
        text = str(d.get("text") or d.get("body") or d.get("message") or "")
        ts = str(d.get("ts") or d.get("time") or "")
        appname = str(d.get("app") or d.get("package") or "")
    else:
        from urllib.parse import parse_qs
        q = parse_qs(raw, keep_blank_values=True)
        g = lambda *ks: next((q[k][0] for k in ks if q.get(k)), "")
        sender, text, ts, appname = g("from", "sender"), g("text", "body", "message"), g("ts", "time"), g("app", "package")
        # 진단용: 아는 키 말고 온 것들도 로그에 남긴다. 카톡 알림 구조가 바뀌어 "방 이름이 어느 칸에 있나"를
        # 찾을 때, 폰 매크로에 후보 변수를 여러 개 실어 보내고 여기 journal 에서 키·값을 눈으로 본다.
        known = {"from", "sender", "text", "body", "message", "ts", "time", "app", "package"}
        extra = {k: (v[0][:80] if v else "") for k, v in q.items() if k not in known}
        if extra:
            print(f"[sms] extra keys: {extra!r}", flush=True)
    # 삼성 메시지 앱 알림의 제목(발신자)은 방향성 유니코드(U+2068/U+2069)로 감싸져 온다 — 벗겨서 저장.
    sender = sender.replace("\u2068", "").replace("\u2069", "").strip()
    if not text.strip():
        return {"ok": False, "reason": "empty"}
    src = "kakao" if any(k in appname.lower() for k in ("kakao", "카카오", "카톡")) else "sms"
    rid = enqueue(src, text, {"sender": sender, "sms_ts": ts, "app": appname})
    return {"ok": True, "id": rid, "src": src}


@app.post("/call")
async def call(request: Request, x_internal_token: str = Header(None)):
    _check(x_internal_token)
    if not SONIOX_KEY:
        raise HTTPException(status_code=503, detail="STT 키 없음 — 통화 전사는 꺼져 있습니다")
    audio, fname = await _read_audio(request)
    if len(audio) < 200:
        return {"ok": False, "reason": "no audio"}
    # 같은 녹음이 6시간 안에 또 오면 버린다 — 부재중 통화에서 폰 매크로가 "직전 녹음 파일"을 다시 쏘는 사고 방어.
    digest = hashlib.sha256(audio).hexdigest()
    now = time.time()
    for h in [h for h, t in _recent_audio.items() if now - t > 6 * 3600]:
        _recent_audio.pop(h, None)
    if digest in _recent_audio:
        return {"ok": True, "reason": "duplicate_audio", "skipped": True}
    _recent_audio[digest] = now
    text = transcribe(audio, fname)
    if not text:
        return {"ok": False, "reason": "transcribe_failed"}
    number = (request.query_params.get("number") or request.headers.get("x-call-number") or "").strip()
    name = (request.query_params.get("name") or request.headers.get("x-call-name") or "").strip()
    head = f"📞 {'발신' if request.query_params.get('dir') == 'out' else '수신'} {name} {number}".strip()
    rid = enqueue("call", f"{head}\n\n{text}", {"sender": number, "name": name})
    return {"ok": True, "id": rid, "chars": len(text)}


@app.post("/voice")
async def voice(request: Request, x_internal_token: str = Header(None)):
    _check(x_internal_token)
    if not SONIOX_KEY:
        raise HTTPException(status_code=503, detail="STT 키 없음 — 음성메모 전사는 꺼져 있습니다")
    audio, fname = await _read_audio(request)
    if len(audio) < 200:
        return {"ok": False, "reason": "no audio"}
    text = transcribe(audio, fname)
    if not text:
        return {"ok": False, "reason": "transcribe_failed"}
    rid = enqueue("voice", text)
    return {"ok": True, "id": rid, "chars": len(text)}
