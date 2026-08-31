# CDP Mouse Event Attempt — Still Failed (2026-08-28)

User asked: "Có giả lập bấm chuột không?" — then requested a script using CDP mouse events (`Input.dispatchMouseEvent`) instead of Selenium `.click()`.

## What was tried
- `Input.dispatchMouseEvent` with `mousePressed`/`mouseReleased` at element center coordinates
- Bezier curve mouse movement (cubic Bezier with random control points)
- `Input.dispatchKeyEvent` for keyboard (tried both CDP key events and Selenium `send_keys`)
- xdotool (apt install xdotool) for OS-level mouse/keyboard on VPS

## Result
- CDP click on trigger → composer opened ✅
- File upload → CDN OK ✅
- CDP click on editor area → editor appeared ✅ (contenteditable showed with placeholder)
- BUT: text typed via CDP `dispatchKeyEvent` did NOT register in React state
- Text typed via Selenium `send_keys` also did NOT register
- "Tiếp" button stayed DISABLED ❌
- Final post: TEXT-ONLY ❌

## Key finding
Even OS-level mouse events (CDP/xdotool) that successfully click the editor cannot make React/Lexical register the file attachment. The React-internal event that fires after a *real* user selects a file through the OS file dialog is not replicated by programmatic file input manipulation — regardless of how the click/move/keyboard events are synthesized.

## Code snippet (CDP mouse event helper)
```python
def cdp_mouse(driver, x, y, btn="left", click=True):
    if click:
        driver.execute_cdp_cmd("Input.dispatchMouseEvent", {
            "type": "mousePressed", "x": x, "y": y, "button": btn, "clickCount": 1
        })
        time.sleep(random.uniform(0.05, 0.15))
        driver.execute_cdp_cmd("Input.dispatchMouseEvent", {
            "type": "mouseReleased", "x": x, "y": y, "button": btn, "clickCount": 1
        })
    else:
        driver.execute_cdp_cmd("Input.dispatchMouseEvent", {
            "type": "mouseMoved", "x": x, "y": y
        })
```

## Conclusion
CDP mouse events are more "real" than Selenium clicks for bypassing bot detection, but they do NOT solve the React state sync problem for FB photo uploads. Do not promise this as a solution.
