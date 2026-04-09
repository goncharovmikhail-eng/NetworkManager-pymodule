Работает только с ipv4

дебаг делаю с датой и временем

дописать метод dhcp auto


Makefile goals:
1. build pip-module - собирается в докер контейнере и выплевывается локально на машину
2. build cli-binary - собирается в докер контейнере и выплевывается локально на машину
3. smoke_test (python3 -m scripts.cli get-profile eth1

# 2. добавить DNS
python3 -m scripts.cli add-dns eth1 8.8.8.8

# 3. сменить IP
python3 -m scripts.cli set-ip eth1 192.168.5.123

# 4. сменить prefix
python3 -m scripts.cli set-prefix eth1 24

# 5. включить DHCP обратно
python3 -m scripts.cli enable-dhcp eth1)
4. unit_test:
Добавлять dns если ping -c 1 $address - true
Добавлять если не был добавлен ранее. т.е дубликатов. Если есть дубликат, то warning! Уже есть. Pass.

---пример ---
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
---пример ---


проверки set-ip :
он должен быть в одной сети с gw. - Если не принадлежит, то Warning и добавляем тот ip который ввели. 
-- Вопрос. А если тут стоит публичный ip? --
должен принадлежить к         networks = {
            "10.0.0.0/8": ipaddress.ip_network('10.0.0.0/8'),
            "172.16.0.0/12": ipaddress.ip_network('172.16.0.0/12'),
            "192.168.0.0/16": ipaddress.ip_network('192.168.0.0/16')
        }   
т.к маску мы не трогаем а меняем только ip он должен не давать вводить тот ip даже того же пула адресов, которые выходят за пределы этой маски.
проверка на отключение dhcp сервера нет тк method = manual в функциях


проверки для set-prefix:
1. смотрим на ip, определяем какой диапозон в принципе  соответствует этой сетки и не даем функции принять число префикса который не соответсвует  которое не входит в этот диапозон. 
2. 0 - блокируем
3. 32 - исключение - выводим warning что единичный хост сети. 
проверка на отключение dhcp сервера нет тк method = manual в функциях



5. stages_up
