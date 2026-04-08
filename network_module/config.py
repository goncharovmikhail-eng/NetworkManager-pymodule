from gi.repository import GLib
from pydbus import SystemBus
import ipaddress


class NetworkModule:
    def __init__(self):
        self.bus = SystemBus()
        self.nm = self.bus.get(
            "org.freedesktop.NetworkManager",
            "/org/freedesktop/NetworkManager"
        )
        self.settings = self.bus.get(
            "org.freedesktop.NetworkManager",
            "/org/freedesktop/NetworkManager/Settings"
        )

    # -----------------------------
    # Internal helpers
    # -----------------------------

    def _get_connection_path(self, iface_name):
        for path in self.settings.ListConnections():
            conn = self.bus.get("org.freedesktop.NetworkManager", path)
            props = conn.GetSettings()
            if props["connection"]["interface-name"] == iface_name:
                return path
        raise ValueError(f"No connection profile for {iface_name}")

    def _get_conn(self, iface_name):
        path = self._get_connection_path(iface_name)
        return self.bus.get("org.freedesktop.NetworkManager", path), path

    def _unpack(self, value):
        if isinstance(value, GLib.Variant):
            return value.unpack()
        return value

    def _get_ipv4(self, settings):
        return settings.setdefault("ipv4", {})

    def _get_address_data(self, ipv4):
        return ipv4.get("address-data", [])

    def _extract_ip_prefix(self, addr_data):
        if not addr_data:
            raise ValueError("No address-data found")
        entry = addr_data[0]
        ip = self._unpack(entry["address"])
        prefix = self._unpack(entry["prefix"])
        return ip, prefix

    def _validate_ip(self, ip):
        ipaddress.ip_address(ip)

    def _validate_ip_gw(self, ip, prefix, gw):
        if not gw:
            return
        gw = self._unpack(gw)
        net = ipaddress.ip_network(f"{ip}/{prefix}", strict=False)
        if ipaddress.ip_address(gw) not in net:
            raise ValueError(f"Gateway {gw} not in subnet {net}")

    def _set_address_data(self, ipv4, ip, prefix):
        ipv4["address-data"] = GLib.Variant('aa{sv}', [
            {
                "address": GLib.Variant('s', ip),
                "prefix": GLib.Variant('u', int(prefix))
            }
        ])

    def _update_connection(self, conn, settings, path):
        conn.Update(settings)
        self.nm.ActivateConnection(path, "/", "/")

    # -----------------------------
    # Public API
    # -----------------------------

    def get_profile(self, iface_name):
        conn, _ = self._get_conn(iface_name)
        settings = conn.GetSettings()

        ipv4 = settings.get("ipv4", {})

        return {
            "method": self._unpack(ipv4.get("method")),
            "addresses": ipv4.get("address-data", []),
            "gateway": self._unpack(ipv4.get("gateway")),
            "dns": ipv4.get("dns-data", [])
        }

    def set_ip_only(self, iface_name, new_ip):
        self._validate_ip(new_ip)

        conn, path = self._get_conn(iface_name)
        settings = conn.GetSettings()

        ipv4 = self._get_ipv4(settings)
        addr_data = self._get_address_data(ipv4)

        ip, prefix = self._extract_ip_prefix(addr_data)
        gw = ipv4.get("gateway")

        self._validate_ip_gw(new_ip, prefix, gw)

        ipv4["method"] = GLib.Variant('s', "manual")
        self._set_address_data(ipv4, new_ip, prefix)

        self._update_connection(conn, settings, path)

    def set_prefix_only(self, iface_name, new_prefix):
        conn, path = self._get_conn(iface_name)
        settings = conn.GetSettings()

        ipv4 = self._get_ipv4(settings)
        addr_data = self._get_address_data(ipv4)

        ip, _ = self._extract_ip_prefix(addr_data)
        gw = ipv4.get("gateway")

        self._validate_ip_gw(ip, new_prefix, gw)

        ipv4["method"] = GLib.Variant('s', "manual")
        self._set_address_data(ipv4, ip, new_prefix)

        self._update_connection(conn, settings, path)

    def add_dns(self, iface_name, dns_ip):
        conn_path = self._get_connection_path(iface_name)
        conn = self.bus.get("org.freedesktop.NetworkManager", conn_path)
        settings = conn.GetSettings()
        ipv4 = settings["ipv4"]

        # Собираем текущие DNS в список строк
        dns_list = [d["address"].unpack() for d in ipv4.get("dns-data", [])]
        dns_list.append(dns_ip)

        # Перезаписываем dns-data с правильным форматом GLib.Variant
        ipv4["dns-data"] = GLib.Variant('aa{sv}', [
            {"address": GLib.Variant('s', d)} for d in dns_list
        ])

        # Обновляем профиль
        self._update_connection(conn, settings, conn_path)

    def enable_dhcp(self, iface_name):
        conn, path = self._get_conn(iface_name)
        settings = conn.GetSettings()

        ipv4 = self._get_ipv4(settings)
        ipv4["method"] = GLib.Variant('s', "auto")

        self._update_connection(conn, settings, path)

    def disable_dhcp(self, iface_name):
        conn, path = self._get_conn(iface_name)
        settings = conn.GetSettings()

        ipv4 = self._get_ipv4(settings)
        ipv4["method"] = GLib.Variant('s', "manual")

        self._update_connection(conn, settings, path)