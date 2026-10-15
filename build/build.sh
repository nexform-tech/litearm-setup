#!/usr/bin/env bash
# 生成 LITEARM-SE 机械臂安装教程 PDF。
#
# 排版沿用「技术文档/_build」的房式样式，与 LITEARM SE 产品手册一致：
#   md -> pandoc tex -> zebra 斑马纹 -> breaktt -> xelatex ×3
#
# 用法：
#   bash build/build.sh
set -euo pipefail

cd "$(dirname "$0")/.."
ROOT="$(pwd)"
B="$ROOT/build"
GEN="$B/gen"
NAME="LITEARM-SE机械臂安装教程"
DOCSHORT="LITEARM-SE 机械臂安装教程"
SRC="$ROOT/$NAME.md"
OUT="$ROOT/$NAME.pdf"

for c in pandoc xelatex python3; do
  command -v "$c" >/dev/null 2>&1 || { echo "错误：未找到 $c" >&2; exit 1; }
done

mkdir -p "$GEN"

echo "[1/5] 预处理 Markdown"
python3 -I - "$SRC" "$GEN/$NAME.md" <<'PY'
import sys
t = open(sys.argv[1], encoding="utf-8").read()
# 源文里不便直接排版的符号，按房式流水线做同样替换
for a, b in (("✅", "✓"), ("⚠️", "⚠"), ("📐", "图"), ("️", "")):
    t = t.replace(a, b)
open(sys.argv[2], "w", encoding="utf-8").write(t)
PY

echo "[2/5] 组装排版头（页眉写入手册名 + 产品手册样式片段）"
sed "s/@DOCSHORT@/${DOCSHORT}/g" "$B/a3_layout.tex" > "$GEN/layout_$NAME.tex"
cat "$B/a3_style_prod.tex" >> "$GEN/layout_$NAME.tex"

echo "[3/5] pandoc -> LaTeX"
pandoc "$GEN/$NAME.md" -o "$GEN/$NAME.tex" \
  --pdf-engine=xelatex --include-in-header="$GEN/layout_$NAME.tex" --columns=50 -N \
  -V mainfont="Lato" -V sansfont="Lato" -V monofont="Noto Sans Mono" \
  -V CJKmainfont="Noto Serif CJK SC" -V CJKsansfont="Noto Sans CJK SC" \
  -V CJKmonofont="Noto Sans Mono CJK SC" \
  -V geometry:"a4paper,left=15mm,right=12mm,top=38mm,bottom=30mm,headheight=18pt,headsep=20pt,footskip=10mm" \
  -V fontsize=11pt -V colorlinks=true --standalone

echo "[4/5] 后处理（斑马纹 / 长标识符断行）"
python3 -I "$B/zebra.py" "$GEN/$NAME.tex"
python3 -I "$B/breaktt.py" "$GEN/$NAME.tex"

echo "[5/5] xelatex 三遍"
cd "$GEN"
for pass in 1 2 3; do
  TEXINPUTS=".:$ROOT:" xelatex -interaction=nonstopmode -halt-on-error "$NAME.tex" >/dev/null 2>&1 \
    || { echo "xelatex 失败（第 $pass 遍），日志尾部：" >&2; tail -n 30 "$NAME.log" >&2; exit 1; }
done

cp "$NAME.pdf" "$OUT"
echo "完成：$OUT"
