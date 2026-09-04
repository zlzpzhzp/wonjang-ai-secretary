#!/usr/bin/env python3
"""inbox-ack.py — 수신함 처리표시.

상태파일 data/.inbox-ack 형식: "<처리한 줄 수> <마지막 항목 id>"
poll-trigger.sh 는 첫 필드만 읽는다. pending = 전체 줄 수 - 첫 필드.

사용:
  inbox-ack.py --status        # 현재 미처리 건수만
  inbox-ack.py --upto N        # N번째 줄까지 처리했다고 표시 (권장 — 읽는 사이 도착한 건은 남는다)
  inbox-ack.py                 # 지금까지 전부 처리했다고 표시
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INBOX = ROOT / "data" / "inbox.jsonl"
STATE = ROOT / "data" / ".inbox-ack"


def rows():
    if not INBOX.exists():
        return []
    return [json.loads(l) for l in INBOX.read_text(encoding="utf-8").splitlines() if l.strip()]


def current_ack():
    if not STATE.exists():
        return 0
    head = STATE.read_text(encoding="utf-8").split()
    return int(head[0]) if head and head[0].isdigit() else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--upto", type=int, default=None)
    a = ap.parse_args()
    r = rows()
    total, ack = len(r), current_ack()
    if a.status:
        print(f"수신함 {total}건 · ack {ack} · 미처리 {max(total - ack, 0)}건")
        for i, it in enumerate(r[ack:], start=ack + 1):
            print(f"  #{i} [{it.get('source')}] {it.get('ts','')} {str(it.get('sender',''))[:20]} — {str(it.get('text',''))[:80]!r}")
        return 0
    new = total if a.upto is None else a.upto
    if new < ack:
        print(f"⛔ --upto {new} 가 현재 ack {ack} 보다 작다 — 되돌리지 않는다")
        return 2
    new = min(new, total)
    last_id = r[new - 1].get("id", "") if new > 0 else ""
    STATE.write_text(f"{new} {last_id}\n", encoding="utf-8")
    print(f"✅ ack {ack} → {new} (수신함 {total}건, 미처리 {total - new}건)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
