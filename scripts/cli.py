#!/usr/bin/env python3
import argparse
import logging
import sys
import asyncio

from network_module.config import NetworkModule


# -----------------------------
# Logging setup
# -----------------------------
def setup_logging(verbose: bool):
    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S"
    )


logger = logging.getLogger(__name__)


# -----------------------------
# Async wrappers
# -----------------------------
async def run_blocking(func, *args):
    return await asyncio.to_thread(func, *args)


# -----------------------------
# Main async CLI
# -----------------------------
async def async_main():
    parser = argparse.ArgumentParser(
        description="Async NetworkManager CLI (dbus)"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # -----------------------------
    # get-profile
    # -----------------------------
    p_get = subparsers.add_parser("get-profile")
    p_get.add_argument("iface")

    # -----------------------------
    # set-ip
    # -----------------------------
    p_ip = subparsers.add_parser("set-ip")
    p_ip.add_argument("iface")
    p_ip.add_argument("ip")

    # -----------------------------
    # set-prefix
    # -----------------------------
    p_prefix = subparsers.add_parser("set-prefix")
    p_prefix.add_argument("iface")
    p_prefix.add_argument("prefix", type=int)

    # -----------------------------
    # add-dns
    # -----------------------------
    p_dns = subparsers.add_parser("add-dns")
    p_dns.add_argument("iface")
    p_dns.add_argument("dns")

    # -----------------------------
    # DHCP
    # -----------------------------
    p_dhcp_on = subparsers.add_parser("enable-dhcp")
    p_dhcp_on.add_argument("iface")

    p_dhcp_off = subparsers.add_parser("disable-dhcp")
    p_dhcp_off.add_argument("iface")

    args = parser.parse_args()

    setup_logging(args.verbose)

    nm = NetworkModule()

    try:
        if args.command == "get-profile":
            profile = await run_blocking(nm.get_profile, args.iface)
            logger.info("Profile for %s:", args.iface)
            for k, v in profile.items():
                logger.info("  %s: %s", k, v)

        elif args.command == "set-ip":
            await run_blocking(nm.set_ip, args.iface, args.ip)
            logger.info("IP updated for %s -> %s", args.iface, args.ip)

        elif args.command == "set-prefix":
            await run_blocking(nm.set_prefix, args.iface, args.prefix)
            logger.info("Prefix updated for %s -> /%s", args.iface, args.prefix)

        elif args.command == "add-dns":
            await run_blocking(nm.add_dns, args.iface, args.dns)
            logger.info("DNS %s added to %s", args.dns, args.iface)

        elif args.command == "enable-dhcp":
            await run_blocking(nm.enable_dhcp, args.iface)
            logger.info("DHCP enabled on %s", args.iface)

        elif args.command == "disable-dhcp":
            await run_blocking(nm.disable_dhcp, args.iface)
            logger.info("DHCP disabled on %s", args.iface)

    except Exception as e:
        logger.error("Operation failed: %s", e)
        if args.verbose:
            logger.exception("Stack trace:")
        sys.exit(1)


# -----------------------------
# Entry point
# -----------------------------
def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()