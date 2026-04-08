#!/usr/bin/env python3
import sys
from network_module.config import NetworkModule

if len(sys.argv) < 5:
    print("Usage: python3 -m scripts.cli set-ip <iface> <ip> <prefix> <gateway>")
    sys.exit(1)

cmd = sys.argv[1]
iface = sys.argv[2]
ip = sys.argv[3]
prefix = int(sys.argv[4])
gw = sys.argv[5]

nm = NetworkModule()

if cmd == "set-ip":
    nm.set_ip(iface, ip, prefix, gw)
elif cmd == "enable-dhcp":
    nm.enable_dhcp(iface)
else:
    print("Unknown command:", cmd)
