import dbus
import threading
import ipaddress

from network_module.helpers import NMHelpers
from .validation import _validate_ip, _validate_prefix

class NetworkModule:
    def __init__(self):
        self.bus = dbus.SystemBus()
        self.nm_service = 'org.freedesktop.NetworkManager'

        self.nm_obj = self.bus.get_object(
            self.nm_service,
            '/org/freedesktop/NetworkManager'
        )
        self.nm = dbus.Interface(self.nm_obj, 'org.freedesktop.NetworkManager')
        self.helpers = NMHelpers(self.nm, self.bus, self.nm_service)

    def get_profile(self, iface):
        self.helpers.ensure_managed(iface)

        conn, _ = self.helpers.get_conn(iface)
        s = conn.GetSettings()
        ipv4 = s.get('ipv4', {})

        return {
            "method": str(ipv4.get('method', '')),
            "gateway": str(ipv4.get('gateway', '')),
            "dns": [self.helpers._u32_to_ip(x) for x in ipv4.get('dns', [])],
            "addresses": [
                f"{a['address']}/{a['prefix']}"
                for a in ipv4.get('address-data', [])
            ]
        }


    def set_ip(self, iface, ip):
        self.helpers.ensure_managed(iface)

        if self.helpers.is_default_interface(iface):
            print(f"WARNING: {iface} is default route interface! ")

        conn, path = self.helpers.get_conn(iface)
        s = conn.GetSettings()
        old = s.get('ipv4', {})

        addr_data = old.get('address-data', [])

        if not addr_data:
            prefix = 24
        else:
            prefix = int(addr_data[0].get('prefix', 24))

        gw = old.get('gateway')

        _validate_ip(ip, prefix, gw)

        ipv4 = self.helpers._prepare_ipv4(old, ip=ip, prefix=prefix)
        self.helpers.update(conn, path, iface, ipv4)
    
    def set_prefix(self, iface, prefix):
        self.helpers.ensure_managed(iface)

        if isinstance(prefix, str) and "." in prefix:
            prefix = self.helpers.mask_to_prefix(prefix)
        else:
            prefix = int(prefix)

        conn, path = self.helpers.get_conn(iface)
        s = conn.GetSettings()
        old = s.get('ipv4', {})

        addr_data = old.get('address-data', [])

        if not addr_data:
            raise ValueError("No IP configured. Set IP first.")

        ip = str(addr_data[0]['address'])
        gw = old.get('gateway')

        _validate_prefix(ip, prefix)
        #_validate_ip(ip, prefix, gw)

        ipv4 = self.helpers._prepare_ipv4(old, ip=ip, prefix=prefix)
        self.helpers.update(conn, path, iface, ipv4)

    def add_dns(self, iface, dns_ip):
        self.helpers.ensure_managed(iface)
        ipaddress.ip_address(dns_ip)

        conn, path = self.helpers.get_conn(iface)
        s = conn.GetSettings()
        old = s.get('ipv4', {})

        dns = [self.helpers._u32_to_ip(x) for x in old.get('dns', [])]

        if dns_ip in dns:
            print(f"WARNING: DNS {dns_ip} already exists")
            return

        dns.append(dns_ip)

        ipv4 = self.helpers._prepare_ipv4(old, dns=dns)
        self.helpers.update(conn, path, iface, ipv4)

    def auto_dhcp(self, iface):
        self.helpers.ensure_managed(iface)

        conn, path = self.helpers.get_conn(iface)

        ipv4 = dbus.Dictionary({}, signature='sv')
        ipv4['method'] = dbus.String('auto', variant_level=1)

        self.helpers.update(conn, path, iface, ipv4)
    
    def edit_profile(self, iface, ip, prefix=24, gw=None):
        self.helpers.ensure_managed(iface)

        if self.helpers.is_default_interface(iface):
            print(f"WARNING: {iface} is default route interface!")

        conn, path = self.helpers.get_conn(iface)

        if isinstance(prefix, str) and "." in prefix:
            prefix = self.helpers.mask_to_prefix(prefix)
        else:
            prefix = int(prefix)

        _validate_prefix(ip, prefix)
        _validate_ip(ip, prefix, gw)

        settings = conn.GetSettings()
        old = settings.get('ipv4', {})

        ipv4 = self.helpers._prepare_ipv4(
            old,
            ip=ip,
            prefix=prefix,
            gateway=gw,
            method='manual'
        )

        self.helpers.update(conn, path, iface, ipv4)

        print(f"{iface} updated: {ip}/{prefix}")

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

    def auto_dhcp_async(self, iface, callback=None):
        self._async(self.auto_dhcp, callback, iface)

    def edit_profile_async(self, iface, ip, prefix=24, gw=None, callback=None):
        self._async(self.edit_profile, callback, iface, ip, prefix, gw)

    def get_profile_async(self, iface, ip, prefix=24, gw=None, callback=None):
        self._async(self.get_profile, callback, iface, ip, prefix, gw)