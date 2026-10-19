#!/usr/bin/env bash
# 生成 LITEARM-SE 机械臂使用教程的 PDF：中文版与英文版各一份。
#
# 排版沿用「技术文档/_build」的房式样式，与 LITEARM SE 产品手册一致：
#   md -> pandoc tex -> zebra 斑马纹 -> breaktt -> xelatex ×3
#
# 两份文档共用同一套排版头（build/a3_layout.tex）与产品手册样式
# （build/a3_style_prod.tex），差别只有三处，都在下面的 build_doc 调用里：
#   - 排版头里的四处名称：页眉的册名、目录标题、图注编号格式、引用图时用的词
#   - 中文版要追加 a3_cjk.tex（中文断行规则 + 正文中文字体），英文版不要
#   - 中文版要传 pandoc 的 CJK 字体变量，英文版不要
#
# 用法：
#   bash build/build.sh
set -euo pipefail

cd "$(dirname "$0")/.."
ROOT="$(pwd)"
B="$ROOT/build"
GEN="$B/gen"

for c in pandoc xelatex python3; do
  command -v "$c" >/dev/null 2>&1 || { echo "错误：未找到 $c" >&2; exit 1; }
done

mkdir -p "$GEN"

# 排一份文档。
#   $1 源文件基名（同名 .md 与 .pdf 都在仓库根目录）
#   $2 页眉右端与 PDF 标题里的册名
#   $3 目录标题            $4 图注编号格式        $5 引用图时用的词
#   $6 语言，zh 才追加 build/a3_cjk.tex 并传 CJK 字体变量
build_doc() {
  local name="$1" docshort="$2" contentsname="$3" figlabel="$4" figname="$5" lang="$6"
  local src="$ROOT/$name.md" out="$ROOT/$name.pdf"

  if [ ! -f "$src" ]; then echo "错误：找不到 $src" >&2; exit 1; fi

  echo "[1/5] 预处理 Markdown：$name.md"
  python3 -I - "$src" "$GEN/$name.md" <<'PY'
import sys
t = open(sys.argv[1], encoding="utf-8").read()
# 源文里不便直接排版的符号，按房式流水线做同样替换
for a, b in (("✅", "✓"), ("⚠️", "⚠"), ("📐", "图"), ("️", "")):
    t = t.replace(a, b)
open(sys.argv[2], "w", encoding="utf-8").write(t)
PY

  echo "[2/5] 组装排版头：$name"
  sed -e "s/@DOCSHORT@/${docshort}/g" \
      -e "s/@CONTENTSNAME@/${contentsname}/g" \
      -e "s/@FIGLABEL@/${figlabel}/g" \
      -e "s/@FIGNAME@/${figname}/g" \
      "$B/a3_layout.tex" > "$GEN/layout_$name.tex"
  cat "$B/a3_style_prod.tex" >> "$GEN/layout_$name.tex"

  local cjkfonts=()
  if [ "$lang" = "zh" ]; then
    cat "$B/a3_cjk.tex" >> "$GEN/layout_$name.tex"
    cjkfonts=(-V CJKmainfont="Noto Serif CJK SC" -V CJKsansfont="Noto Sans CJK SC"
              -V CJKmonofont="Noto Sans Mono CJK SC")
  fi

  echo "[3/5] pandoc -> LaTeX：$name"
  pandoc "$GEN/$name.md" -o "$GEN/$name.tex" \
    --pdf-engine=xelatex --include-in-header="$GEN/layout_$name.tex" --columns=50 -N \
    -V mainfont="Lato" -V sansfont="Lato" -V monofont="Noto Sans Mono" \
    "${cjkfonts[@]}" \
    -V geometry:"a4paper,left=15mm,right=12mm,top=38mm,bottom=30mm,headheight=18pt,headsep=20pt,footskip=10mm" \
    -V fontsize=11pt -V colorlinks=true --standalone

  echo "[4/5] 后处理（斑马纹 / 长标识符断行）：$name"
  python3 -I "$B/zebra.py" "$GEN/$name.tex"
  python3 -I "$B/breaktt.py" "$GEN/$name.tex"

  echo "[5/5] xelatex 三遍：$name"
  (
    cd "$GEN"
    for pass in 1 2 3; do
      TEXINPUTS=".:$ROOT:" xelatex -interaction=nonstopmode -halt-on-error "$name.tex" >/dev/null 2>&1 \
        || { echo "xelatex 失败（第 $pass 遍），日志尾部：" >&2; tail -n 30 "$name.log" >&2; exit 1; }
    done
  )

  cp "$GEN/$name.pdf" "$out"
  echo "完成：$out"
}

# 中文版：随产品交付的那份
build_doc "LITEARM-SE机械臂使用教程" "LITEARM-SE 机械臂使用教程" "目录" "图#2. " "图" zh
# 英文版：同一份文档的英文对照，图与图号与中文版一一对应
build_doc "LITEARM-SE-user-guide" "LITEARM-SE User Guide" \
  "Contents" "Figure #2. " "Figure" en
