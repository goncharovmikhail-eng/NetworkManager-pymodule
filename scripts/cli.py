#!/usr/bin/env python3
import argparse
import logging
import sys
import asyncio

from network_module.config import NetworkModule


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )


logger = logging.getLogger(__name__)


async def run_blocking(func, *args):
    return await asyncio.to_thread(func, *args)


async def main():
    parser = argparse.ArgumentParser(description="NetworkManager CLI")

    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("get-profile").add_argument("iface")

    p = sub.add_parser("set-ip")
    p.add_argument("iface")
    p.add_argument("ip")

    p = sub.add_parser("set-prefix")
    p.add_argument("iface")
    p.add_argument("prefix", type=int)

    p = sub.add_parser("set-mask")
    p.add_argument("iface")
    p.add_argument("mask")

    p = sub.add_parser("add-dns")
    p.add_argument("iface")
    p.add_argument("dns")

    sub.add_parser("enable-dhcp").add_argument("iface")
    
    p_edit = sub.add_parser("edit-profile", help="Full profile edit")
    p_edit.add_argument("iface")
    p_edit.add_argument("ip")
    p_edit.add_argument("prefix", help="Prefix (24) or mask (255.255.255.0)")
    p_edit.add_argument("--gw", help="Gateway (optional)", default=None)

    args = parser.parse_args()

    setup_logging()
    nm = NetworkModule()

    try:
        if args.cmd == "get-profile":
            res = await run_blocking(nm.get_profile, args.iface)
            for k, v in res.items():
                logger.info("%s: %s", k, v)

        elif args.cmd == "set-ip":
            await run_blocking(nm.set_ip, args.iface, args.ip)
            logger.info("IP updated")

        elif args.cmd == "set-prefix":
            await run_blocking(nm.set_prefix, args.iface, args.prefix)
            logger.info("Prefix updated")

        elif args.cmd == "set-mask":
            await run_blocking(nm.set_mask, args.iface, args.mask)
            logger.info("Mask updated")

        elif args.cmd == "add-dns":
            await run_blocking(nm.add_dns, args.iface, args.dns)
            logger.info("DNS added")

        elif args.cmd == "enable-dhcp":
            await run_blocking(nm.auto_dhcp, args.iface)
            logger.info("DHCP enabled")

        elif args.cmd == "edit-profile":
            await run_blocking(nm.edit_profile, args.iface, args.ip, args.prefix, args.gw)
            logger.info("Profile updated successfully")

    except Exception as e:
        logger.exception("Error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())