#!/bin/bash
# Создаем папку для готового пакета
mkdir -p ./dist_out

# Собираем образ
docker build -t nm-module-builder -f Dockerfile.build .

# Запускаем контейнер и копируем результат в локальную папку dist_out
docker run --rm -v "$(pwd)/dist_out:/output" nm-module-builder

echo "[INFO] Сборка завершена. Пакет лежит в ./dist_out"

