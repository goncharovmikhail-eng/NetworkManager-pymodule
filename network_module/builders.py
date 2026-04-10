import dbus

def _prepare_ipv4(old, **kwargs):
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