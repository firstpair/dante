#!/bin/sh
set -eu
project_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
install_dir="$project_root/.tools"
mkdir -p "$install_dir"
if [ ! -x "$install_dir/uv" ]; then
  curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="$install_dir" sh
fi
"$install_dir/uv" --version
