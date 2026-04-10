import pytest
from network_module.config import NetworkModule


# =========================
# MOCK HELPERS
# =========================

class DummyHelpers:
    def __init__(self):
        self.managed = True
        self.exists = True
        self.default = False

        self.settings = {
            "ipv4": {
                "method": "manual",
                "gateway": "192.168.1.1",
                "dns": [],
                "address-data": [{"address": "192.168.1.100", "prefix": 24}],
            }
        }

    def ensure_managed(self, iface):
        if not self.exists:
            raise ValueError(f"{iface} not found")
        if not self.managed:
            raise RuntimeError(f"{iface} is unmanaged by NetworkManager")

    def is_default_interface(self, iface):
        return self.default

    def get_conn(self, iface):
        return self, "dummy-path"

    def GetSettings(self):
        return self.settings

    def _u32_to_ip(self, x):
        return x

    def _prepare_ipv4(self, old, **kwargs):
        self.prepared = kwargs
        return kwargs

    def update(self, conn, path, iface, ipv4):
        self.updated = ipv4


# =========================
# ensure_managed
# =========================

def test_unmanaged_interface():
    nm = NetworkModule()
    nm.helpers = DummyHelpers()
    nm.helpers.managed = False

    with pytest.raises(RuntimeError):
        nm.set_ip("test1", "192.168.1.10")


def test_interface_not_found():
    nm = NetworkModule()
    nm.helpers = DummyHelpers()
    nm.helpers.exists = False

    with pytest.raises(ValueError):
        nm.set_ip("test2", "192.168.1.10")


# =========================
# edit-profile logic
# =========================

def test_edit_profile_success():
    nm = NetworkModule()
    nm.helpers = DummyHelpers()

    nm.edit_profile("test0", "192.168.1.200", 24, "192.168.1.1")

    assert nm.helpers.updated is not None


def test_edit_profile_default_route_warning():
    nm = NetworkModule()
    nm.helpers = DummyHelpers()
    nm.helpers.default = True

    nm.edit_profile("test0", "192.168.1.200", 24, "192.168.1.1")

    assert nm.helpers.updated is not None


# =========================
# DNS
# =========================

def test_add_dns_success():
    nm = NetworkModule()
    nm.helpers = DummyHelpers()

    nm.add_dns("test0", "8.8.8.8")

    assert "8.8.8.8" in nm.helpers.prepared["dns"]


def test_add_dns_duplicate():
    nm = NetworkModule()
    nm.helpers = DummyHelpers()
    nm.helpers.settings["ipv4"]["dns"] = ["8.8.8.8"]

    nm.add_dns("test0", "8.8.8.8")

    # update не должен вызываться
    assert not hasattr(nm.helpers, "updated")


# =========================
# set_ip
# =========================

def test_set_ip_invalid():
    nm = NetworkModule()
    nm.helpers = DummyHelpers()

    with pytest.raises(ValueError):
        nm.set_ip("test0", "192.168.5.123ddf")


def test_set_ip_public():
    nm = NetworkModule()
    nm.helpers = DummyHelpers()

    with pytest.raises(ValueError):
        nm.set_ip("test0", "5.4.5.5")


def test_set_ip_success():
    nm = NetworkModule()
    nm.helpers = DummyHelpers()

    nm.set_ip("test0", "192.168.5.123")

    assert nm.helpers.updated is not None


def test_set_ip_gateway_warning():
    nm = NetworkModule()
    nm.helpers = DummyHelpers()

    # gateway не в подсети
    nm.helpers.settings["ipv4"]["gateway"] = "192.168.1.1"

    nm.set_ip("test0", "192.168.5.123")

    assert nm.helpers.updated is not None


def test_set_ip_default_route_warning():
    nm = NetworkModule()
    nm.helpers = DummyHelpers()
    nm.helpers.default = True

    nm.set_ip("test0", "192.168.1.200")

    assert nm.helpers.updated is not None


# =========================
# set_prefix
# =========================

def test_set_prefix_too_small():
    nm = NetworkModule()
    nm.helpers = DummyHelpers()

    with pytest.raises(ValueError):
        nm.set_prefix("test0", 8)


def test_set_prefix_success():
    nm = NetworkModule()
    nm.helpers = DummyHelpers()

    nm.set_prefix("test0", 16)

    assert nm.helpers.updated is not None


# =========================
# DHCP
# =========================

def test_enable_dhcp():
    nm = NetworkModule()
    nm.helpers = DummyHelpers()

    nm.auto_dhcp("test0")

    assert nm.helpers.updated["method"] == "auto"