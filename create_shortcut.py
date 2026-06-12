import sys
import subprocess
from pathlib import Path


def main():
    app_dir  = Path(__file__).parent.resolve()
    main_py  = app_dir / "main.py"
    desktop  = Path.home() / "Desktop"
    shortcut = desktop / "LyricOverlay.lnk"

    pythonw = Path(sys.executable).parent / "pythonw.exe"
    if not pythonw.exists():
        pythonw = Path(sys.executable)

    ps = f"""
$ws = New-Object -ComObject WScript.Shell
$s  = $ws.CreateShortcut('{shortcut}')
$s.TargetPath       = '{pythonw}'
$s.Arguments        = '"{main_py}"'
$s.WorkingDirectory = '{app_dir}'
$s.Description      = 'LyricOverlay'
$s.Save()
"""
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps],
        capture_output=True, text=True,
    )

    if result.returncode == 0:
        print(f"Shortcut created at: {shortcut}")
        print("Double-click LyricOverlay on your desktop to launch it.")
    else:
        print("Failed:")
        print(result.stderr)

    input("\nPress Enter to close…")


if __name__ == "__main__":
    main()
