from gi.repository import GLib
from pydbus import SystemBus
import socket, struct

class NetworkModule:
    def __init__(self):
        self.bus = SystemBus()
        self.nm = self.bus.get("org.freedesktop.NetworkManager",
                               "/org/freedesktop/NetworkManager")
        self.settings = self.bus.get("org.freedesktop.NetworkManager",
                                     "/org/freedesktop/NetworkManager/Settings")

    def _get_connection_path(self, iface_name):
        for path in self.settings.ListConnections():
            conn = self.bus.get("org.freedesktop.NetworkManager", path)
            props = conn.GetSettings()
            if props["connection"]["interface-name"] == iface_name:
                return path
        raise ValueError(f"No connection profile for {iface_name}")

    def get_profile(self, iface_name):
        conn_path = self._get_connection_path(iface_name)
        conn = self.bus.get("org.freedesktop.NetworkManager", conn_path)

        settings = conn.GetSettings()

        ipv4 = settings.get("ipv4", {})
        addr_data = ipv4.get("address-data", [])

        result = {
            "method": ipv4.get("method"),
            "addresses": addr_data,
            "gateway": ipv4.get("gateway"),
            "dns": ipv4.get("dns-data", [])
        }

        return result

    @staticmethod
    def ip2uint(ip):
        return struct.unpack("!I", socket.inet_aton(ip))[0]

    def set_ip_only(self, iface_name, new_ip):
        conn_path = self._get_connection_path(iface_name)
        conn = self.bus.get("org.freedesktop.NetworkManager", conn_path)

        settings = conn.GetSettings()
        ipv4 = settings["ipv4"]

        addr_data = ipv4.get("address-data", [])

        if not addr_data:
            raise ValueError("No address-data found")

        prefix = addr_data[0]["prefix"]

        ipv4["address-data"] = GLib.Variant('aa{sv}', [
            {
                "address": GLib.Variant('s', new_ip),
                "prefix": GLib.Variant('u', prefix)
            }
        ])

        conn.Update(settings)
    
    def set_prefix_only(self, iface_name, new_prefix):
        conn_path = self._get_connection_path(iface_name)
        conn = self.bus.get("org.freedesktop.NetworkManager", conn_path)

        settings = conn.GetSettings()
        ipv4 = settings["ipv4"]

        addr_data = ipv4.get("address-data", [])

        if not addr_data:
            raise ValueError("No address-data found")

        ip = addr_data[0]["address"]

        ipv4["address-data"] = GLib.Variant('aa{sv}', [
            {
                "address": GLib.Variant('s', ip),
                "prefix": GLib.Variant('u', int(new_prefix))
            }
        ])

        conn.Update(settings)

    def add_dns(self, iface_name, dns_ip):
        conn_path = self._get_connection_path(iface_name)
        conn = self.bus.get("org.freedesktop.NetworkManager", conn_path)

        settings = conn.GetSettings()
        ipv4 = settings["ipv4"]

        dns_list = ipv4.get("dns-data", [])

        dns_list.append({
            "address": GLib.Variant('s', dns_ip)
        })

        ipv4["dns-data"] = GLib.Variant('aa{sv}', dns_list)

        conn.Update(settings)

    def enable_dhcp(self, iface_name):
        conn_path = self._get_connection_path(iface_name)
        conn = self.bus.get("org.freedesktop.NetworkManager", conn_path)

        settings = conn.GetSettings()
        settings["ipv4"]["method"] = GLib.Variant('s', "auto")

        conn.Update(settings)


    def disable_dhcp(self, iface_name):
        conn_path = self._get_connection_path(iface_name)
        conn = self.bus.get("org.freedesktop.NetworkManager", conn_path)

        settings = conn.GetSettings()
        settings["ipv4"]["method"] = GLib.Variant('s', "manual")

        conn.Update(settings)

    # def edit_profile(self, iface_name, ip, prefix=24, gw=None):
    #     conn_path = self._get_connection_path(iface_name)
    #     conn = self.bus.get("org.freedesktop.NetworkManager", conn_path)

    #     # Подготавливаем данные. 
    #     # Ключи — обычные строки, значения — Variant-ы нужных типов.
    #     ipv4_data = {
    #         "method": GLib.Variant('s', "manual"),
    #         "address-data": GLib.Variant('aa{sv}', [
    #             {
    #                 "address": GLib.Variant('s', ip),
    #                 "prefix": GLib.Variant('u', int(prefix))
    #             }
    #         ])
    #     }

    #     if gw:
    #         ipv4_data["gateway"] = GLib.Variant('s', gw)

    #     # Собираем итоговый словарь для pydbus.
    #     # Не оборачивайте весь словарь в GLib.Variant вручную!
    #     # pydbus сам упакует этот Python dict в аргумент метода Update.
    #     settings = {
    #         "connection": {
    #             "id": GLib.Variant('s', iface_name),
    #             "type": GLib.Variant('s', "802-3-ethernet"),
    #             "interface-name": GLib.Variant('s', iface_name)
    #         },
    #         "ipv4": ipv4_data,
    #         "ipv6": {
    #             "method": GLib.Variant('s', "ignore")
    #         }
    #     }

    #     # Вызов Update напрямую с обычным словарем (значения внутри — Variant)
    #     conn.Update(settings)

    #     # Активация
    #     self.nm.ActivateConnection(conn_path, "/", "/")

