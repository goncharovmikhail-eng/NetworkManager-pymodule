import dbus
import socket
import struct
import ipaddress
import threading


class NetworkModule:
    def __init__(self):
        self.bus = dbus.SystemBus()
        self.nm_service = 'org.freedesktop.NetworkManager'

        self.nm_obj = self.bus.get_object(
            self.nm_service,
            '/org/freedesktop/NetworkManager'
        )
        self.nm = dbus.Interface(self.nm_obj, 'org.freedesktop.NetworkManager')

    # =========================
    # INTERNAL HELPERS
    # =========================

    def _get_conn(self, iface):
        settings_obj = self.bus.get_object(
            self.nm_service,
            '/org/freedesktop/NetworkManager/Settings'
        )
        settings = dbus.Interface(
            settings_obj,
            'org.freedesktop.NetworkManager.Settings'
        )

        for path in settings.ListConnections():
            obj = self.bus.get_object(self.nm_service, path)
            conn = dbus.Interface(
                obj,
                'org.freedesktop.NetworkManager.Settings.Connection'
            )
            cfg = conn.GetSettings()

            if cfg.get('connection', {}).get('interface-name') == iface:
                return conn, path

        raise ValueError(f"Interface {iface} not found")

    def _ip_to_u32(self, ip):
        return struct.unpack("!I", socket.inet_aton(ip))[0]

    def _u32_to_ip(self, val):
        return socket.inet_ntoa(struct.pack("!I", int(val)))

    def _netmask_to_prefix(self, mask):
        return ipaddress.IPv4Network(f"0.0.0.0/{mask}").prefixlen

    def _validate(self, ip, prefix, gw=None):
        ip_obj = ipaddress.ip_address(ip)
        net = ipaddress.ip_network(f"{ip}/{prefix}", strict=False)

        if ip_obj == net.network_address:
            raise ValueError(f"{ip} is network address")

        if ip_obj == net.broadcast_address:
            raise ValueError(f"{ip} is broadcast address")

        if gw and ipaddress.ip_address(gw) not in net:
            raise ValueError(f"Gateway {gw} not in {net}")

    def _update(self, conn, path, ipv4):
        settings = conn.GetSettings()
        settings['ipv4'] = ipv4

        conn.Update(settings)
        if hasattr(conn, 'Save'):
            conn.Save()

        self.nm.ActivateConnection(path, "/", "/")

    def _prepare_ipv4(self, old, **kwargs):
        ipv4 = dbus.Dictionary({}, signature='sv')

        # method
        ipv4['method'] = dbus.String(
            kwargs.get('method', old.get('method', 'manual')),
            variant_level=1
        )

        # gateway
        gw = kwargs.get('gateway', old.get('gateway'))
        if gw:
            ipv4['gateway'] = dbus.String(str(gw), variant_level=1)

        # DNS
        dns = kwargs.get('dns', old.get('dns', []))
        ipv4['dns'] = dbus.Array(
            [dbus.UInt32(self._ip_to_u32(str(d))) for d in dns],
            signature='u',
            variant_level=1
        )

        # address-data
        if 'ip' in kwargs and 'prefix' in kwargs:
            entry = dbus.Dictionary({
                'address': dbus.String(kwargs['ip'], variant_level=1),
                'prefix': dbus.UInt32(int(kwargs['prefix']), variant_level=1)
            }, signature='sv')

            ipv4['address-data'] = dbus.Array([entry], signature='a{sv}')

        else:
            addr_data = old.get('address-data', [])
            arr = dbus.Array([], signature='a{sv}')

            for a in addr_data:
                arr.append(dbus.Dictionary({
                    'address': dbus.String(str(a['address']), variant_level=1),
                    'prefix': dbus.UInt32(int(a['prefix']), variant_level=1)
                }, signature='sv'))

            ipv4['address-data'] = arr

        return ipv4

    # =========================
    # PUBLIC API
    # =========================

    def get_profile(self, iface):
        conn, _ = self._get_conn(iface)
        s = conn.GetSettings()
        ipv4 = s.get('ipv4', {})

        return {
            "method": str(ipv4.get('method', '')),
            "gateway": str(ipv4.get('gateway', '')),
            "dns": [self._u32_to_ip(x) for x in ipv4.get('dns', [])],
            "addresses": [
                f"{a['address']}/{a['prefix']}"
                for a in ipv4.get('address-data', [])
            ]
        }

    def set_ip(self, iface, ip):
        conn, path = self._get_conn(iface)
        s = conn.GetSettings()
        ipv4_old = s.get('ipv4', {})

        prefix = int(ipv4_old.get('address-data', [{}])[0].get('prefix', 24))
        gw = ipv4_old.get('gateway')

        self._validate(ip, prefix, gw)

        ipv4 = self._prepare_ipv4(ipv4_old, ip=ip, prefix=prefix)

        self._update(conn, path, ipv4)

    def set_prefix(self, iface, prefix):
        conn, path = self._get_conn(iface)
        s = conn.GetSettings()
        ipv4_old = s.get('ipv4', {})

        ip = str(ipv4_old['address-data'][0]['address'])
        gw = ipv4_old.get('gateway')

        self._validate(ip, prefix, gw)

        ipv4 = self._prepare_ipv4(ipv4_old, ip=ip, prefix=prefix)

        self._update(conn, path, ipv4)

    def set_mask(self, iface, mask):
        prefix = self._netmask_to_prefix(mask)
        self.set_prefix(iface, prefix)

    def add_dns(self, iface, dns_ip):
        conn, path = self._get_conn(iface)
        s = conn.GetSettings()
        ipv4_old = s.get('ipv4', {})

        dns = [self._u32_to_ip(x) for x in ipv4_old.get('dns', [])]

        if dns_ip not in dns:
            dns.append(dns_ip)

        ipv4 = self._prepare_ipv4(ipv4_old, dns=dns)

        self._update(conn, path, ipv4)

    def enable_dhcp(self, iface):
        conn, path = self._get_conn(iface)
        s = conn.GetSettings()
        ipv4_old = s.get('ipv4', {})

        ipv4 = self._prepare_ipv4(ipv4_old, method='auto')

        self._update(conn, path, ipv4)

    # =========================
    # ASYNC LAYER
    # =========================

    def _async(self, func, callback, *args):
        def run():
            try:
                res = func(*args)
                if callback:
                    callback(True, res, None)
            except Exception as e:
                if callback:
                    callback(False, None, e)

        threading.Thread(target=run, daemon=True).start()

    def set_ip_async(self, iface, ip, callback=None):
        self._async(self.set_ip, callback, iface, ip)

    def set_prefix_async(self, iface, prefix, callback=None):
        self._async(self.set_prefix, callback, iface, prefix)

    def add_dns_async(self, iface, dns, callback=None):
        self._async(self.add_dns, callback, iface, dns)

    def enable_dhcp_async(self, iface, callback=None):
        self._async(self.enable_dhcp, callback, iface)