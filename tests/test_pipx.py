"""Verify sptui is registered in pipx after install."""
import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-m", "pipx", "list"],
    text=True,
    capture_output=True,
)
print(result.stdout)
assert "sptui" in result.stdout, f"sptui not found in pipx list:\n{result.stdout}"
print("pipx check OK")
