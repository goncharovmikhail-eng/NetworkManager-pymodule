import ipaddress

def _validate_ip(ip, prefix, gw=None):
        ip_obj = ipaddress.ip_address(ip)
        net = ipaddress.ip_network(f"{ip}/{prefix}", strict=False)

        if not ip_obj.is_private:
            raise ValueError(f"{ip} is PUBLIC. Only private networks allowed")

        if ip_obj == net.network_address:
            raise ValueError(f"{ip} is network address") # например 192.168.1.0

        if ip_obj == net.broadcast_address:
            raise ValueError(f"{ip} is broadcast address")

        if gw and ipaddress.ip_address(gw) not in net:
            print(f"WARNING: gateway {gw} not in {net}")

def _validate_prefix(ip, prefix):
    ip_obj = ipaddress.ip_address(ip)

    if prefix == 0:
        raise ValueError("Prefix /0 is not allowed")

    if prefix == 32:
        print("WARNING: /32 = single host")

    private_ranges = [
        ipaddress.ip_network("10.0.0.0/8"),
        ipaddress.ip_network("172.16.0.0/12"),
        ipaddress.ip_network("192.168.0.0/16"),
    ]
 
    for net in private_ranges:
        if ip_obj in net:
            if prefix < net.prefixlen:
                raise ValueError(
                    f"Prefix /{prefix} too small for {net}"
                )
            return

    raise ValueError(f"{ip} not in allowed private ranges")