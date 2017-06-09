#!/usr/bin/python3

import os
import xapp.os

flag_path = os.path.expanduser("~/.linuxmint/mintwelcome/norun.flag")

if (not os.path.exists(flag_path)) and (not xapp.os.is_live_session()) and (not xapp.os.is_guest_session()):
    os.system("mintwelcome")
