#!/usr/bin/env bash
# Prepara el entorno para renderizar a Nailong en 3D: librerías gráficas del
# sistema (render por software, sin GPU) y un entorno virtual con Blender.
#
# Uso: bash tools/modelo/instalar.sh
set -euo pipefail

raiz="$(cd "$(dirname "$0")/../.." && pwd)"

if ! ldconfig -p | grep -q libEGL.so.1; then
  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
    libegl1 libgl1 libegl-mesa0 libgl1-mesa-dri libxi6 libxkbcommon0 \
    libsm6 libxrender1 libxxf86vm1 libxfixes3 >/dev/null
fi

if [ ! -x "$raiz/.venv/bin/python" ]; then
  python3 -m venv "$raiz/.venv"
fi
"$raiz/.venv/bin/pip" install -q -r "$raiz/tools/modelo/requirements.txt"
"$raiz/.venv/bin/python" -c "import bpy; print('Blender', bpy.app.version_string, 'listo')"
