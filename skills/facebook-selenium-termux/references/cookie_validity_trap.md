# Cookie validity trap — why `current_url` lies, and the probe that doesn't

Discovered 2026-08-29 after a full session of false "login OK" / "CO BAI" confidence
that turned out to be a dead (rejected) cookie session.

## The trap
`https://m.facebook.com/` does NOT contain the substring `login` even when it IS the
login page (blue "f" logo + email/password fields). So any check of the form:

```python
is_logged_in = "login" not in d.current_url.lower()   # ALWAYS True on login page
```

returns `True` on the login screen. You then spin on a composer that never renders.

## The reliable check
After inject_cookies + d.get("https://m.facebook.com/") (+ time.sleep(4)):

```python
src = d.page_source
is_logged_in = ("Log in" not in src) and ("Quan" in src)
```

If src contains "Log in" -> cookies REJECTED (stale / rotated / not-logged-in export).
Also vision_check the screenshot — must NOT show the blue "f" + 2 input fields.

## Cookie flakiness on datacenter IP
A cookie file that logged in in run A may fail in run B minutes later (FB rotates
xs/datr on unusual IP). Re-verify login EVERY run; ask for a FRESH export from a
currently-open logged-in FB tab when it fails.

## The page_source phrase false-positive (verify step)
If POST silently fails, the composer DOM still holds the post text, so
`"BÓNG ĐEN THÙ GHÉT" in d.page_source` is True even when the post NEVER published.
Always pair the phrase check with a vision_analyze on the loaded profile screenshot
confirming the text appears as a PUBLISHED post, not inside a composer input box.
