Работает только с ipv4

дебаг делаю с датой и временем

дописать метод dhcp auto


Makefile goals:
1. подготовка интерфейсов:
удаление старых интерфейсов с именем test*
создание 2 тестовых интерфейса 
ip link add test0 type dummy
ip link set test0 up
nmcli dev set test0 managed yes
nmcli dev status
nmcli con add type dummy ifname test0 con-name test0
nmcli con up test0
ip link add test1 type dummy
ip link set test1 up
___
потом в тестировании проверка метода ensure_managed на интерфейсе test1 
python3 -m scripts.cli edit-profile test1 192.168.1.200 24 --gw 192.168.1.1 - RuntimeError: test1 is unmanaged by NetworkManager
python3 -m scripts.cli edit-profile test2 192.168.1.200 24 --gw 192.168.1.1 ValueError: test2 not found
python3 -m scripts.cli edit-profile test2 192.168.1.200 24  192.168.1.1 - usage: cli.py [-h] {get-profile,set-ip,set-prefix,set-mask,add-dns,enable-dhcp,edit-profile} ... - cli.py: error: unrecognized arguments: 192.168.1.1
python3 -m scripts.cli edit-profile test0 192.168.1.200 24 --gw 192.168.1.1 ; 
python3 -m scripts.cli get-profile test0
2026-04-10 09:36:19,834 [INFO] method: manual
2026-04-10 09:36:19,835 [INFO] gateway: 192.168.1.1
2026-04-10 09:36:19,835 [INFO] dns: []
2026-04-10 09:36:19,835 [INFO] addresses: ['192.168.1.200/24'] => get_profile - ok ; edit-profile - ok

---
test 
если дважды ввести эту команду  python3 -m scripts.cli edit-profile test0 192.168.1.200 24 --gw 192.168.1.1 то на второй раз будет предупреждение т.к в 
ip route добавиться default via 192.168.1.1 dev 
test0 proto static metric 550
WARNING: test0 is default route interface!

---
test
root@main ~/projects/NetworkManager-pymodule (develop2 *) ➜ python3 -m scripts.cli add-dns test0 8.8.8.8
2026-04-10 09:49:42,411 [INFO] DNS added
---
test
root@main ~/projects/NetworkManager-pymodule (develop2 *) ➜ python3 -m scripts.cli add-dns test0 8.8.8.8
WARNING: DNS 8.8.8.8 already exists
2026-04-10 09:49:49,563 [INFO] DNS added 
---
test
python3 -m scripts.cli set-ip test0 192.168.5.123ddf ValueError: '192.168.5.123ddf' does not appear to be an IPv4 or IPv6 address
root@main ~/projects/NetworkManager-pymodule (develop2 *) ➜ python3 -m scripts.cli set-ip test0 192.168.5.123
WARNING: test0 is default route interface! 
WARNING: gateway 192.168.1.1 not in 192.168.5.0/24
2026-04-10 09:55:26,155 [INFO] IP updated
root@main ~/projects/NetworkManager-pymodule (develop2 *) ➜ python3 -m scripts.cli get-profile test0
2026-04-10 09:55:55,413 [INFO] method: manual
2026-04-10 09:55:55,413 [INFO] gateway: 192.168.1.1
2026-04-10 09:55:55,413 [INFO] dns: ['8.8.8.8']
2026-04-10 09:55:55,413 [INFO] addresses: ['192.168.5.123/24'] = > условие _validate_ip - ок and проверка на default ok

---
test
python3 -m scripts.cli set-ip test0 5.4.5.5 
ValueError: 5.4.5.5 is PUBLIC. Only private networks allowed условие _validate_ip - ок 

---
test
python3 -m scripts.cli set-prefix test0 8 ValueError: Prefix /8 too small for 192.168.0.0/16
---
test
python3 -m scripts.cli set-prefix test0 16 ; 2026-04-10 10:07:57,163 [INFO] Prefix updated
---
test
root@main ~/projects/NetworkManager-pymodule (develop2 *) ➜ python3 -m scripts.cli enable-dhcp test0
2026-04-10 10:54:52,090 [INFO] DHCP enabled
root@main ~/projects/NetworkManager-pymodule (develop2 *) ➜ python3 -m scripts.cli get-profile test0
2026-04-10 10:54:55,702 [INFO] method: auto
2026-04-10 10:54:55,702 [INFO] gateway:
2026-04-10 10:54:55,702 [INFO] dns: []
2026-04-10 10:54:55,702 [INFO] addresses: []
empty т.к нет dhcp сервер

1. build pip-module - собирается в докер контейнере и выплевывается локально на машину
2. build cli-binary - собирается в докер контейнере и выплевывается локально на машину
3. smoke_test python3 -m scripts.cli get-profile eth1

# 2. добавить DNS
python3 -m scripts.cli add-dns eth1 8.8.8.8

# 3. сменить IP
python3 -m scripts.cli set-ip eth1 192.168.5.123

# 4. сменить prefix
python3 -m scripts.cli set-prefix eth1 24

# 5. включить DHCP обратно
python3 -m scripts.cli enable-dhcp eth1
4. unit_test:
Добавлять dns если ping -c 1 $address - true, если нет то warning.
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

проверка dhcp auto
set ip 1565566
get_pofile - смотрим данные
dhcp auto
get_pofile - смотрим данные
---
если изменились, значит тест прошел успешно.



5. stages_up





