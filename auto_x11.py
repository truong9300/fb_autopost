#!/usr/bin/env python3
"""
auto_x11.py — Hook bàn phím chuột cấp OS (X11/Linux) bằng xdotool.
Mô phỏng input thật — không qua CDP/Selenium.
Dùng để đăng bài FB không bị detect automation.

Cài: apt install xdotool
Chạy: python3 auto_x11.py
"""
import time
import random
import subprocess
import math

# ===== MOUSE =====

def get_mouse_pos():
    """Lấy vị trí chuột hiện tại"""
    r = subprocess.run(["xdotool", "getmouselocation", "--shell"], 
                      capture_output=True, text=True)
    pos = {}
    for line in r.stdout.strip().split('\n'):
        if '=' in line:
            k, v = line.split('=', 1)
            pos[k] = int(v)
    return pos.get('X', 0), pos.get('Y', 0)

def move_mouse(x, y):
    """Di chuyển chuột đến (x, y)"""
    subprocess.run(["xdotool", "mousemove", str(x), str(y)], 
                  capture_output=True)

def click(x=None, y=None, button=1, click_count=1):
    """Click chuột tại (x, y)"""
    if x is not None and y is not None:
        move_mouse(x, y)
        time.sleep(random.uniform(0.05, 0.15))
    
    btn_map = {1: 1, 2: 2, 3: 3}
    xbtn = btn_map.get(button, 1)
    
    for _ in range(click_count):
        subprocess.run(["xdotool", "click", str(xbtn)], capture_output=True)
        time.sleep(random.uniform(0.08, 0.15))

def bezier_mouse(target_x, target_y, duration=0.5):
    """Di chuyển chuột theo Bezier curve (mượt như người thật)"""
    start_x, start_y = get_mouse_pos()
    
    dx = target_x - start_x
    dy = target_y - start_y
    cp1_x = start_x + dx * random.uniform(0.2, 0.5)
    cp1_y = start_y + dy * random.uniform(-0.4, 0.4)
    cp2_x = start_x + dx * random.uniform(0.5, 0.8)
    cp2_y = start_y + dy * random.uniform(-0.4, 0.4)
    
    steps = max(10, int(duration * 30))
    for i in range(steps + 1):
        t = i / steps
        u = 1 - t
        x = u**3 * start_x + 3*u**2*t * cp1_x + 3*u*t**2 * cp2_x + t**3 * target_x
        y = u**3 * start_y + 3*u**2*t * cp1_y + 3*u*t**2 * cp2_y + t**3 * target_y
        move_mouse(int(x), int(y))
        time.sleep(duration / steps + random.uniform(-0.002, 0.005))
    
    move_mouse(target_x, target_y)

def human_click(x, y, button=1):
    """Click chuột giống con người (Bezier move + random delay)"""
    bezier_mouse(x, y, duration=random.uniform(0.3, 0.7))
    time.sleep(random.uniform(0.05, 0.15))
    click(button=button)

# ===== KEYBOARD =====

def type_text(text, min_delay=0.03, max_delay=0.12):
    """Gõ text từng chữ với random delay (giống gõ thật)"""
    for char in text:
        delay = random.uniform(min_delay, max_delay)
        if char in '.,!?;:':
            delay += random.uniform(0.1, 0.3)
        if char == '\n':
            delay += random.uniform(0.2, 0.5)
        if random.random() < 0.02:
            time.sleep(random.uniform(0.3, 0.8))
        
        subprocess.run(["xdotool", "type", "--delay", str(int(delay * 1000)), char],
                      capture_output=True)
        time.sleep(random.uniform(min_delay, max_delay))

def press_key(key):
    """Nhấn một phím"""
    subprocess.run(["xdotool", "key", key], capture_output=True)

def hotkey(modifier, key):
    """Nhấn tổ hợp phím (Ctrl+C, Alt+Tab, etc.)"""
    subprocess.run(["xdotool", "key", f"{modifier}+{key}"], capture_output=True)

# ===== SCREEN =====

def screenshot(filename="screenshot.png"):
    """Chụp màn hình"""
    subprocess.run(["import", "-window", "root", filename], capture_output=True)

def get_screen_size():
    """Lấy kích thước màn hình"""
    r = subprocess.run(["xdotool", "getdisplaygeometry"], capture_output=True, text=True)
    w, h = r.stdout.strip().split()
    return int(w), int(h)

# ===== ELEMENT FINDING =====

def find_by_name(name):
    """Tìm window theo name"""
    r = subprocess.run(["xdotool", "search", "--name", name, "--shell"],
                      capture_output=True, text=True)
    return [int(i) for i in r.stdout.strip().split('\n') if i]

def find_by_class(cls):
    """Tìm window theo class"""
    r = subprocess.run(["xdotool", "search", "--class", cls, "--shell"],
                      capture_output=True, text=True)
    return [int(i) for i in r.stdout.strip().split('\n') if i]

def get_geometry(win_id):
    """Lấy vị trí + kích thước của window"""
    r = subprocess.run(["xdotool", "getwindowgeometry", str(win_id)],
                      capture_output=True, text=True)
    geo = {}
    for line in r.stdout.strip().split('\n'):
        if 'Position' in line:
            pos = line.split('(')[1].split(')')[0]
            geo['x'], geo['y'] = map(int, pos.split(','))
        elif 'Geometry' in line:
            geo['w'], geo['h'] = map(int, line.split()[1].split('x'))
    return geo

def click_element(win_id):
    """Click vào center của window/element"""
    geo = get_geometry(win_id)
    x = geo['x'] + geo['w'] // 2
    y = geo['y'] + geo['h'] // 2
    human_click(x, y)

# ===== MAIN =====

if __name__ == "__main__":
    print("🖱️ AutoX11 — Hook bàn phím chuột cấp OS (xdotool)")
    print(f"Screen: {get_screen_size()}")
    print(f"Mouse: {get_mouse_pos()}")
    print("\nTest: di chuyển chuột đến giữa màn hình...")
    
    w, h = get_screen_size()
    human_click(w // 2, h // 2)
    print("✅ Click OK")
    
    print("\nTest: gõ text...")
    time.sleep(1)
    type_text("Xin chao!")
    print("✅ Type OK")
