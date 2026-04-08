#!/usr/bin/env python3

from network_module.config import NetworkModule

nm = NetworkModule()

# Ручная конфигурация
nm.set_ip("eth0", "192.168.1.42", 24)
nm.set_gateway("eth0", "192.168.1.1")
nm.set_dns("eth0", ["8.8.8.8", "8.8.4.4"])

# Включение DHCP
settings = nm.enable_dhcp("eth0")
print(settings)
