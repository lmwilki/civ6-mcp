"""Game lifecycle management — kill, launch, and load saves via OCR.

Safety guardrails for automated agents:
- Only kills Civ 6 processes (hardcoded process names)
- Only launches Civ 6 via Steam (hardcoded app ID 289070)
- Only loads saves from the known autosave directory
- No config file modifications, no arbitrary system commands
- All process/file interactions are scoped to Civ 6 only

Platform support:
- macOS: fully supported (process mgmt, OCR, window automation)
  Install with: uv pip install 'civ6-mcp[launcher-macos]'
- Windows: process mgmt + save discovery (GUI automation not yet implemented)
"""

from __future__ import annotations

import asyncio
import glob
import logging
import os
import subprocess
import sys
import time
from typing import NamedTuple

log = logging.getLogger(__name__)


class WindowInfo(NamedTuple):
    """Game window metadata from Quartz CGWindowList."""

    window_id: int
    x: int  # screen points
    y: int  # screen points
    w: int  # screen points
    h: int  # screen points
    pid: int


# ---------------------------------------------------------------------------
# Constants — hardcoded for safety (not configurable by agents)
# ---------------------------------------------------------------------------

STEAM_APP_ID = "289070"
_ALLOWED_PROCESS_PATTERNS = ("Civ6",)  # pkill -f pattern — only matches Civ 6
# CGWindowList/AppKit report app name ("Civilization VI"), not binary name ("Civ6_Exe")
_APP_NAME_PATTERNS = ("Civilization",)

if sys.platform == "darwin":
    _PROCESS_NAMES = ("Civ6_Exe_Child", "Civ6_Exe", "Civ6")
    _SAVE_BASE = os.path.expanduser(
        "~/Library/Application Support/Sid Meier's Civilization VI/"
        "Sid Meier's Civilization VI/Saves/Single"
    )
    SAVE_DIR = os.path.join(_SAVE_BASE, "auto")  # autosaves
    SINGLE_SAVE_DIR = _SAVE_BASE  # regular saves (including benchmark)
elif sys.platform == "win32":
    _PROCESS_NAMES = ("Civ6_Exe_Child.exe", "Civ6_Exe.exe", "CivilizationVI.exe")
    _SAVE_BASE = os.path.expanduser(
        "~/Documents/My Games/Sid Meier's Civilization VI/Saves/Single"
    )
    SAVE_DIR = os.path.join(_SAVE_BASE, "auto")
    SINGLE_SAVE_DIR = _SAVE_BASE
else:
    _PROCESS_NAMES = ()
    SAVE_DIR = ""
    SINGLE_SAVE_DIR = ""

# How long to wait after kill for Steam to deregister the game
_KILL_SETTLE_SECONDS = 10
# How long to wait for game process to appear after launch
_LAUNCH_TIMEOUT_SECONDS = 60
# How long to wait for main menu after process starts
_MAIN_MENU_WAIT_SECONDS = 15


def _require_gui_deps() -> None:
    """Validate GUI dependencies are available, raising clear error if missing."""
    if sys.platform == "win32":
        raise NotImplementedError(
            "Windows GUI automation not yet implemented. "
            "Process management and save discovery work; OCR/click do not."
        )
    if sys.platform != "darwin":
        raise NotImplementedError(f"GUI automation not supported on {sys.platform}")
    try:
        import Quartz  # noqa: F401
        import Vision  # noqa: F401
    except ImportError:
        raise RuntimeError(
            "Game launcher requires pyobjc GUI dependencies. "
            "Install with: uv pip install 'civ6-mcp[launcher-macos]'"
        )


# ---------------------------------------------------------------------------
# Process management (no GUI deps needed)
# ---------------------------------------------------------------------------


def is_game_running() -> bool:
    """Check if Civ 6 is running."""
    if sys.platform == "darwin":
        r = subprocess.run(
            ["pgrep", "-f", _ALLOWED_PROCESS_PATTERNS[0]],
            capture_output=True,
        )
        return r.returncode == 0
    elif sys.platform == "win32":
        for name in _PROCESS_NAMES:
            r = subprocess.run(
                ["tasklist", "/FI", f"IMAGENAME eq {name}", "/NH"],
                capture_output=True,
                text=True,
            )
            if name.lower() in r.stdout.lower():
                return True
        return False
    raise NotImplementedError(f"is_game_running not supported on {sys.platform}")


def _kill_game_sync() -> str:
    """Kill Civ 6 and wait for Steam to deregister. Blocking."""
    if not is_game_running():
        return "Game is not running."

    if sys.platform == "darwin":
        subprocess.run(["pkill", "-9", "-f", "Civ6"], capture_output=True)
    elif sys.platform == "win32":
        for name in _PROCESS_NAMES:
            subprocess.run(["taskkill", "/IM", name, "/F"], capture_output=True)
    else:
        raise NotImplementedError(f"kill not supported on {sys.platform}")
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


def _click_aspyr_launcher_sync() -> str | None:
    """Click PLAY on the Aspyr launcher if it appears (macOS only).

    On macOS, `steam://run/289070` opens the Aspyr LaunchPad — a splash
    screen with a PLAY button — before the actual game binary starts.
    This function detects that screen via OCR and clicks through it.

    Returns None on success, error string on failure.
    """
    if sys.platform != "darwin":
        return None  # no Aspyr launcher on other platforms

    try:
        _require_gui_deps()
    except (RuntimeError, NotImplementedError):
        log.warning("GUI deps not available — cannot auto-click Aspyr launcher")
        return "GUI deps not available. Click PLAY on the Aspyr launcher manually."

    log.info("Waiting for Aspyr launcher PLAY button...")
    if _click_text("PLAY", timeout=30, exact=True, post_delay=3):
        log.info("Clicked PLAY on Aspyr launcher")
        return None

    # Launcher may not appear if game was already past it
    log.info("Aspyr launcher PLAY button not found — may have been skipped")
    return None


def _wait_for_game_process(timeout: int = _LAUNCH_TIMEOUT_SECONDS) -> int | None:
    """Wait for the actual game process to appear. Returns seconds waited, or None."""
    for i in range(timeout):
        if is_game_running():
            log.info("Game process detected after %ds", i)
            return i
        time.sleep(1)
    return None


def _launch_game_sync() -> str:
    """Launch Civ 6 via Steam and wait for process. Blocking.

    On macOS, Steam opens the Aspyr LaunchPad first (a splash screen
    with a PLAY button). This function auto-clicks through it if GUI
    deps are available.
    """
    if is_game_running():
        return "Game is already running."

    if sys.platform == "darwin":
        subprocess.run(["open", f"steam://run/{STEAM_APP_ID}"])
    elif sys.platform == "win32":
        os.startfile(f"steam://run/{STEAM_APP_ID}")  # noqa: S606 — hardcoded Steam URL
    else:
        raise NotImplementedError(f"launch not supported on {sys.platform}")
    log.info("Launched Civ 6 via Steam, waiting for process...")

    # macOS: click through the Aspyr launcher if it appears
    launcher_err = _click_aspyr_launcher_sync()
    if launcher_err:
        return f"WARNING: {launcher_err}"

    # Wait for actual game process
    waited = _wait_for_game_process()
    if waited is None:
        return "WARNING: Game process not detected after launch. Check Steam."

    # Wait for main menu / FireTuner to become reachable
    time.sleep(_MAIN_MENU_WAIT_SECONDS)
    return f"Game launched. Process started after {waited}s, waited {_MAIN_MENU_WAIT_SECONDS}s for main menu."


# ---------------------------------------------------------------------------
# OCR + GUI helpers (require pyobjc)
# ---------------------------------------------------------------------------


def _find_game_window() -> WindowInfo | None:
    """Find the Civ 6 game window via Quartz CGWindowList.

    Returns WindowInfo with window ID, bounds (screen points), and PID.
    Returns None if no matching window is found on screen.
    """
    _require_gui_deps()
    import Quartz

    window_list = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly
        | Quartz.kCGWindowListExcludeDesktopElements,
        Quartz.kCGNullWindowID,
    )
    if not window_list:
        return None

    for w in window_list:
        owner = w.get("kCGWindowOwnerName", "")
        layer = w.get("kCGWindowLayer", -1)
        if layer != 0:
            continue
        if not (
            any(p in owner for p in _PROCESS_NAMES)
            or any(p in owner for p in _APP_NAME_PATTERNS)
        ):
            continue
        bounds = w.get("kCGWindowBounds", {})
        return WindowInfo(
            window_id=w.get("kCGWindowNumber", 0),
            x=int(bounds.get("X", 0)),
            y=int(bounds.get("Y", 0)),
            w=int(bounds.get("Width", 0)),
            h=int(bounds.get("Height", 0)),
            pid=w.get("kCGWindowOwnerPID", 0),
        )
    return None


def _capture_window(window_id: int) -> object:
    """Capture a single window as an in-memory CGImage (no disk I/O).

    Returns a CGImageRef for direct use with Vision framework.
    """
    import Quartz

    image = Quartz.CGWindowListCreateImage(
        Quartz.CGRectNull,
        Quartz.kCGWindowListOptionIncludingWindow,
        window_id,
        Quartz.kCGWindowImageBoundsIgnoreFraming,
    )
    if image is None:
        raise RuntimeError(f"CGWindowListCreateImage failed for window {window_id}")
    return image


def _ocr_vision(
    cg_image: object,
    origin_x: int,
    origin_y: int,
    extent_w: int,
    extent_h: int,
) -> list[tuple[str, int, int, int, int]]:
    """Run Vision OCR on a CGImage, mapping results to screen points.

    Coordinates are mapped using the capture region's known bounds in
    screen points (not retina pixels), making this retina-independent:
        screen_x = origin_x + normalized_center_x * extent_w
        screen_y = origin_y + (1 - norm_y - norm_h/2) * extent_h
    """
    import Vision

    request = Vision.VNRecognizeTextRequest.alloc().init()
    request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
    handler = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(
        cg_image, None
    )
    success, error = handler.performRequests_error_([request], None)
    if not success:
        log.warning("Vision OCR failed: %s", error)
        return []

    results = []
    for obs in request.results() or []:
        text = obs.topCandidates_(1)[0].string()
        bbox = obs.boundingBox()
        # Vision: normalized [0,1], origin bottom-left → screen points
        norm_cx = bbox.origin.x + bbox.size.width / 2
        norm_cy = 1 - bbox.origin.y - bbox.size.height / 2  # flip Y
        sx = origin_x + norm_cx * extent_w
        sy = origin_y + norm_cy * extent_h
        sw = bbox.size.width * extent_w
        sh = bbox.size.height * extent_h
        results.append((text, int(sx), int(sy), int(sw), int(sh)))
    return results


def _ocr_game_window(win: WindowInfo) -> list[tuple[str, int, int, int, int]]:
    """Capture the game window and OCR it. All coords in screen points."""
    cg_image = _capture_window(win.window_id)
    return _ocr_vision(cg_image, win.x, win.y, win.w, win.h)


def _ocr_fullscreen() -> list[tuple[str, int, int, int, int]]:
    """Full-screen OCR fallback for when no game window exists.

    Used during the Aspyr launcher phase before the game process starts.
    Maps via display dimensions in points (retina-independent).
    """
    import Quartz

    main_display = Quartz.CGMainDisplayID()
    display_bounds = Quartz.CGDisplayBounds(main_display)
    disp_w = int(display_bounds.size.width)
    disp_h = int(display_bounds.size.height)

    image = Quartz.CGWindowListCreateImage(
        display_bounds,
        Quartz.kCGWindowListOptionAll,
        Quartz.kCGNullWindowID,
        Quartz.kCGWindowImageDefault,
    )
    if image is None:
        return []

    return _ocr_vision(image, 0, 0, disp_w, disp_h)


def _find_text(
    ocr_results: list[tuple[str, int, int, int, int]],
    target: str,
    exact: bool = False,
    prefer_bottom: bool = False,
) -> tuple[str, int, int, int, int] | None:
    """Find OCR result matching target text.

    Args:
        prefer_bottom: When True and multiple matches exist, return the one
            with the largest y coordinate (lowest on screen). Useful when a
            label and a button have the same text (e.g. "Load Game" title
            at top vs "Load Game" button at bottom).
    """
    target_lower = target.lower().strip()
    matches = []
    for text, x, y, w, h in ocr_results:
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
    """Click at screen coordinates (points)."""
    _require_gui_deps()
    import Quartz

    e = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventMouseMoved, (x, y), 0)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, e)
    time.sleep(0.15)
    e = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDown, (x, y), 0)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, e)
    time.sleep(0.05)
    e = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseUp, (x, y), 0)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, e)


def _is_window_focused() -> bool:
    """Check if a Civ 6 window is the frontmost application (macOS only)."""
    if sys.platform != "darwin":
        return False
    try:
        from AppKit import NSWorkspace

        active = NSWorkspace.sharedWorkspace().frontmostApplication()
        if active is None:
            return False
        name = active.localizedName() or ""
        return any(p in name for p in _PROCESS_NAMES) or any(
            p in name for p in _APP_NAME_PATTERNS
        )
    except ImportError:
        return False


def _bring_to_front(pid: int | None = None) -> None:
    """Bring the game window to front via native AppKit activation.

    Args:
        pid: Process ID from WindowInfo. If None, looks up via
            _find_game_window().
    """
    if sys.platform != "darwin":
        raise NotImplementedError(f"Window focus not supported on {sys.platform}")
    try:
        from AppKit import (
            NSApplicationActivateIgnoringOtherApps,
            NSRunningApplication,
        )
    except ImportError:
        log.warning("AppKit not available for window focus")
        return

    if pid is None:
        win = _find_game_window()
        if win is None:
            log.debug("Cannot bring to front: no game window found")
            return
        pid = win.pid

    app = NSRunningApplication.runningApplicationWithProcessIdentifier_(pid)
    if app is None:
        log.warning("Cannot bring to front: no app with PID %d", pid)
        return

    for attempt in range(3):
        app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)
        time.sleep(0.3)
        if app.isActive():
            return
        if attempt < 2:
            log.debug("Window focus attempt %d failed, retrying...", attempt + 1)
    log.warning("Could not confirm window focus after 3 attempts")


def _wait_for_text(
    target: str,
    timeout: int = 60,
    exact: bool = False,
    interval: int = 3,
    prefer_bottom: bool = False,
) -> tuple[str, int, int, int, int] | None:
    """Wait until OCR finds target text in game window.

    Captures only the game window (not the full screen). Falls back to
    full-screen capture when no game window exists (e.g. Aspyr launcher).
    """
    _require_gui_deps()
    start = time.time()
    while time.time() - start < timeout:
        win = _find_game_window()
        if win is None:
            # No game window yet (Aspyr launcher phase) — full-screen fallback
            log.debug("No game window found, using full-screen OCR")
            results = _ocr_fullscreen()
        else:
            _bring_to_front(pid=win.pid)
            time.sleep(0.3)
            try:
                results = _ocr_game_window(win)
            except RuntimeError:
                log.debug("Window capture failed, retrying...")
                time.sleep(interval)
                continue

        match = _find_text(
            results, target, exact=exact, prefer_bottom=prefer_bottom
        )
        if match:
            return match
        time.sleep(interval)
    return None


def _click_text(
    target: str,
    timeout: int = 30,
    exact: bool = False,
    post_delay: float = 2,
    prefer_bottom: bool = False,
) -> bool:
    """Find text via OCR and click it. Returns success."""
    match = _wait_for_text(
        target, timeout=timeout, exact=exact, prefer_bottom=prefer_bottom
    )
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


def _navigate_to_save_sync(save_name: str, tab: str = "Autosaves") -> str:
    """Navigate: Main Menu → Single Player → Load Game → tab → select → Load.

    Args:
        save_name: Display name of the save (no extension).
        tab: Which tab to click ("Autosaves" — the only tab that shows
            all save types sorted by last modified).

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

    log.info("[3/6] Clicking '%s' tab...", tab)
    if not _click_text(tab, timeout=10, exact=True, post_delay=2):
        log.info("%s tab not found — may already be selected", tab)
        steps.append(f"{tab} tab (may already be selected)")
    else:
        steps.append(f"Clicked {tab} tab")

    log.info("[4/6] Looking for save '%s'...", save_name)
    if not _click_text(save_name, timeout=15, post_delay=2):
        return f"FAILED: Save '{save_name}' not found in {tab} list. Steps completed: {', '.join(steps)}"
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
        save_name: Save name without extension (e.g. "AutoSave_0221" or
            "GROUND_CONTROL_SA"). If None, loads most recent autosave.

    Checks both regular saves and autosaves directories. Uses the
    appropriate tab in the Load Game screen.

    Requires the game to be at the main menu (launched but no game loaded).
    """
    if save_name is None:
        save_name = get_latest_autosave()
        if save_name is None:
            return "No autosaves found in save directory."

    # All saves (autosaves, MCP saves, named saves) appear under the
    # "Autosaves" tab in the Load Game screen, sorted by last modified.
    # There is no separate "Game Saves" tab in the Civ 6 UI.
    auto_path = os.path.join(SAVE_DIR, f"{save_name}.Civ6Save")
    single_path = os.path.join(SINGLE_SAVE_DIR, f"{save_name}.Civ6Save")

    if os.path.exists(auto_path) or os.path.exists(single_path):
        tab = "Autosaves"
    else:
        available = list_autosaves(5)
        # Also list regular saves
        regular = glob.glob(os.path.join(SINGLE_SAVE_DIR, "*.Civ6Save"))
        regular = [os.path.basename(s).replace(".Civ6Save", "") for s in sorted(regular, key=os.path.getmtime, reverse=True)[:5]]
        avail_str = ", ".join(available + regular) if (available or regular) else "none"
        return f"Save '{save_name}' not found. Available: {avail_str}"

    return await asyncio.to_thread(_navigate_to_save_sync, save_name, tab)


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
