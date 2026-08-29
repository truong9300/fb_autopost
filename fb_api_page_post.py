#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dang bai len PAGE AI News Daily qua Graph API (user yeu cau 'dang page luon')."""
import requests, json

USER_TOKEN = "EAAUxmZAMn6Y4BR9oTjukZBNh5NjHUAj9YMHQG6gtHfgn5BWVabgxm67jE87rtfs9MYBgeQpLnUuzkrFZApmJRdRlhIS5w17rKTFHc7oPyyKwhW1RFUgmdBtD3a6TCs7qGkE54u0RmGTwy0YJEoEiFxqJhMyKRP6sLa2YUT71mHIz9Hi2O2xggDZAcP5lI9kDsgZDZD"

MSG = open("/root/fb_manager_local/fb_post_message.txt", encoding="utf-8").read().strip()

# Lay page token
r = requests.get("https://graph.facebook.com/v22.0/me/accounts?access_token=" + USER_TOKEN)
pages = r.json().get("data", [])
target = None
for p in pages:
    if "ai news" in p["name"].lower() or "ainews" in p["name"].lower():
        target = p; break
if not target:
    print("Pages:", [(p["name"], p["id"]) for p in pages]); raise SystemExit("AI News Daily not found")

PID = target["id"]
PTOK = target["access_token"]
print("Target:", target["name"], PID)

# Post
resp = requests.post(f"https://graph.facebook.com/v22.0/{PID}/feed", data={
    "message": MSG,
    "access_token": PTOK
})
out = resp.json()
print("RESULT:", json.dumps(out, indent=2)[:300])
if "id" in out:
    print("SUCCESS POST ID:", out["id"])
else:
    print("FAIL:", out)
