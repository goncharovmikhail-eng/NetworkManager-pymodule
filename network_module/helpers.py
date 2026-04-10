import dbus
import subprocess
import socket
import struct


class NMHelpers:
    def __init__(self, nm, bus, nm_service):
        self.nm = nm
        self.bus = bus
        self.nm_service = nm_service

    # =========================
    # SYSTEM
    # =========================

    def is_default_interface(self, iface: str) -> bool:
        out = subprocess.check_output("ip route", shell=True).decode()

        for line in out.splitlines():
            if line.startswith("default") and iface in line:
                return True

        return False

    # =========================
    # NM HELPERS
    # =========================

    def get_device_path(self, iface):
        for dev_path in self.nm.GetDevices():
            dev_obj = self.bus.get_object(self.nm_service, dev_path)
            props = dbus.Interface(dev_obj, 'org.freedesktop.DBus.Properties')

            name = props.Get(
                'org.freedesktop.NetworkManager.Device',
                'Interface'
            )

            if name == iface:
                return dev_path

        raise ValueError(f"Device {iface} not found")

    def get_conn(self, iface):
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

    def ensure_managed(self, iface):
        for dev in self.nm.GetDevices():
            obj = self.bus.get_object(self.nm_service, dev)
            props = dbus.Interface(obj, "org.freedesktop.DBus.Properties")

            name = props.Get("org.freedesktop.NetworkManager.Device", "Interface")
            managed = props.Get("org.freedesktop.NetworkManager.Device", "Managed")

            if name == iface:
                if not managed:
                    raise RuntimeError(f"{iface} is unmanaged by NetworkManager")
                return

        raise ValueError(f"{iface} not found")

    def update(self, conn, path, iface, ipv4):
        settings = conn.GetSettings()
        settings['ipv4'] = ipv4

        conn.Update(settings)

        if hasattr(conn, 'Save'):
            conn.Save()

        device = self.get_device_path(iface)
        self.nm.ActivateConnection(path, device, "/")

    # =========================
    # UTILS
    # =========================



    def mask_to_prefix(self, mask: str) -> int:
        import ipaddress
        try:
            ipaddress.IPv4Address(mask)  # гарантирует IPv4 формат
            return ipaddress.IPv4Network(f"0.0.0.0/{mask}").prefixlen
        except Exception:
            raise ValueError(f"Invalid netmask: {mask}")

    def _u32_to_ip(self, val):
        return socket.inet_ntoa(struct.pack("!I", int(val)))
    
    def _ip_to_u32(self, ip_str):
        return struct.unpack("!I", socket.inet_aton(str(ip_str)))[0]
    
    def _prepare_ipv4(self, old, **kwargs):
        ipv4 = dbus.Dictionary({}, signature='sv')

        ipv4['method'] = dbus.String(
            kwargs.get('method', old.get('method', 'manual')),
            variant_level=1
        )

        gw = kwargs.get('gateway', old.get('gateway'))
        if gw:
            ipv4['gateway'] = dbus.String(str(gw), variant_level=1)

        dns = kwargs.get('dns', old.get('dns', []))
        ipv4['dns'] = dbus.Array(
            [dbus.UInt32(self._ip_to_u32(str(d))) for d in dns],
            signature='u',
            variant_level=1
        )

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