import numpy as np
from PIL import Image
import subprocess
import re
from time import sleep
from datetime import datetime
import os
import pyotp
import pyperclip as pc
import random
import time

ld_path = 'F:\\LDPlayer\\LDPlayer9\\'

# determine adb path similar to screenshot: try relative ADB\adb.exe first, then fall back
relative_adb = os.path.join('ADB', 'adb.exe')
adb_path = relative_adb
if not os.path.isfile(adb_path):
    # try inside the LD Player installation directory
    possible_adb = os.path.join(ld_path, 'ADB', 'adb.exe')
    if os.path.isfile(possible_adb):
        adb_path = possible_adb
    else:
        # final fallback directly under ld_path
        adb_path = os.path.join(ld_path, 'adb.exe')

if not os.path.isfile(adb_path):
    print(f"Warning: adb executable not found (tried '{relative_adb}', '{possible_adb if 'possible_adb' in locals() else ''}', '{os.path.join(ld_path,'adb.exe')}')")
else:
    print(f"Using adb at: {adb_path}")

# device id may change; we'll auto-detect from `adb devices`
def get_device_id():
    """Return the first connected emulator device ID or None."""
    try:
        output = subprocess.check_output([adb_path, 'devices'], text=True)
        lines = output.strip().splitlines()[1:]
        for line in lines:
            if line.strip():
                parts = line.split('\t')
                if len(parts) >= 2 and parts[1] == 'device':
                    return parts[0]
    except Exception as e:
        print(f"Error querying adb devices: {e}")
    return None

# initial device lookup
# if no device found, try launching LD Player and connecting

def launch_ldplayer_and_connect():
    """Start LD Player and ensure adb can see it."""
    # try to start emulator process
    try:
        subprocess.Popen([os.path.join(ld_path, 'dnplayer.exe')], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("🚀 Đang khởi chạy LD Player (nếu chưa chạy)...")
    except Exception as e:
        print(f"⚠️ Không thể khởi LD Player: {e}")
    
    # give emulator time to boot (longer because LD Player can be slow)
    boot_wait = 20
    print(f"⏳ Waiting {boot_wait}s for emulator to launch...")
    time.sleep(boot_wait)
    # attempt adb connect (default LD Player port 5555)
    for attempt in range(3):
        try:
            subprocess.call([adb_path, 'connect', '127.0.0.1:5555'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
        # small pause between tries
        time.sleep(2)
    
    # wait for device to appear, allow longer
    for i in range(20):
        d = get_device_id()
        if d:
            return d
        time.sleep(1)
    return None

# initial device lookup
device = get_device_id()
if not device:
    print("⚠️ No adb device found. Is LD Player running and ADB enabled? Trying to start...")
    device = launch_ldplayer_and_connect()
    if device:
        print(f"✅ Detected device after launch: {device}")
    else:
        print("❌ Still no adb device detected")
        device = ''
else:
    print(f"Using adb device: {device}")


def launch_fb_app():
    """Use adb to start the Facebook app on the emulator."""
    if not os.path.isfile(adb_path):
        print(f"Error: adb not found at {adb_path}")
        return False
    if not device:
        print("No valid device ID available - cannot launch app")
        return False
    cmd = f'"{adb_path}" -s {device} shell monkey -p com.facebook.katana -c android.intent.category.LAUNCHER 1'
    try:
        print(f"🔧 Launching Facebook app via adb (device={device})...")
        # retry a few times because emulator might be sluggish
        for attempt in range(3):
            subprocess.call(cmd, shell=True)
            sleep(5)  # give app time to start
            # check if FB process is running
            out = subprocess.check_output([adb_path, '-s', device, 'shell', 'pidof', 'com.facebook.katana'], text=True).strip()
            if out:
                print('✅ Facebook process started')
                return True
            else:
                print(f"   attempt {attempt+1} failed, retrying...")
        print('⚠️ Unable to confirm FB launch after retries')
        return False
    except Exception as e:
        print(f"Failed to launch FB: {e}")
        return False

# gọi hàm
launch_fb_app()

def swipe(device, x1=400, y1=900, x2=400, y2=400, duration=100):
    # Bạn có thể hoàn thiện hàm swipe bằng lệnh adb shell input swipe ở đây
    pass