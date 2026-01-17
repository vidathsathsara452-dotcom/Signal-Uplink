#!/usr/bin/env python3
import os
import socket
import platform
import time
import psutil
import requests
from colorama import Fore, Style, init
import ipaddress

init(autoreset=True)

TOOL_PATH = "/usr/share/Signal-Uplinlk"
BANNER = [] 

banner_file = ""

backup_BANNER = [
r"  _________.__                     .__                                            ",
r" /   _____/|__| ____   ____ _____  |  |                                           ",
r" \_____  \ |  |/ ___\ /    \\__  \ |  |                                           ",
r" /        \|  / /_/  >   |  \/ __ \|  |__                                         ",
r"/_______  /|__\___  /|___|  (____  /____/_____                                    ",
r"        \/   /_____/      \/     \/    /_____/                                    ",
r"                                           ____ ___        .__  .__        __     ",
r"                                          |    |   \______ |  | |__| ____ |  | __",
r"                                          |    |   /\____ \|  | |  |/    \|  |/ /",
r"                                          |    |  / |  |_> >  |_|  |   |  \    < ",
r" _________________________________________|______/  |   __/|____/__|___|  /__|_ \ ",
r"/_____/_____/_____/_____/_____/_____/_____/         |__|                \/     \/ ",
r"",
r"                   SIGNAL UPLINK :: project by Vidath101                          ",
]

banner_file = os.path.join(TOOL_PATH, "banner.txt")

# Use backup if banner.txt doesn't exist
if os.path.exists(banner_file):
    with open(banner_file, "r") as bnfile:
        BANNER = [line.rstrip("\n") for line in bnfile]
else:
    BANNER = backup_BANNER.copy()

# =========================
# Helpers
# =========================
def clear():
    os.system("cls" if os.name == "nt" else "clear")

def public_ip():
    try:
        return requests.get("https://api.ipify.org", timeout=1.2).text
    except:
        return "Unavailable"

def egress_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "Unavailable"

def default_interface():
    try:
        lip = egress_local_ip()
        for iface, addrs in psutil.net_if_addrs().items():
            for a in addrs:
                if a.family == socket.AF_INET and a.address == lip:
                    return iface
        return "Unknown"
    except:
        return "Unavailable"

def default_gateway_ip():
    try:
        with open("/proc/net/route") as f:
            for line in f.readlines()[1:]:
                fields = line.strip().split()
                if fields[1] == "00000000":
                    return socket.inet_ntoa(bytes.fromhex(fields[2])[::-1])
    except:
        pass
    return "Unknown"


def dns_servers():
    servers = []
    try:
        with open("/etc/resolv.conf") as f:
            for line in f:
                if line.startswith("nameserver"):
                    ip = line.split()[1]
                    try:
                        addr = ipaddress.ip_address(ip)
                        if addr.version == 4:
                            servers.append(ip)
                    except:
                        pass
    except:
        pass

    # de-duplicate, preserve order
    servers = list(dict.fromkeys(servers))
    return ", ".join(servers) if servers else "Unknown"

def vpn_status():
    vpns = []
    for iface in psutil.net_if_addrs().keys():
        if iface.startswith(("tun", "wg", "vpn")):
            vpns.append(iface)

    if vpns:
        return Fore.GREEN + "ACTIVE (" + ", ".join(vpns) + ")" + Style.RESET_ALL
    return Fore.RED + "INACTIVE" + Style.RESET_ALL


def iface_list():
    out = []
    stats = psutil.net_if_stats()
    addrs = psutil.net_if_addrs()

    for iface, st in stats.items():
        if iface == "lo":
            continue

        ip = "-"
        for a in addrs.get(iface, []):
            if a.family == socket.AF_INET:
                ip = a.address

        color = Fore.GREEN if st.isup else Fore.RED
        state = "UP" if st.isup else "DOWN"
        out.append(f"{iface} ({color}{state}{Style.RESET_ALL} | {ip})")

    return ", ".join(out)


def uptime():
    secs = int(time.time() - psutil.boot_time())
    h, rem = divmod(secs, 3600)
    m, s = divmod(rem, 60)
    return f"{h}h {m}m {s}s"

def active_connections():
    try:
        return sum(1 for c in psutil.net_connections() if c.status == "ESTABLISHED")
    except:
        return "Unavailable"

def routes_summary():
    try:
        routes = []
        for c in psutil.net_connections(kind="inet"):
            if c.laddr and c.raddr:
                routes.append(f"{c.laddr.ip} -> {c.raddr.ip}")
        return f"{len(routes)} routes"
    except:
        return "Unavailable"

# =========================
# Info Panel
# =========================
INFO = [
    f"{Fore.CYAN}Hostname        {Style.RESET_ALL}: {socket.gethostname()}",
    f"{Fore.CYAN}OS              {Style.RESET_ALL}: {platform.system()} {platform.release()}",
    f"{Fore.CYAN}Architecture    {Style.RESET_ALL}: {platform.machine()}",
    f"{Fore.CYAN}Python Version  {Style.RESET_ALL}: {platform.python_version()}",
    f"{Fore.CYAN}Uptime          {Style.RESET_ALL}: {uptime()}",
    "",
    f"{Fore.GREEN}Public IP       {Style.RESET_ALL}: {public_ip()}",
    f"{Fore.GREEN}Local IP        {Style.RESET_ALL}: {egress_local_ip()}",
    f"{Fore.GREEN}Default IFACE   {Style.RESET_ALL}: {default_interface()}",
    f"{Fore.GREEN}DNS Servers     {Style.RESET_ALL}: {dns_servers()}",
    f"{Fore.GREEN}VPN Status      {Style.RESET_ALL}: {vpn_status()}",
    "",
    f"{Fore.MAGENTA}Interfaces      {Style.RESET_ALL}: {iface_list()}",
    f"{Fore.MAGENTA}Connections     {Style.RESET_ALL}: {active_connections()} ESTABLISHED",
    f"{Fore.MAGENTA}Gateway         {Style.RESET_ALL}: {default_gateway_ip()}",
]

# =========================
# Side-by-side renderer
# =========================
def render(left, right, padding=8):
    maxl = max(len(l) for l in left)
    total = max(len(left), len(right))
    for i in range(total):
        l = left[i] if i < len(left) else ""
        r = right[i] if i < len(right) else ""
        print(Fore.RED + l.ljust(maxl) + " " * padding + Fore.WHITE + r)

# =========================
# Run
# =========================
clear()
render(BANNER, INFO)
