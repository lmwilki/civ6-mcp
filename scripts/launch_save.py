#!/usr/bin/env python3
"""Launch Civ 6 and load a save file via OCR-guided menu navigation.

Usage:
    python scripts/launch_save.py                    # load most recent autosave
    python scripts/launch_save.py AutoSave_0221      # load specific autosave
    python scripts/launch_save.py --kill-first        # kill existing game first

Requires: pyobjc-framework-Quartz, pyobjc-framework-Vision (pip install)

Note: FireTuner only allows ONE connection at a time. This script does NOT
poll the port — use MCP tools after the script finishes.
"""

import argparse
import glob
import os
import subprocess
import sys
import time

import Quartz
import Vision
from Foundation import NSURL


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

STEAM_APP_ID = "289070"
PROCESS_NAME = "Civ6_Exe_Child"
SAVE_DIR = os.path.expanduser(
    "~/Library/Application Support/Sid Meier's Civilization VI/"
    "Sid Meier's Civilization VI/Saves/Single/auto"
)


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def screenshot(path="/tmp/civ_ocr_nav.png"):
    subprocess.run(["screencapture", "-x", path], check=True)
    return path


def ocr(image_path):
    """Run OCR on an image, return list of (text, screen_x, screen_y, width, height)."""
    url = NSURL.fileURLWithPath_(image_path)
    source = Quartz.CGImageSourceCreateWithURL(url, None)
    image = Quartz.CGImageSourceCreateImageAtIndex(source, 0, None)
    img_w = Quartz.CGImageGetWidth(image)
    img_h = Quartz.CGImageGetHeight(image)

    request = Vision.VNRecognizeTextRequest.alloc().init()
    request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
    handler = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(image, None)
    handler.performRequests_error_([request], None)

    results = []
    for obs in request.results():
        text = obs.topCandidates_(1)[0].string()
        bbox = obs.boundingBox()
        # Vision: normalized coords, origin bottom-left. Convert to screen coords (retina /2).
        sx = (bbox.origin.x + bbox.size.width / 2) * img_w / 2
        sy = (1 - bbox.origin.y - bbox.size.height / 2) * img_h / 2
        sw = bbox.size.width * img_w / 2
        sh = bbox.size.height * img_h / 2
        results.append((text, int(sx), int(sy), int(sw), int(sh)))
    return results


def get_game_window():
    """Get the game window bounds (x, y, w, h) in screen coords."""
    for proc in [PROCESS_NAME, "Civ6_Exe", "Civ6"]:
        r = subprocess.run([
            "osascript", "-e",
            f'tell application "System Events"\n'
            f'  tell process "{proc}"\n'
            f'    set {{x, y}} to position of window 1\n'
            f'    set {{w, h}} to size of window 1\n'
            f'    return (x as string) & "," & (y as string) & "," & (w as string) & "," & (h as string)\n'
            f'  end tell\n'
            f'end tell'
        ], capture_output=True, text=True)
        parts = r.stdout.strip().split(",")
        if len(parts) == 4:
            return tuple(int(p) for p in parts)
    return None


def find_text(ocr_results, target, exact=False, window_bounds=None):
    """Find OCR result matching target text within game window."""
    target_lower = target.lower().strip()
    for text, x, y, w, h in ocr_results:
        if window_bounds:
            wx, wy, ww, wh = window_bounds
            if not (wx <= x <= wx + ww and wy <= y <= wy + wh):
                continue
        if exact and text.strip().lower() == target_lower:
            return (text, x, y, w, h)
        if not exact and target_lower in text.lower():
            return (text, x, y, w, h)
    return None


def click(x, y):
    """Move mouse to (x,y) and click."""
    e = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventMouseMoved, (x, y), 0)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, e)
    time.sleep(0.15)
    e = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDown, (x, y), 0)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, e)
    time.sleep(0.05)
    e = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseUp, (x, y), 0)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, e)


def bring_to_front():
    subprocess.run([
        "osascript", "-e",
        f'tell application "System Events" to set frontmost of process "{PROCESS_NAME}" to true'
    ], capture_output=True)
    time.sleep(0.3)


def is_running():
    r = subprocess.run(["pgrep", "-f", PROCESS_NAME], capture_output=True)
    return r.returncode == 0


def kill_game():
    subprocess.run(["pkill", "-9", "-f", "Civ6"], capture_output=True)
    time.sleep(10)  # Steam needs time to register game as stopped


def launch_game():
    subprocess.run(["open", f"steam://run/{STEAM_APP_ID}"])


def wait_for_text(target, timeout=60, exact=False, interval=3):
    """Wait until OCR finds target text in game window."""
    start = time.time()
    while time.time() - start < timeout:
        bring_to_front()
        time.sleep(0.5)
        bounds = get_game_window()
        results = ocr(screenshot())
        match = find_text(results, target, exact=exact, window_bounds=bounds)
        if match:
            return match
        time.sleep(interval)
    return None


def click_text(target, timeout=30, exact=False, post_delay=2):
    """Find text in game window via OCR and click it."""
    match = wait_for_text(target, timeout=timeout, exact=exact)
    if not match:
        print(f"  ERROR: '{target}' not found on screen after {timeout}s")
        return False
    text, x, y, w, h = match
    print(f"  Found '{text}' at ({x},{y}) — clicking")
    bring_to_front()
    click(x, y)
    time.sleep(post_delay)
    return True


# ---------------------------------------------------------------------------
# Menu navigation
# ---------------------------------------------------------------------------

def get_latest_autosave():
    """Find the most recent autosave filename (without extension)."""
    saves = glob.glob(os.path.join(SAVE_DIR, "AutoSave_*.Civ6Save"))
    if not saves:
        return None
    saves.sort(key=os.path.getmtime, reverse=True)
    return os.path.basename(saves[0]).replace(".Civ6Save", "")


def navigate_to_save(save_name):
    """Navigate: Main Menu → Single Player → Load Game → Autosaves → select save → Load."""

    print("[1/6] Waiting for main menu...")
    if not click_text("Single Player", timeout=90, exact=True, post_delay=3):
        return False

    print("[2/6] Clicking 'Load Game'...")
    if not click_text("Load Game", timeout=15, exact=True, post_delay=3):
        return False

    print("[3/6] Clicking 'Autosaves' tab...")
    if not click_text("Autosaves", timeout=10, exact=True, post_delay=2):
        # May already be on autosaves tab
        print("  (may already be on autosaves tab, continuing)")

    print(f"[4/6] Looking for save '{save_name}'...")
    if not click_text(save_name, timeout=15, post_delay=2):
        print(f"  Save '{save_name}' not found in list")
        return False

    print("[5/6] Clicking 'Load Game' button...")
    # The "Load Game" button at the bottom — search for it again
    if not click_text("Load Game", timeout=10, post_delay=5):
        # May have loaded already from double-click
        pass

    print("[6/6] Clicking 'CONTINUE GAME' if leader screen appears...")
    # Wait for either the leader intro screen or the game itself
    match = wait_for_text("CONTINUE GAME", timeout=30, exact=True)
    if match:
        text, x, y, w, h = match
        print(f"  Found '{text}' at ({x},{y}) — clicking")
        bring_to_front()
        click(x, y)
        time.sleep(3)
    else:
        print("  No leader screen — game may be loading directly")

    print("\nDone! Game should be loading. Use MCP tools to verify (get_game_overview).")
    print("NOTE: Do NOT poll FireTuner port from scripts — only one connection allowed.")
    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Launch Civ 6 and load a save")
    parser.add_argument("save", nargs="?", help="Save name (default: most recent autosave)")
    parser.add_argument("--kill-first", action="store_true", help="Kill existing game first")
    parser.add_argument("--no-launch", action="store_true", help="Don't launch, just navigate")
    args = parser.parse_args()

    save_name = args.save or get_latest_autosave()
    if not save_name:
        print("No autosaves found!")
        sys.exit(1)
    print(f"Target save: {save_name}")

    if args.kill_first:
        print("Killing existing game...")
        kill_game()

    if not args.no_launch and not is_running():
        print("Launching Civ 6 via Steam...")
        launch_game()
        for _ in range(30):
            if is_running():
                print("  Process started")
                break
            time.sleep(1)
        else:
            print("  ERROR: Game didn't start")
            sys.exit(1)
        time.sleep(10)  # Let game reach main menu

    if not navigate_to_save(save_name):
        print("FAILED to navigate to save")
        sys.exit(1)


if __name__ == "__main__":
    main()
