import dbus
import socket
import struct
import ipaddress

class NetworkModule:
    def __init__(self):
        # Подключаемся к системной шине
        self.bus = dbus.SystemBus()
        self.nm_service = 'org.freedesktop.NetworkManager'
        
        # Прокси для активации соединений
        self.nm_obj = self.bus.get_object(self.nm_service, '/org/freedesktop/NetworkManager')
        self.nm_manager = dbus.Interface(self.nm_obj, 'org.freedesktop.NetworkManager')

    def _get_conn_iface(self, iface_name):
        settings_obj = self.bus.get_object(self.nm_service, '/org/freedesktop/NetworkManager/Settings')
        settings_iface = dbus.Interface(settings_obj, 'org.freedesktop.NetworkManager.Settings')
        
        for path in settings_iface.ListConnections():
            conn_obj = self.bus.get_object(self.nm_service, path)
            conn_iface = dbus.Interface(conn_obj, 'org.freedesktop.NetworkManager.Settings.Connection')
            
            settings = conn_iface.GetSettings()
            if settings.get('connection', {}).get('interface-name') == iface_name:
                return conn_iface, path
        raise ValueError(f"Профиль для {iface_name} не найден")


    def _ip_to_u32(self, ip_str):
        # Конвертация строки в UInt32 (Big-endian)
        return struct.unpack("!I", socket.inet_aton(str(ip_str)))[0]

    def _u32_to_ip(self, ip_u32):
        # Конвертация UInt32 обратно в строку IP
        return socket.inet_ntoa(struct.pack("!I", int(ip_u32)))

    def _validate_network(self, ip, prefix):
        ip_obj = ipaddress.ip_address(ip)
        
        # 1. Проверка на частные диапазоны
        networks = {
            "10.0.0.0/8": ipaddress.ip_network('10.0.0.0/8'),
            "172.16.0.0/12": ipaddress.ip_network('172.16.0.0/12'),
            "192.168.0.0/16": ipaddress.ip_network('192.168.0.0/16')
        }

        parent_net = None
        for name, net in networks.items():
            if ip_obj in net:
                parent_net = net
                parent_name = name
                break
        
        if not parent_net:
            raise ValueError(f"IP {ip} — ПУБЛИЧНЫЙ. Модуль разрешает только 10.x, 172.16-31.x, 192.168.x")

        # 2. Проверка префикса
        min_p = parent_net.prefixlen
        if prefix != 32 and not (min_p <= prefix <= 30):
            raise ValueError(
                f"Префикс /{prefix} некорректен для {parent_name}.\n"
                f"Рекомендация: используйте диапазон /{min_p}.../30 или /32."
            )

        # 3. Проверка на адрес сети и бродкаст (только если не /32)
        if prefix < 32:
            current_net = ipaddress.ip_network(f"{ip}/{prefix}", strict=False)
            if ip_obj == current_net.network_address:
                raise ValueError(f"IP {ip} является АДРЕСОМ СЕТИ {current_net}. Назначать его нельзя.")
            if ip_obj == current_net.broadcast_address:
                raise ValueError(f"IP {ip} является БРОДКАСТОМ сети {current_net}. Назначать его нельзя.")

    def get_profile(self, iface_name):
        conn_iface, _ = self._get_conn_iface(iface_name)
        settings = conn_iface.GetSettings()
        ipv4 = settings.get('ipv4', {})
        
        # Теперь self._u32_to_ip будет работать корректно
        dns_list = [self._u32_to_ip(u) for u in ipv4.get('dns', [])]
        
        addresses = []
        for addr in ipv4.get('address-data', []):
            addresses.append(f"{addr['address']}/{addr['prefix']}")

        return {
            "iface": iface_name,
            "method": str(ipv4.get('method', 'unknown')),
            "ip_addresses": addresses,
            "dns_servers": dns_list,
            "gateway": str(ipv4.get('gateway', ''))
        }

    def add_dns(self, iface_name, dns_ip):
        conn_iface, conn_path = self._get_conn_iface(iface_name)
        settings = conn_iface.GetSettings()
        ipv4 = settings.get('ipv4', dbus.Dictionary({}, signature='sv'))

        # 1. Читаем текущие DNS
        current_dns_uints = [int(u) for u in ipv4.get('dns', [])]
        new_dns_val = self._ip_to_u32(dns_ip)

        # 2. Защита от дублей
        if new_dns_val in current_dns_uints:
            print(f"WARNING! DNS {dns_ip} уже есть в профиле {iface_name}. Пропускаем.")
            return

        current_dns_uints.append(new_dns_val)

        # 3. Упаковка
        ipv4['dns'] = dbus.Array([dbus.UInt32(u) for u in current_dns_uints], signature='u', variant_level=1)
        ipv4['method'] = dbus.String(ipv4.get('method', 'manual'), variant_level=1)

        # Сохраняем остальные важные поля (адреса)
        if 'address-data' in ipv4:
            addr_array = dbus.Array([], signature='a{sv}')
            for a in ipv4['address-data']:
                item = dbus.Dictionary({
                    'address': dbus.String(str(a['address']), variant_level=1),
                    'prefix': dbus.UInt32(int(a['prefix']), variant_level=1)
                }, signature='sv')
                addr_array.append(item)
            ipv4['address-data'] = addr_array

        settings['ipv4'] = ipv4
        conn_iface.Update(settings)
        self.nm_manager.ActivateConnection(conn_path, "/", "/")
        print(f"Готово! DNS {dns_ip} добавлен.")

    def set_ip(self, iface_name, new_ip):
        conn_iface, conn_path = self._get_conn_iface(iface_name)
        settings = conn_iface.GetSettings()
        ipv4 = settings.get('ipv4', dbus.Dictionary({}, signature='sv'))

        # 1. Получаем текущий префикс для валидации связки IP/Маска
        addr_data = ipv4.get('address-data', dbus.Array([], signature='a{sv}'))
        if addr_data:
            prefix = int(addr_data[0]['prefix'])
        elif 'addresses' in ipv4 and len(ipv4['addresses']) > 0:
            prefix = int(ipv4['addresses'][0][1])
        else:
            prefix = 24  # дефолт

        # 2. Единая валидация (RFC 1918, маска, Network/Broadcast ID)
        self._validate_network(new_ip, prefix)

        # 3. Проверка шлюза (если он есть)
        gateway = str(ipv4.get('gateway', ''))
        if gateway:
            net = ipaddress.ip_network(f"{new_ip}/{prefix}", strict=False)
            if ipaddress.ip_address(gateway) not in net:
                raise ValueError(f"Критическая ошибка: шлюз {gateway} не будет доступен через новый IP {new_ip}/{prefix}")

        # 4. Формируем обновление
        new_entry = dbus.Dictionary({
            'address': dbus.String(str(new_ip), variant_level=1),
            'prefix': dbus.UInt32(prefix, variant_level=1)
        }, signature='sv')
        
        ipv4['address-data'] = dbus.Array([new_entry], signature='a{sv}')
        if 'addresses' in ipv4: del ipv4['addresses']
        
        ipv4['method'] = dbus.String('manual', variant_level=1)
        if gateway:
            ipv4['gateway'] = dbus.String(gateway, variant_level=1)
        
        if 'dns' in ipv4:
            ipv4['dns'] = dbus.Array([dbus.UInt32(u) for u in ipv4['dns']], signature='u', variant_level=1)

        # 5. Запись и активация
        settings['ipv4'] = ipv4
        conn_iface.Update(settings)
        if hasattr(conn_iface, 'Save'): conn_iface.Save()
        self.nm_manager.ActivateConnection(conn_path, "/", "/")
        print(f"IP {new_ip}/{prefix} успешно применен.")

    def set_prefix(self, iface_name, new_prefix):
        conn_iface, conn_path = self._get_conn_iface(iface_name)
        settings = conn_iface.GetSettings()
        ipv4 = settings.get('ipv4', dbus.Dictionary({}, signature='sv'))

        # 1. Получаем текущий IP
        addr_data = ipv4.get('address-data', dbus.Array([], signature='a{sv}'))
        if not addr_data:
            raise ValueError(f"На интерфейсе {iface_name} не найден активный IP для смены маски")
        
        current_ip = str(addr_data[0]['address'])

        # 2. Единая валидация
        self._validate_network(current_ip, new_prefix)

        # 3. Проверка шлюза при новой маске
        gateway = str(ipv4.get('gateway', ''))
        if gateway:
            new_net = ipaddress.ip_network(f"{current_ip}/{new_prefix}", strict=False)
            if ipaddress.ip_address(gateway) not in new_net:
                raise ValueError(f"Ошибка: при маске /{new_prefix} шлюз {gateway} окажется вне сети {new_net}")

        # 4. Формируем обновление
        new_entry = dbus.Dictionary({
            'address': dbus.String(current_ip, variant_level=1),
            'prefix': dbus.UInt32(int(new_prefix), variant_level=1)
        }, signature='sv')
        
        ipv4['address-data'] = dbus.Array([new_entry], signature='a{sv}')
        if 'addresses' in ipv4: del ipv4['addresses']

        ipv4['method'] = dbus.String('manual', variant_level=1)
        if 'dns' in ipv4:
            ipv4['dns'] = dbus.Array([dbus.UInt32(u) for u in ipv4['dns']], signature='u', variant_level=1)

        # 5. Запись и активация
        settings['ipv4'] = ipv4
        conn_iface.Update(settings)
        if hasattr(conn_iface, 'Save'): conn_iface.Save()
        self.nm_manager.ActivateConnection(conn_path, "/", "/")
        print(f"Префикс /{new_prefix} для IP {current_ip} успешно применен.")
