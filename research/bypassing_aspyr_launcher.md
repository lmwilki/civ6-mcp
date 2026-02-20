# Bypassing the Aspyr Launcher for Civilization VI on macOS

## Problem
The Aspyr launcher for Civilization VI adds friction to automated workflows. When launching the game via Steam, a GUI launcher appears requiring manual "PLAY" button click before the game starts.

## Solutions

### Solution 1: Steam Launch Options (RECOMMENDED)

The most reliable method is to configure Steam to launch the game executable directly, bypassing the Aspyr launcher entirely.

#### Method
1. Right-click **Sid Meier's Civilization VI** in your Steam Library
2. Select **Properties** → **General** tab
3. In the **Launch Options** field, paste:

```bash
"/Users/YOUR_USERNAME/Library/Application Support/Steam/steamapps/common/Sid Meier's Civilization VI/Civ6.app/Contents/MacOS/Civ6_Exe_Child" %command%
```

Replace `YOUR_USERNAME` with your macOS username (visible in Finder → Go → Home).

#### How it Works
- `%command%` is a Steam placeholder that gets replaced with the game's normal launch command
- By prepending the direct executable path in quotes, we override the launcher
- The game launches directly in whatever resolution mode was last used (typically fullscreen)

#### Executable Options
You have two choices:
- **`Civ6_Exe_Child`** (60.8 MB) - Child process executable (recommended)
- **`Civ6_Exe`** (8.8 MB) - Parent/launcher executable

Based on community reports, `Civ6_Exe_Child` is more reliable for bypassing the launcher.

#### Verification
```bash
# Check that your username is correct:
whoami

# Verify the executable exists:
ls -la "/Users/$(whoami)/Library/Application Support/Steam/steamapps/common/Sid Meier's Civilization VI/Civ6.app/Contents/MacOS/Civ6_Exe_Child"
```

### Solution 2: Programmatic Steam Config Modification

For automated/scripted setup, you can modify Steam's `localconfig.vdf` file directly.

#### Location
```bash
~/Library/Application Support/Steam/userdata/<user-id>/config/localconfig.vdf
```

Where `<user-id>` is a numeric Steam user ID (usually an 8-9 digit number).

#### Structure
Launch options are stored in the VDF (Valve Data Format) file under:
```
"UserLocalConfigStore"
  "Software"
    "Valve"
      "Steam"
        "Apps"
          "289070"  # Civilization VI App ID
            "LaunchOptions" "<your launch option string>"
```

#### Challenges
1. **Steam doesn't auto-reload** - Changes to `localconfig.vdf` aren't picked up until Steam restarts
2. **Format is finicky** - VDF uses a custom key-value format (not JSON)
3. **Character limit** - macOS has a 262,144 character limit for launch options
4. **Manual reload required** - You can try `steam://flushconfig/` URL scheme to force reload, but this isn't reliable

#### Python Tools
- [steam-localconfig-nix](https://github.com/steamdeckuser/steam-localconfig-nix) uses `steamlc-patcher` (Python with `srctools` library) to parse and modify VDF files
- Primarily developed for Linux but may work on macOS

#### Example Script (Untested)
```python
import os
import subprocess

def set_civ6_launch_option():
    username = os.environ.get("USER")
    steam_userdata = os.path.expanduser("~/Library/Application Support/Steam/userdata")

    # Find the first user ID directory
    user_dirs = [d for d in os.listdir(steam_userdata) if d.isdigit()]
    if not user_dirs:
        raise FileNotFoundError("No Steam user directories found")

    vdf_path = os.path.join(steam_userdata, user_dirs[0], "config", "localconfig.vdf")

    # Read existing VDF
    with open(vdf_path, 'r') as f:
        content = f.read()

    # Modify LaunchOptions for app 289070 (Civ VI)
    # WARNING: This is a naive replacement, not a proper VDF parser
    launch_option = f'"/Users/{username}/Library/Application Support/Steam/steamapps/common/Sid Meier\'s Civilization VI/Civ6.app/Contents/MacOS/Civ6_Exe_Child" %command%'

    # ... VDF modification logic here ...
    # Consider using a proper VDF parsing library

    # Restart Steam to pick up changes
    subprocess.run(["killall", "Steam"])
    subprocess.run(["open", "-a", "Steam"])
```

**Recommendation:** Use Solution 1 (manual Steam UI configuration) unless you have a strong need for automation. The VDF approach is fragile and requires Steam restart.

### Solution 3: Direct Executable Launch (DOES NOT WORK)

Launching the executable directly without Steam **does not work** because:
- Steam's DRM requires the Steam client to be running
- The game needs Steam's overlay and achievement systems
- Networking/multiplayer features require Steam authentication
- The executable expects to be launched as a child process of Steam

```bash
# This will fail:
"/Users/$(whoami)/Library/Application Support/Steam/steamapps/common/Sid Meier's Civilization VI/Civ6.app/Contents/MacOS/Civ6_Exe_Child"
```

### Solution 4: AppleScript/Accessibility API Automation (COMPLEX)

You can automate clicking the "PLAY" button using macOS accessibility APIs, but this is fragile and over-engineered.

#### Requirements
1. Grant **Accessibility** permissions to your script/terminal app:
   - System Settings → Privacy & Security → Accessibility
   - Add Terminal.app or your script runner

2. Use AppleScript with GUI scripting:

```applescript
tell application "System Events"
    tell process "Aspyr Launcher" -- or whatever the process name is
        -- Wait for the window to appear
        repeat until exists window 1
            delay 0.5
        end repeat

        -- Click the PLAY button
        -- You'll need to identify the button by its accessibility description
        click (first button where its accessibility description = "PLAY")
    end repeat
end tell
```

#### Challenges
1. **Process name may vary** - Need to identify the launcher process name
2. **Button identification** - Need to use Accessibility Inspector (part of Xcode) to find the button's properties
3. **Timing issues** - Must wait for launcher to fully load
4. **Brittle** - Breaks if Aspyr updates the launcher UI
5. **Screen recording permission** - May require Screen Recording permission in addition to Accessibility

#### Tools
- **Accessibility Inspector** - Part of Xcode (free from Mac App Store)
- **UI Browser** - Third-party tool for exploring UI element hierarchy
- **AppleScript Editor** - Built into macOS (/Applications/Utilities/)

**Recommendation:** Avoid this approach. Use Solution 1 instead.

### Solution 5: Command-Line Flags (NOT AVAILABLE)

Unfortunately, Civilization VI does **not** expose command-line flags for:
- `--skip-launcher` or `--nolaunch`
- `--autoplay`
- DirectX/Vulkan API selection (macOS uses Metal by default)

The game does support **debug mode** but this requires editing `AppOptions.txt`:
```
EnableDebugMenu 1
```

This enables the in-game debug console (backtick key), but does not affect launcher behavior.

### Solution 6: Environment Variables (NOT AVAILABLE)

There are **no known environment variables** that bypass the Aspyr launcher. The launcher does not check for:
- `SKIP_LAUNCHER=1`
- `ASPYR_NOLAUNCH=1`
- `NO_LAUNCHER=1`

## Recommended Workflow

For automated/scripted game launching:

1. **One-time setup:** Configure Steam launch options (Solution 1)
2. **Launch via Steam URL scheme:**
   ```bash
   open "steam://rungameid/289070"
   ```
   This launches the game with your configured launch options, bypassing the launcher.

3. **Wait for FireTuner port:**
   ```python
   import socket
   import time

   def wait_for_firetuner(host="127.0.0.1", port=4318, timeout=60):
       """Wait for Civ6 FireTuner port to become available."""
       start = time.time()
       while time.time() - start < timeout:
           try:
               with socket.create_connection((host, port), timeout=1):
                   return True
           except (socket.timeout, ConnectionRefusedError):
               time.sleep(1)
       return False

   if wait_for_firetuner():
       print("Game ready!")
   else:
       print("Timeout waiting for game to start")
   ```

4. **Connect to FireTuner and start playing**

## Testing

After configuring launch options, test the behavior:

```bash
# Launch via Steam URL scheme
open "steam://rungameid/289070"

# The game should launch directly to fullscreen without showing the Aspyr launcher
```

## Known Issues

1. **First launch after restart** - Sometimes the first launch still shows the launcher; subsequent launches work correctly
2. **Updates may reset** - Steam updates to Civilization VI may clear launch options; check after updates
3. **DLC compatibility** - Launch options should work with all DLC (Gathering Storm, Rise and Fall, etc.)

## References

- [Steam Community Guide: Bypass Aspyr Launcher](https://steamcommunity.com/sharedfiles/filedetails/?id=2786273741)
- [MacGameStore Support: Civilization VI Full Screen](https://macgamestore.zendesk.com/hc/en-us/articles/36447427227159-Civilization-VI-Run-in-Full-Screen-on-macOS)
- [CivFanatics: How to bypass the launcher](https://forums.civfanatics.com/threads/how-to-bypass-the-stupid-launcher.639325/)
- [Steam Support: Setting Game Launch Options](https://help.steampowered.com/en/faqs/view/7D01-D2DD-D75E-2955)
- [Apple Developer: Mac Automation Scripting Guide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/AutomatetheUserInterface.html)
- [macOS Automation: GUI Scripting](https://macosxautomation.com/mavericks/guiscripting/index.html)

## Conclusion

**Use Solution 1 (Steam Launch Options)** for a clean, reliable bypass that works across Steam client restarts and doesn't require fragile automation.

For fully automated workflows, combine Solution 1 with the Steam URL scheme (`open "steam://rungameid/289070"`) and wait for the FireTuner port to become available before connecting.
