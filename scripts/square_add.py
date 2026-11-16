#!/usr/bin/env python3
"""Light a visitor square on the square wall from a "[SQUARE]" issue.

Runs from .github/workflows/squares.yml on `issues: opened`. The issue body is
untrusted text from a stranger that ends up on a public profile, so:
  * it is only read from the event JSON and regex-parsed, never given to a shell
  * the message passes a strict whitelist (letters, digits, space and ! ? ' , -)
    so no URLs, markup or HTML survive, and is capped at 28 chars
  * a profanity/slur blocklist rejects abuse (leet-speak normalised)
  * shade must be 1-4
  * one square per login (re-submitting just updates your message)
"""
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "squares", "visitors.json")
LOGIN_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$")
MAX_LEN, MAX_SQUARES = 28, 180
BLOCK = ["fuck", "shit", "bitch", "cunt", "nigg", "fagg", "retard", "rape", "nazi", "hitler", "slut", "whore",
         "dick", "cock", "pussy", "porn", "sex", "kys", "killyourself", "suicide", "asshole", "bastard", "twat"]
LEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a", "$": "s", "!": "i"})
BODY_RE = re.compile(r"###\s*Message\s*\n+(.*?)\n+###\s*Shade\s*\n+(\d)", re.S | re.I)


def gh(*args):
    if os.environ.get("DRY_RUN"):
        print("gh", *args)
        return
    subprocess.run(["gh", *args], check=False)


def clean(msg):
    msg = re.sub(r"[^A-Za-z0-9 !?',\-]", "", msg)
    return re.sub(r"\s+", " ", msg).strip()[:MAX_LEN]


def blocked(msg):
    flat = re.sub(r"[^a-z]", "", msg.lower().translate(LEET))
    return any(w in flat for w in BLOCK)


def main():
    event = json.load(open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8"))
    issue = event["issue"]
    num, login = str(issue["number"]), issue["user"]["login"]
    if not LOGIN_RE.match(login):
        sys.exit("unexpected login format")

    m = BODY_RE.search(issue.get("body") or "")
    if not m:
        gh("issue", "comment", num, "--body", "Couldn't read that form. Please use the **Light a square** template.")
        gh("issue", "close", num, "--reason", "not planned")
        return
    msg = clean(m.group(1)) or "was here"
    level = min(4, max(1, int(m.group(2))))
    if blocked(msg):
        gh("issue", "comment", num, "--body", "That message didn't pass the filter. Try something friendlier in a new issue.")
        gh("issue", "close", num, "--reason", "not planned")
        return

    db = json.load(open(DB, encoding="utf-8")) if os.path.exists(DB) else []
    db = [v for v in db if v["login"].lower() != login.lower()]  # one square per login
    db.append({"login": login, "msg": msg, "level": level,
               "date": datetime.now(timezone.utc).strftime("%Y-%m-%d")})
    db = db[-MAX_SQUARES:]
    json.dump(db, open(DB, "w", encoding="utf-8"), indent=2)
    gh("issue", "comment", num, "--body",
       f"\U0001F7E9 **Your square is lit, @{login}.** It shows up on the profile wall within a minute. "
       "Open another issue any time to change your message.")
    gh("issue", "close", num, "--reason", "completed")
    print("square lit:", login, level, repr(msg))


if __name__ == "__main__":
    main()
