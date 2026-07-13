import subprocess
import os
import sys

def start_warp():
    try:
        print("[WARP] Starting Cloudflare WARP...")
        
        result = subprocess.run(["which", "warp-cli"], capture_output=True, timeout=5)
        if result.returncode != 0:
            print("[WARP] warp-cli not installed, skipping")
            return False
        
        subprocess.run(["warp-cli", "registration", "new"], capture_output=True, timeout=15)
        subprocess.run(["warp-cli", "mode", "proxy"], capture_output=True, timeout=5)
        subprocess.run(["warp-cli", "proxy", "port", "40000"], capture_output=True, timeout=5)
        subprocess.run(["warp-cli", "connect"], capture_output=True, timeout=5)
        
        import time
        time.sleep(5)
        
        result = subprocess.run(
            ["curl", "-s", "--proxy", "socks5://127.0.0.1:40000", "--max-time", "10", "https://ifconfig.me"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0 and result.stdout.strip():
            print(f"[WARP] OK - New IP: {result.stdout.strip()}")
            return True
        else:
            print("[WARP] Connection test failed")
            return False
    except Exception as e:
        print(f"[WARP] Not available: {e}")
        return False

print("=" * 50)
print("Starting Melody20 Bot...")
print("=" * 50)

warp_ok = start_warp()
if warp_ok:
    os.environ["WARP_PROXY"] = "socks5://127.0.0.1:40000"
else:
    os.environ["WARP_PROXY"] = ""
    print("[INFO] Running without proxy")

from bot import main
main()
