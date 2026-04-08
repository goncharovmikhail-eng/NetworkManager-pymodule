import dbus

class NetworkModule:
    def __init__(self):
        # Подключение к D-Bus system bus
        self.bus = dbus.SystemBus()
        self.nm_proxy = self.bus.get_object(
            "org.freedesktop.NetworkManager",
            "/org/freedesktop/NetworkManager"
        )
        self.nm = dbus.Interface(self.nm_proxy, "org.freedesktop.NetworkManager")

    def _get_connection_path(self, iface_name):
        # Получаем путь соединения по имени интерфейса
        connections = self.nm.ListConnections()
        for path in connections:
            conn_proxy = self.bus.get_object("org.freedesktop.NetworkManager", path)
            settings = dbus.Interface(conn_proxy, "org.freedesktop.NetworkManager.Settings.Connection")
            settings_dict = settings.GetSettings()
            if settings_dict["connection"]["id"] == iface_name:
                return path
        raise ValueError(f"Interface {iface_name} not found")

    def set_ip(self, iface_name, ip_addr, prefix=24):
        path = self._get_connection_path(iface_name)
        conn_proxy = self.bus.get_object("org.freedesktop.NetworkManager", path)
        settings = dbus.Interface(conn_proxy, "org.freedesktop.NetworkManager.Settings.Connection")
        s = settings.GetSettings()
        s["ipv4"]["method"] = "manual"
        s["ipv4"]["address-data"] = [{"address": ip_addr, "prefix": prefix}]
        settings.Update(s)

    def set_netmask(self, iface_name, prefix):
        # просто обновляем префикс подсети
        path = self._get_connection_path(iface_name)
        conn_proxy = self.bus.get_object("org.freedesktop.NetworkManager", path)
        settings = dbus.Interface(conn_proxy, "org.freedesktop.NetworkManager.Settings.Connection")
        s = settings.GetSettings()
        if "address-data" in s["ipv4"] and s["ipv4"]["address-data"]:
            s["ipv4"]["address-data"][0]["prefix"] = prefix
        settings.Update(s)

    def set_gateway(self, iface_name, gateway):
        path = self._get_connection_path(iface_name)
        conn_proxy = self.bus.get_object("org.freedesktop.NetworkManager", path)
        settings = dbus.Interface(conn_proxy, "org.freedesktop.NetworkManager.Settings.Connection")
        s = settings.GetSettings()
        s["ipv4"]["gateway"] = gateway
        settings.Update(s)

    def set_dns(self, iface_name, dns_list):
        path = self._get_connection_path(iface_name)
        conn_proxy = self.bus.get_object("org.freedesktop.NetworkManager", path)
        settings = dbus.Interface(conn_proxy, "org.freedesktop.NetworkManager.Settings.Connection")
        s = settings.GetSettings()
        s["ipv4"]["method"] = "manual"
        s["ipv4"]["dns"] = dns_list
        settings.Update(s)

    def enable_dhcp(self, iface_name):
        path = self._get_connection_path(iface_name)
        conn_proxy = self.bus.get_object("org.freedesktop.NetworkManager", path)
        settings = dbus.Interface(conn_proxy, "org.freedesktop.NetworkManager.Settings.Connection")
        s = settings.GetSettings()
        s["ipv4"]["method"] = "auto"
        settings.Update(s)

        # Получение текущих настроек
        active_connections = self.nm.ActiveConnections()
        for ac_path in active_connections:
            ac_proxy = self.bus.get_object("org.freedesktop.NetworkManager", ac_path)
            ac_iface = dbus.Interface(ac_proxy, "org.freedesktop.NetworkManager.Connection.Active")
            conn_id = ac_iface.Id()
            if conn_id == iface_name:
                ip4_config_path = ac_iface.Ip4Config()
                ip4_proxy = self.bus.get_object("org.freedesktop.NetworkManager", ip4_config_path)
                ip4 = dbus.Interface(ip4_proxy, "org.freedesktop.NetworkManager.IP4Config")
                addresses = ip4.Addresses()
                gateway = ip4.Gateway()
                nameservers = ip4.Nameservers()
                return {
                    "ip": addresses,
                    "gateway": gateway,
                    "dns": nameservers,
                    "dhcp": True
                }
        return {}
