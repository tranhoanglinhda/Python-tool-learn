import numpy as np
try:
    from PIL import Image
except ImportError:
    Image = None
import subprocess
import re
from time import sleep
from datetime import datetime
import os
import pyotp
try:
    import pyperclip as pc
except ImportError:
    pc = None
import random
import time

# Note: pyperclip is used for clipboard operations. Install with:
#     pip install pyperclip

# Note: PIL (Pillow) is required for image operations. If missing, install via:
#     pip install pillow

ld_path = 'F:\\LDPlayer\\LDPlayer9\\'

try:
    proc = subprocess.Popen([ld_path + 'dnplayer.exe'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    serviceList = proc.stdout.readlines()
except OSError as e:
    if hasattr(e, 'winerror') and e.winerror == 740:
        print("Error: dnplayer.exe requires elevation (run script as Administrator).")
    else:
        print(f"Failed to start dnplayer.exe: {e}")
    serviceList = []

list_ld = []
for i in range(len(serviceList)):
    serviceList[i] = str(serviceList[i])
    serviceList[i] = serviceList[i].split(',')
    if len(serviceList[0]) > 1:
        list_ld.append(serviceList[i][0].split('=')[1])
print(list_ld)

ld_name = 'LDPlayer-0'
subprocess.call([ld_path + 'dnconsole.exe', 'launch', ld_name])