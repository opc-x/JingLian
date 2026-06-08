#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PY:-.venv/bin/python}"

echo "==> 原样导出教材（页图 + 逐行原文，零改写）"
"$PY" scripts/export_faithful.py --all

echo "==> 同步 JingYu 网站"
node jingyu/scripts/sync-data.mjs

echo "==> 完成。启动: cd jingyu && npm run dev"
echo "    批注请只改 annotations/callan/ 或网站侧栏，勿改 sources/callan/faithful/"
