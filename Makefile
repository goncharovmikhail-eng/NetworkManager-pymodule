SHELL := /bin/bash

.PHONY: prepos_local build smoke-test clean

prepos_local:
	@nmcli con delete test0 || true
	@nmcli con delete test1 || true

	@echo "[INFO] Загружаем dummy module..."
	@sudo modprobe dummy || true

	@echo "[INFO] Создаём test0..."
	@sudo ip link add test0 type dummy || true
	@sudo ip link set test0 up

	@echo "[INFO] Отдаём test0 под NetworkManager..."
	@sudo nmcli dev set test0 managed yes || true
	@sudo nmcli con add type dummy ifname test0 con-name test0 || true
	@sudo nmcli con up test0 || true

	@echo "[INFO] Создаём test1 (без NetworkManager)..."
	@sudo ip link add test1 type dummy || true
	@sudo ip link set test1 up

	@echo "[INFO] Проверка состояния:"
	@nmcli dev status || true
	@echo ""
	@ip link show | grep test || true

	@echo "[DONE] Интерфейсы готовы"
	@python -c "import network_module; print(network_module.__file__)"

build:
	@echo "[INFO] Создаем папку dist_out..."
	@rm -rf dist_out
	@mkdir -p dist_out

	@echo "[INFO] Сборка docker image..."
	@DOCKER_BUILDKIT=1 docker build -t nm-module-builder -f Dockerfile.build .

	@echo "[INFO] Запуск сборки wheel внутри контейнера..."
	# Теперь контейнер при запуске выполнит CMD и положит билд в примонтированную папку
	@docker run --rm -v "$(PWD)/dist_out:/output" nm-module-builder

	@echo "[INFO] Проверка результата..."
	@ls -lah dist_out

test-smoke:
	@echo "[INFO] Проверка CLI сценариев..."

	@python -m scripts get-profile test0
	@echo "[INFO] Первично заполняем профиль"
	@python3 -m scripts.cli edit-profile test0 192.168.1.200 24 --gw 192.168.1.1 || true
	@python3 -m scripts get-profile test0

	@echo "[STEP 1] DNS add"
	@python3 -m scripts.cli add-dns test0 8.8.8.8 || true
	@python3 -m scripts get-profile test0

	@echo "[STEP 2] change IP"
	@python3 -m scripts.cli set-ip test0 192.168.5.123 || true
	@python3 -m scripts get-profile test0

	@echo "[STEP 3] change prefix"
	@python3 -m scripts.cli set-prefix test0 24 || true
	@python3 -m scripts get-profile test0

	@echo "[STEP 4] enable DHCP"
	@python3 -m scripts.cli enable-dhcp test0 || true
	@python3 -m scripts get-profile test0

	@echo "[DONE] Smoke test completed"

test-units:
	@echo "[INFO] Running unit tests..."
	@PYTHONPATH=. pytest -v tests

reinstall:
	@pip uninstall -y network-manager-pymodule || true
	@rm -rf dist_out
	@$(MAKE) build
	@ls -lah dist_out
	@pip install dist_out/*.whl
	@python -c "import network_module; print(network_module.__file__)"

# =========================
# CLEAN
# =========================
clean:
	@echo "[INFO] Cleaning build artifacts..."
	@rm -rf dist_out build *.egg-info

	@echo "[INFO] Cleaning Python cache..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + || true
	@find . -type f -name "*.pyc" -delete || true
	@find . -type f -name "*.pyo" -delete || true

	@echo "[DONE] cleaned"