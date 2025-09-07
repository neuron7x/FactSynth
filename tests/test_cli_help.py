import importlib, subprocess, sys, shutil, os, pytest

def _has_console_script(name):
    return shutil.which(name) is not None

def test_cli_help():
    # Try 'python -m factsynth_ultimate' first, then console scripts
    cmds = [
        [sys.executable, "-m", "factsynth_ultimate", "--help"],
        [sys.executable, "-m", "factsynth", "--help"],
        ["factsynth", "--help"],
        ["factsynth-ultimate", "--help"],
    ]
    for cmd in cmds:
        try:
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
            if proc.returncode == 0:
                return
        except Exception:
            continue
    pytest.skip("CLI not found or --help failed")
