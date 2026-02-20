"""Game lifecycle management — kill, launch, and load saves via OCR.

Safety guardrails for automated agents:
- Only kills Civ 6 processes (hardcoded process names)
- Only launches Civ 6 via Steam (hardcoded app ID 289070)
- Only loads saves from the known autosave directory
- No config file modifications, no arbitrary system commands
- All process/file interactions are scoped to Civ 6 only

Requires: pyobjc-framework-Quartz, pyobjc-framework-Vision
Install with: uv pip install 'civ6-mcp[launcher]'
"""

from __future__ import annotations

import asyncio
import glob
import logging
import os
import subprocess
import time

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants — hardcoded for safety (not configurable by agents)
# ---------------------------------------------------------------------------

STEAM_APP_ID = "289070"
_ALLOWED_PROCESS_PATTERNS = ("Civ6",)  # pkill -f pattern — only matches Civ 6
_PROCESS_NAMES = ("Civ6_Exe_Child", "Civ6_Exe", "Civ6")  # for window detection
SAVE_DIR = os.path.expanduser(
    "~/Library/Application Support/Sid Meier's Civilization VI/"
    "Sid Meier's Civilization VI/Saves/Single/auto"
)

# How long to wait after kill for Steam to deregister the game
_KILL_SETTLE_SECONDS = 10
# How long to wait for game process to appear after launch
_LAUNCH_TIMEOUT_SECONDS = 60
# How long to wait for main menu after process starts
_MAIN_MENU_WAIT_SECONDS = 15


def _require_gui_deps():
    """Import and return GUI dependencies, raising clear error if missing."""
    try:
        import Quartz
        import Vision
        from Foundation import NSURL
        return Quartz, Vision, NSURL
    except ImportError:
        raise RuntimeError(
            "Game launcher requires pyobjc GUI dependencies. "
            "Install with: uv pip install 'civ6-mcp[launcher]'"
        )


# ---------------------------------------------------------------------------
# Process management (no GUI deps needed)
# ---------------------------------------------------------------------------

def is_game_running() -> bool:
    """Check if Civ 6 is running."""
    r = subprocess.run(
        ["pgrep", "-f", _ALLOWED_PROCESS_PATTERNS[0]],
        capture_output=True,
    )
    return r.returncode == 0


def _kill_game_sync() -> str:
    """Kill Civ 6 and wait for Steam to deregister. Blocking."""
    if not is_game_running():
        return "Game is not running."

    subprocess.run(["pkill", "-9", "-f", "Civ6"], capture_output=True)
    log.info("Killed Civ 6, waiting %ds for Steam to deregister", _KILL_SETTLE_SECONDS)

    # Wait for process to actually die
    for _ in range(10):
        if not is_game_running():
            break
        time.sleep(1)

    # Extra wait for Steam to deregister
    time.sleep(_KILL_SETTLE_SECONDS)

    if is_game_running():
        return "WARNING: Game process may still be running after kill attempt."
    return "Game killed. Steam deregistration wait complete."


def _launch_game_sync() -> str:
    """Launch Civ 6 via Steam and wait for process. Blocking."""
    if is_game_running():
        return "Game is already running."

    subprocess.run(["open", f"steam://run/{STEAM_APP_ID}"])
    log.info("Launched Civ 6 via Steam, waiting for process...")

    for i in range(_LAUNCH_TIMEOUT_SECONDS):
        if is_game_running():
            log.info("Game process detected after %ds", i)
            # Wait for main menu to be reachable
            time.sleep(_MAIN_MENU_WAIT_SECONDS)
            return f"Game launched. Process started after {i}s, waited {_MAIN_MENU_WAIT_SECONDS}s for main menu."
        time.sleep(1)

    return "WARNING: Game process not detected after launch. Check Steam."


# ---------------------------------------------------------------------------
# OCR + GUI helpers (require pyobjc)
# ---------------------------------------------------------------------------

def _screenshot(path: str = "/tmp/civ_ocr_nav.png") -> str:
    """Take a screenshot of the entire screen."""
    subprocess.run(["screencapture", "-x", path], check=True)
    return path


def _ocr(image_path: str) -> list[tuple[str, int, int, int, int]]:
    """Run OCR, return [(text, screen_x, screen_y, width, height)]."""
    Quartz, Vision, NSURL = _require_gui_deps()

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
        # Vision: normalized coords, origin bottom-left → screen coords (retina /2)
        sx = (bbox.origin.x + bbox.size.width / 2) * img_w / 2
        sy = (1 - bbox.origin.y - bbox.size.height / 2) * img_h / 2
        sw = bbox.size.width * img_w / 2
        sh = bbox.size.height * img_h / 2
        results.append((text, int(sx), int(sy), int(sw), int(sh)))
    return results


def _get_game_window() -> tuple[int, int, int, int] | None:
    """Get game window bounds (x, y, w, h) via AppleScript."""
    for proc in _PROCESS_NAMES:
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


def _find_text(
    ocr_results: list[tuple[str, int, int, int, int]],
    target: str,
    exact: bool = False,
    window_bounds: tuple[int, int, int, int] | None = None,
    prefer_bottom: bool = False,
) -> tuple[str, int, int, int, int] | None:
    """Find OCR result matching target within game window.

    Args:
        prefer_bottom: When True and multiple matches exist, return the one
            with the largest y coordinate (lowest on screen). Useful when a
            label and a button have the same text (e.g. "Load Game" title
            at top vs "Load Game" button at bottom).
    """
    target_lower = target.lower().strip()
    matches = []
    for text, x, y, w, h in ocr_results:
        if window_bounds:
            wx, wy, ww, wh = window_bounds
            if not (wx <= x <= wx + ww and wy <= y <= wy + wh):
                continue
        if exact and text.strip().lower() == target_lower:
            matches.append((text, x, y, w, h))
        elif not exact and target_lower in text.lower():
            matches.append((text, x, y, w, h))
    if not matches:
        return None
    if prefer_bottom:
        return max(matches, key=lambda m: m[2])
    return matches[0]


def _click(x: int, y: int) -> None:
    """Click at screen coordinates."""
    Quartz = _require_gui_deps()[0]
    e = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventMouseMoved, (x, y), 0)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, e)
    time.sleep(0.15)
    e = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDown, (x, y), 0)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, e)
    time.sleep(0.05)
    e = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseUp, (x, y), 0)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, e)


def _bring_to_front() -> None:
    """Bring the game window to front."""
    for proc in _PROCESS_NAMES:
        r = subprocess.run([
            "osascript", "-e",
            f'tell application "System Events" to set frontmost of process "{proc}" to true'
        ], capture_output=True)
        if r.returncode == 0:
            break
    time.sleep(0.3)


def _wait_for_text(
    target: str, timeout: int = 60, exact: bool = False, interval: int = 3,
    prefer_bottom: bool = False,
) -> tuple[str, int, int, int, int] | None:
    """Wait until OCR finds target text in game window."""
    start = time.time()
    while time.time() - start < timeout:
        _bring_to_front()
        time.sleep(0.5)
        bounds = _get_game_window()
        results = _ocr(_screenshot())
        match = _find_text(results, target, exact=exact, window_bounds=bounds,
                           prefer_bottom=prefer_bottom)
        if match:
            return match
        time.sleep(interval)
    return None


def _click_text(
    target: str, timeout: int = 30, exact: bool = False, post_delay: float = 2,
    prefer_bottom: bool = False,
) -> bool:
    """Find text via OCR and click it. Returns success."""
    match = _wait_for_text(target, timeout=timeout, exact=exact,
                           prefer_bottom=prefer_bottom)
    if not match:
        log.warning("OCR: '%s' not found after %ds", target, timeout)
        return False
    text, x, y, w, h = match
    log.info("OCR: found '%s' at (%d,%d) — clicking", text, x, y)
    _bring_to_front()
    _click(x, y)
    time.sleep(post_delay)
    return True


# ---------------------------------------------------------------------------
# Save discovery
# ---------------------------------------------------------------------------

def get_latest_autosave() -> str | None:
    """Find the most recent autosave name (without extension)."""
    saves = glob.glob(os.path.join(SAVE_DIR, "AutoSave_*.Civ6Save"))
    if not saves:
        return None
    saves.sort(key=os.path.getmtime, reverse=True)
    return os.path.basename(saves[0]).replace(".Civ6Save", "")


def list_autosaves(limit: int = 10) -> list[str]:
    """List recent autosave names, newest first."""
    saves = glob.glob(os.path.join(SAVE_DIR, "AutoSave_*.Civ6Save"))
    saves.sort(key=os.path.getmtime, reverse=True)
    return [os.path.basename(s).replace(".Civ6Save", "") for s in saves[:limit]]


# ---------------------------------------------------------------------------
# Menu navigation (blocking — run via asyncio.to_thread)
# ---------------------------------------------------------------------------

def _navigate_to_save_sync(save_name: str) -> str:
    """Navigate: Main Menu → Single Player → Load Game → Autosaves → select → Load.

    Blocking operation — takes 30-90 seconds. Returns status message.
    """
    _require_gui_deps()  # Fail fast if deps missing
    steps = []

    log.info("[1/6] Waiting for main menu (Single Player)...")
    if not _click_text("Single Player", timeout=90, exact=True, post_delay=3):
        return "FAILED: Could not find 'Single Player' on main menu. Is the game at the main menu?"
    steps.append("Clicked Single Player")

    log.info("[2/6] Clicking 'Load Game'...")
    if not _click_text("Load Game", timeout=15, exact=True, post_delay=3):
        return "FAILED: Could not find 'Load Game' button."
    steps.append("Clicked Load Game")

    log.info("[3/6] Clicking 'Autosaves' tab...")
    if not _click_text("Autosaves", timeout=10, exact=True, post_delay=2):
        log.info("Autosaves tab not found — may already be selected")
        steps.append("Autosaves tab (may already be selected)")
    else:
        steps.append("Clicked Autosaves tab")

    log.info("[4/6] Looking for save '%s'...", save_name)
    if not _click_text(save_name, timeout=15, post_delay=2):
        return f"FAILED: Save '{save_name}' not found in autosaves list. Steps completed: {', '.join(steps)}"
    steps.append(f"Selected save {save_name}")

    log.info("[5/6] Clicking 'Load Game' button (bottom, not title)...")
    if not _click_text("Load Game", timeout=10, post_delay=5, prefer_bottom=True):
        steps.append("Load Game button not found (may have loaded from double-click)")
    else:
        steps.append("Clicked Load Game button")

    log.info("[6/6] Checking for leader screen...")
    match = _wait_for_text("CONTINUE GAME", timeout=30, exact=True)
    if match:
        text, x, y, w, h = match
        log.info("Found CONTINUE GAME at (%d,%d) — clicking", x, y)
        _bring_to_front()
        _click(x, y)
        time.sleep(3)
        steps.append("Clicked CONTINUE GAME")
    else:
        steps.append("No leader screen (loading directly)")

    return f"Save loading. Steps: {', '.join(steps)}. Wait ~10s then use get_game_overview to verify."


# ---------------------------------------------------------------------------
# Async public API (called by MCP tools)
# ---------------------------------------------------------------------------

async def kill_game() -> str:
    """Kill Civ 6 and wait for Steam to deregister."""
    return await asyncio.to_thread(_kill_game_sync)


async def launch_game() -> str:
    """Launch Civ 6 via Steam and wait for process."""
    return await asyncio.to_thread(_launch_game_sync)


async def load_save_from_menu(save_name: str | None = None) -> str:
    """Navigate the main menu to load a save via OCR.

    Args:
        save_name: Autosave name (e.g. "AutoSave_0221"). If None, loads most recent.

    Requires the game to be at the main menu (launched but no game loaded).
    """
    if save_name is None:
        save_name = get_latest_autosave()
        if save_name is None:
            return "No autosaves found in save directory."

    # Validate save exists on disk
    save_path = os.path.join(SAVE_DIR, f"{save_name}.Civ6Save")
    if not os.path.exists(save_path):
        available = list_autosaves(5)
        avail_str = ", ".join(available) if available else "none"
        return f"Save '{save_name}' not found. Available: {avail_str}"

    return await asyncio.to_thread(_navigate_to_save_sync, save_name)


async def restart_and_load(save_name: str | None = None) -> str:
    """Kill game, relaunch, and load a save. Full recovery sequence.

    This is the recommended tool for recovering from game hangs.
    Takes 60-120 seconds total.
    """
    results = []

    # Step 1: Kill
    kill_result = await kill_game()
    results.append(f"Kill: {kill_result}")

    # Step 2: Launch
    launch_result = await launch_game()
    results.append(f"Launch: {launch_result}")
    if "not detected" in launch_result:
        return " | ".join(results) + " | ABORTED: Game failed to launch."

    # Step 3: Load save via OCR
    load_result = await load_save_from_menu(save_name)
    results.append(f"Load: {load_result}")

    return " | ".join(results)
