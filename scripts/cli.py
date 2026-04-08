#!/usr/bin/env python3
import argparse
from network_module.config import NetworkModule


def main():
    parser = argparse.ArgumentParser(
        description="Simple NetworkManager CLI (pydbus)"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # -----------------------------
    # get-profile
    # -----------------------------
    p_get = subparsers.add_parser("get-profile", help="Show interface profile")
    p_get.add_argument("iface")

    # -----------------------------
    # set-ip
    # -----------------------------
    p_ip = subparsers.add_parser("set-ip", help="Set only IP")
    p_ip.add_argument("iface")
    p_ip.add_argument("ip")

    # -----------------------------
    # set-prefix
    # -----------------------------
    p_prefix = subparsers.add_parser("set-prefix", help="Set only prefix")
    p_prefix.add_argument("iface")
    p_prefix.add_argument("prefix", type=int)

    # -----------------------------
    # add_dns
    # -----------------------------
    p_dns = subparsers.add_parser("add_dns", help="Add DNS server")
    p_dns.add_argument("iface")
    p_dns.add_argument("dns")

    # -----------------------------
    # DHCP
    # -----------------------------
    p_dhcp_on = subparsers.add_parser("enable-dhcp", help="Enable DHCP")
    p_dhcp_on.add_argument("iface")

    p_dhcp_off = subparsers.add_parser("disable-dhcp", help="Disable DHCP")
    p_dhcp_off.add_argument("iface")

    args = parser.parse_args()
    nm = NetworkModule()

    # -----------------------------
    # Commands
    # -----------------------------
    if args.command == "get-profile":
        profile = nm.get_profile(args.iface)
        print(profile)

    elif args.command == "set-ip":
        nm.set_ip_only(args.iface, args.ip)
        print(f"IP updated for {args.iface}")

    elif args.command == "set-prefix":
        nm.set_prefix_only(args.iface, args.prefix)
        print(f"Prefix updated for {args.iface}")

    elif args.command == "add_dns":
        nm.add_dns(args.iface, args.dns)
        print(f"DNS {args.dns} added to {args.iface}")

    elif args.command == "enable-dhcp":
        nm.enable_dhcp(args.iface)
        print(f"DHCP enabled on {args.iface}")

    elif args.command == "disable-dhcp":
        nm.disable_dhcp(args.iface)
        print(f"DHCP disabled on {args.iface}")


if __name__ == "__main__":
    main()