#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 LITEARM-SE 机械臂安装教程.md 转成可直接编辑的 Word 文档。

流程：md（去掉 latex 原始块）-> pandoc -> docx -> python-docx 补封面/样式/题注。

用法：
    python3 build/build_docx.py
输出：
    LITEARM-SE机械臂安装教程.docx
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "build")
GEN = os.path.join(BUILD, "gen")
TOOLS = os.path.join(BUILD, ".tools")

sys.path.insert(0, TOOLS)

import pypandoc  # noqa: E402
from docx import Document  # noqa: E402
from docx.enum.section import WD_SECTION  # noqa: E402
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK  # noqa: E402
from docx.oxml import OxmlElement  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402
from docx.shared import Cm, Pt, RGBColor  # noqa: E402
from PIL import Image  # noqa: E402

SRC_MD = os.path.join(ROOT, "LITEARM-SE机械臂安装教程.md")
OUT_DOCX = os.path.join(ROOT, "LITEARM-SE机械臂安装教程.docx")

# ---- 版式参数（对齐 PDF 设计：思源宋体正文、灰白细线表格）------------------
FONT_EA_BODY = "宋体"          # 等价于 PDF 的 Noto Serif CJK SC
FONT_EA_SANS = "微软雅黑"      # 封面大标题用无衬线
FONT_LATIN = "Times New Roman"
BODY_SIZE = 10.5
TABLE_SIZE = 9.5
GRAY_RULE = "999999"
GRAY_SHADE = "EFEFEF"          # 对齐 PDF 斑马纹 gray 0.937
CALLOUT_SHADE = "F5F5F5"

# 对齐 LaTeX 版 \setkeys{Gin}{width=0.70\linewidth,height=0.52\textheight}
# 的做法：所有图统一装进同一个框，宽高都不超，保持比例。
# 0.70\linewidth = 364.5pt = 12.86cm，0.52\textheight = 338.8pt = 11.95cm。
# 注意不能只缩不放——源图 DPI 元数据不一致（fig07 带 220dpi，其余没有），
# 按 pandoc 给的原尺寸做单向缩小会让各图大小差异很大。
MAX_IMG_W = Cm(12.9)
MAX_IMG_H = Cm(12.0)


# --------------------------------------------------------------------------
# XML 小工具
# --------------------------------------------------------------------------
def _el(tag, **attrs):
    e = OxmlElement(tag)
    for k, v in attrs.items():
        e.set(qn("w:" + k), str(v))
    return e


# OOXML 里子元素必须按 schema 顺序排列，否则 Word/WPS 会判定文件损坏。
PPR_SEQ = ("w:pStyle", "w:keepNext", "w:keepLines", "w:pageBreakBefore",
           "w:framePr", "w:widowControl", "w:numPr", "w:suppressLineNumbers",
           "w:pBdr", "w:shd", "w:tabs", "w:suppressAutoHyphens", "w:kinsoku",
           "w:wordWrap", "w:overflowPunct", "w:topLinePunct", "w:autoSpaceDE",
           "w:autoSpaceDN", "w:bidi", "w:adjustRightInd", "w:snapToGrid",
           "w:spacing", "w:ind", "w:contextualSpacing", "w:mirrorIndents",
           "w:suppressOverlap", "w:jc", "w:textDirection", "w:textAlignment",
           "w:textboxTightWrap", "w:outlineLvl", "w:divId", "w:cnfStyle",
           "w:rPr", "w:sectPr", "w:pPrChange")

RPR_SEQ = ("w:rStyle", "w:rFonts", "w:b", "w:bCs", "w:i", "w:iCs", "w:caps",
           "w:smallCaps", "w:strike", "w:dstrike", "w:outline", "w:shadow",
           "w:emboss", "w:imprint", "w:noProof", "w:snapToGrid", "w:vanish",
           "w:webHidden", "w:color", "w:spacing", "w:w", "w:kern", "w:position",
           "w:sz", "w:szCs", "w:highlight", "w:u", "w:effect", "w:bdr",
           "w:shd", "w:fitText", "w:vertAlign", "w:rtl", "w:cs", "w:em",
           "w:lang", "w:eastAsianLayout", "w:specVanish", "w:oMath")

TBLPR_SEQ = ("w:tblStyle", "w:tblpPr", "w:tblOverlap", "w:bidiVisual",
             "w:tblStyleRowBandSize", "w:tblStyleColBandSize", "w:tblW",
             "w:jc", "w:tblCellSpacing", "w:tblInd", "w:tblBorders", "w:shd",
             "w:tblLayout", "w:tblCellMar", "w:tblLook", "w:tblCaption",
             "w:tblDescription")

TCPR_SEQ = ("w:cnfStyle", "w:tcW", "w:gridSpan", "w:hMerge", "w:vMerge",
            "w:tcBorders", "w:shd", "w:noWrap", "w:tcMar", "w:textDirection",
            "w:tcFitText", "w:vAlign", "w:hideMark")

TRPR_SEQ = ("w:cnfStyle", "w:divId", "w:gridBefore", "w:gridAfter", "w:wBefore",
            "w:wAfter", "w:cantSplit", "w:trHeight", "w:tblHeader",
            "w:tblCellSpacing", "w:jc", "w:hidden")


def _qseq(seq):
    """把 ('w:tblLook', ...) 转成 Clark 记法元组，便于和 lxml 的 tag 直接比。"""
    return tuple(qn(t) for t in seq)


def insert_ordered(parent, child, seq):
    """按 schema 顺序把 child 插进 parent，替换同名的旧元素。"""
    seq = _qseq(seq)
    old = parent.find(child.tag)
    if old is not None:
        parent.remove(old)
    if child.tag not in seq:
        parent.append(child)
        return child
    rank = seq.index(child.tag)
    for i, existing in enumerate(parent):
        if existing.tag in seq and seq.index(existing.tag) > rank:
            parent.insert(i, child)
            return child
    parent.append(child)
    return child


def set_fonts(style, ea=None, latin=None, size=None, bold=None, color=None,
              italic=None):
    """给 paragraph style 设置中西文字体。eastAsia 必须手写，python-docx 不管。"""
    rpr = style.element.get_or_add_rPr()
    if latin or ea:
        rf = rpr.get_or_add_rFonts()
        if latin:
            rf.set(qn("w:ascii"), latin)
            rf.set(qn("w:hAnsi"), latin)
        if ea:
            rf.set(qn("w:eastAsia"), ea)
        # 去掉主题字体，否则显式字体不生效
        for a in ("asciiTheme", "hAnsiTheme", "eastAsiaTheme", "cstheme"):
            if rf.get(qn("w:" + a)) is not None:
                del rf.attrib[qn("w:" + a)]
    f = style.font
    if size is not None:
        f.size = Pt(size)
    if bold is not None:
        f.bold = bold
    if italic is not None:
        f.italic = italic
    if color is not None:
        f.color.rgb = RGBColor.from_string(color)
    return style


def set_para(style, before=None, after=None, line=None, align=None,
             keep_next=None, keep_lines=None):
    pf = style.paragraph_format
    if before is not None:
        pf.space_before = Pt(before)
    if after is not None:
        pf.space_after = Pt(after)
    if line is not None:
        pf.line_spacing = line
    if align is not None:
        pf.alignment = align
    if keep_next is not None:
        pf.keep_with_next = keep_next
    if keep_lines is not None:
        pf.keep_together = keep_lines
    return style


def shade(element_pr, fill, seq):
    """给 pPr / tcPr 加底纹（按 schema 顺序插入）。"""
    return insert_ordered(
        element_pr, _el("w:shd", val="clear", color="auto", fill=fill), seq)


def page_break_paragraph(doc):
    p = doc.add_paragraph()
    p.add_run().add_break(WD_BREAK.PAGE)
    return p


def add_field(par, instr, font=None, size=None):
    run = par.add_run()
    run._r.append(_el("w:fldChar", fldCharType="begin"))
    t = OxmlElement("w:instrText")
    t.set(qn("xml:space"), "preserve")
    t.text = instr
    run._r.append(t)
    run._r.append(_el("w:fldChar", fldCharType="end"))
    if font:
        rf = run._r.get_or_add_rPr().get_or_add_rFonts()
        rf.set(qn("w:ascii"), font)
        rf.set(qn("w:hAnsi"), font)
    if size:
        run.font.size = Pt(size)
    return run


# --------------------------------------------------------------------------
# 1. 源文件 -> pandoc 输入（剥掉只给 LaTeX 用的封面/目录块）
# --------------------------------------------------------------------------
def prepare_markdown():
    src = open(SRC_MD, encoding="utf-8").read()
    body = re.sub(r"^```\{=latex\}.*?^```[ \t]*\n?", "", src, flags=re.S | re.M)
    if body == src:
        print("  ! 未匹配到 latex 块，请检查文档开头的 ```{=latex} 围栏")
    os.makedirs(GEN, exist_ok=True)
    md = os.path.join(GEN, "LITEARM-SE机械臂安装教程.docx.md")
    with open(md, "w", encoding="utf-8") as f:
        f.write(body)
    return md


def run_pandoc(md_path):
    out = os.path.join(tempfile.mkdtemp(prefix="litearm_docx_"), "body.docx")
    pypandoc.convert_file(
        md_path,
        "docx",
        outputfile=out,
        format="markdown+implicit_figures",
        extra_args=[
            "--toc",
            "--toc-depth=2",
            "--metadata", "toc-title=目录",
            "--resource-path", ROOT,
        ],
    )
    return out


# --------------------------------------------------------------------------
# 2. 样式
# --------------------------------------------------------------------------
def style_document(doc):
    st = doc.styles

    set_fonts(st["Normal"], ea=FONT_EA_BODY, latin=FONT_LATIN, size=BODY_SIZE,
              color="1A1A1A")
    set_para(st["Normal"], before=0, after=6, line=1.5,
             align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    for name in ("BodyText", "FirstParagraph", "Compact"):
        if name in [s.name for s in st]:
            set_fonts(st[name], ea=FONT_EA_BODY, latin=FONT_LATIN, size=BODY_SIZE)
            set_para(st[name], before=0, after=6, line=1.5,
                     align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    # 列表项（Compact）不要段后距，否则条目之间空得厉害
    set_para(st["Compact"], after=2, line=1.35)

    # 标题：对齐 PDF —— 正文同族衬线加粗
    heads = {
        "Heading 1": (15.5, 20, 10),
        "Heading 2": (12.5, 16, 8),
        "Heading 3": (11, 12, 6),
        "Heading 4": (10.5, 10, 5),
    }
    for name, (size, before, after) in heads.items():
        if name not in [s.name for s in st]:
            continue
        s = st[name]
        set_fonts(s, ea=FONT_EA_BODY, latin=FONT_LATIN, size=size, bold=True,
                  color="000000")
        set_para(s, before=before, after=after, line=1.3, keep_next=True,
                 keep_lines=True, align=WD_ALIGN_PARAGRAPH.LEFT)

    if "Heading 1" in [s.name for s in st]:
        # 一级标题下加一条细线，替代 PDF 的分节观感
        s = st["Heading 1"]
        ppr = s.element.get_or_add_pPr()
        bdr = _el("w:pBdr")
        bdr.append(_el("w:bottom", val="single", sz="6", space="4",
                       color=GRAY_RULE))
        insert_ordered(ppr, bdr, PPR_SEQ)

    # 引用块（建议/注意）：灰底 + 左侧竖条
    if "Block Text" in [s.name for s in st]:
        s = st["Block Text"]
        set_fonts(s, ea=FONT_EA_BODY, latin=FONT_LATIN, size=BODY_SIZE)
        set_para(s, before=6, after=6, line=1.45,
                 align=WD_ALIGN_PARAGRAPH.JUSTIFY)
        ppr = s.element.get_or_add_pPr()
        shade(ppr, CALLOUT_SHADE, PPR_SEQ)
        bdr = _el("w:pBdr")
        bdr.append(_el("w:left", val="single", sz="18", space="8",
                       color="BFBFBF"))
        insert_ordered(ppr, bdr, PPR_SEQ)
        insert_ordered(ppr, _el("w:ind", left="240", right="120"), PPR_SEQ)

    # 图注
    if "Image Caption" in [s.name for s in st]:
        set_fonts(st["Image Caption"], ea=FONT_EA_BODY, latin=FONT_LATIN,
                  size=9, color="595959")
        set_para(st["Image Caption"], before=4, after=12, line=1.15,
                 align=WD_ALIGN_PARAGRAPH.CENTER)
    for s in st:
        if s.name == "Caption":
            set_fonts(s, ea=FONT_EA_BODY, latin=FONT_LATIN, size=9,
                      color="595959")

    if "Table Caption" in [s.name for s in st]:
        set_fonts(st["Table Caption"], ea=FONT_EA_BODY, latin=FONT_LATIN,
                  size=9, color="595959")

    # 目录
    if "TOC Heading" in [s.name for s in st]:
        set_fonts(st["TOC Heading"], ea=FONT_EA_BODY, latin=FONT_LATIN,
                  size=16, bold=True, color="000000")
        set_para(st["TOC Heading"], before=0, after=14, line=1.3,
                 align=WD_ALIGN_PARAGRAPH.LEFT)

    # 目录条目 / 超链接
    for s in st:
        if s.name in ("toc 1", "toc 2", "toc 3"):
            set_fonts(s, ea=FONT_EA_BODY, latin=FONT_LATIN, size=BODY_SIZE,
                      color="1A1A1A")
            set_para(s, before=2, after=2, line=1.3)
    if "Hyperlink" in [s.name for s in st]:
        set_fonts(st["Hyperlink"], ea=FONT_EA_BODY, latin=FONT_LATIN,
                  color="0B5FA5")
        st["Hyperlink"].font.underline = True


# --------------------------------------------------------------------------
# 3. 正文微调：图片缩放、题注编号、表格线
# --------------------------------------------------------------------------
def fit_images(doc):
    for shape in doc.inline_shapes:
        w, h = shape.width, shape.height
        if not w or not h:
            continue
        scale = min(MAX_IMG_W / w, MAX_IMG_H / h)
        shape.width = int(w * scale)
        shape.height = int(h * scale)
    # pandoc 把图和题注各自放在一段里，让图片段居中
    for p in doc.paragraphs:
        if p.style.name in ("CaptionedFigure", "Figure") or (
            p._element.findall(".//" + qn("w:drawing"))
        ):
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.0


def number_captions(doc):
    n = 0
    for p in doc.paragraphs:
        if p.style.name != "Image Caption":
            continue
        n += 1
        txt = p.text.strip()
        if re.match(r"^图\s*\d+", txt):
            continue
        for r in p.runs:  # 清掉原有 run，重建
            r.text = ""
        if p.runs:
            p.runs[0].text = f"图 {n}　{txt}"
            p.runs[0].bold = False
        else:
            p.add_run(f"图 {n}　{txt}")
    print(f"  题注编号：{n} 张图")
    return n


def style_tables(doc):
    for table in doc.tables:
        table.autofit = True
        tbl_pr = table._tbl.tblPr

        borders = _el("w:tblBorders")
        for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
            borders.append(_el("w:" + edge, val="single", sz="4", space="0",
                               color=GRAY_RULE))
        insert_ordered(tbl_pr, borders, TBLPR_SEQ)

        mar = _el("w:tblCellMar")
        for edge, w in (("top", "60"), ("left", "110"), ("bottom", "60"),
                        ("right", "110")):
            mar.append(_el("w:" + edge, w=w, type="dxa"))
        insert_ordered(tbl_pr, mar, TBLPR_SEQ)

        rows = table.rows
        if not rows:
            continue
        # 表头：灰底、加粗、跨页重复
        tr_pr = rows[0]._tr.get_or_add_trPr()
        insert_ordered(tr_pr, _el("w:tblHeader", val="true"), TRPR_SEQ)
        insert_ordered(tr_pr, _el("w:cantSplit"), TRPR_SEQ)
        for cell in rows[0].cells:
            shade(cell._tc.get_or_add_tcPr(), GRAY_SHADE, TCPR_SEQ)
        for r_i, row in enumerate(rows):
            for cell in row.cells:
                for p in cell.paragraphs:
                    p.paragraph_format.space_before = Pt(2)
                    p.paragraph_format.space_after = Pt(2)
                    p.paragraph_format.line_spacing = 1.15
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    for run in p.runs:
                        run.font.size = Pt(TABLE_SIZE)
                        rf = run._r.get_or_add_rPr().get_or_add_rFonts()
                        rf.set(qn("w:eastAsia"), FONT_EA_BODY)
                        if r_i == 0:
                            run.font.bold = True


# --------------------------------------------------------------------------
# 4. 封面（重建 LaTeX titlepage 的版式）
# --------------------------------------------------------------------------
def add_cover(doc):
    body = doc.element.body
    made = []  # 显式收集，不能靠 body 切片——sectPr 的位置会让切片错位

    def keep(p):
        made.append(p._element)
        return p

    def pic(path, width_pt, before, after=0):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(before)
        p.paragraph_format.space_after = Pt(after)
        p.paragraph_format.line_spacing = 1.0
        p.add_run().add_picture(path, width=Pt(width_pt))
        return keep(p)

    def text(txt, size, ea, bold=False, before=0, after=0, color="000000",
             spacing=None, latin=FONT_EA_SANS):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(before)
        p.paragraph_format.space_after = Pt(after)
        p.paragraph_format.line_spacing = 1.0
        r = p.add_run(txt)
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.color.rgb = RGBColor.from_string(color)
        rf = r._r.get_or_add_rPr().get_or_add_rFonts()
        rf.set(qn("w:eastAsia"), ea)
        rf.set(qn("w:ascii"), latin)
        rf.set(qn("w:hAnsi"), latin)
        if spacing is not None:
            insert_ordered(r._r.get_or_add_rPr(),
                           _el("w:spacing", val=str(spacing)), RPR_SEQ)
        return keep(p)

    pic(os.path.join(ROOT, "images", "cover_litearm_logo.png"), 100, before=41)
    text("安装教程", 28, FONT_EA_SANS, bold=True, before=24, after=0)
    pic(os.path.join(ROOT, "images", "cover_litearm_se.png"), 289.1, before=21)
    text("NEXFORM ROBOTICS", 11, FONT_EA_SANS, bold=True, before=121, spacing=30)
    text("版本：V1.0　　日期：2026年10月13日", 9, FONT_EA_SANS, before=15,
         color="404040")

    brk = page_break_paragraph(doc)
    brk_el = brk._element
    body.remove(brk_el)

    # 封面整块搬到文档最前，分页符紧随其后；sectPr 始终留在 body 末尾
    for i, el in enumerate(made):
        body.remove(el)
        body.insert(i, el)
    body.insert(len(made), brk_el)


# --------------------------------------------------------------------------
# 5. 目录后分页、页眉页脚、字段刷新
# --------------------------------------------------------------------------
def add_breaks_and_furniture(doc):
    body = doc.element.body
    sdts = body.findall(qn("w:sdt"))
    if sdts:
        toc_sdt = sdts[0]
        idx = list(body).index(toc_sdt)
        p = page_break_paragraph(doc)
        el = p._element
        body.remove(el)
        body.insert(idx + 1, el)
    else:
        print("  ! 未找到目录字段")

    sec = doc.sections[0]
    sec.different_first_page_header_footer = True

    hp = sec.header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    hp.paragraph_format.space_after = Pt(0)
    r = hp.add_run("LITEARM-SE 机械臂安装教程")
    r.font.size = Pt(8.5)
    r.font.color.rgb = RGBColor.from_string("808080")
    rf = r._r.get_or_add_rPr().get_or_add_rFonts()
    rf.set(qn("w:eastAsia"), FONT_EA_BODY)
    ppr = hp._p.get_or_add_pPr()
    bdr = _el("w:pBdr")
    bdr.append(_el("w:bottom", val="single", sz="4", space="2",
                   color="D9D9D9"))
    insert_ordered(ppr, bdr, PPR_SEQ)

    for footer in (sec.footer, sec.even_page_footer):
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        fp.paragraph_format.space_before = Pt(0)
        add_field(fp, "PAGE", font=FONT_LATIN, size=9)

    # 打开文档时自动刷新目录页码
    settings = doc.settings.element
    if settings.find(qn("w:updateFields")) is None:
        uf = _el("w:updateFields", val="true")
        compat = settings.find(qn("w:compat"))
        if compat is not None:
            compat.addprevious(uf)
        else:
            settings.append(uf)


def verify(doc):
    """结构自检：sectPr 必须在 body 末尾，封面元素齐全。"""
    body = doc.element.body
    kids = list(body)
    assert kids[-1].tag == qn("w:sectPr"), "w:sectPr 不是 body 的最后一个元素"
    assert len(kids) == len(set(kids)), "body 里有重复移动的元素"
    head = kids[:6]
    texts = ["".join(t.text or "" for t in k.iter(qn("w:t"))) for k in head]
    imgs = [len(k.findall(".//" + qn("w:drawing"))) for k in head]
    assert imgs[0] == 1 and imgs[2] == 1, f"封面图片缺失：{imgs}"
    assert "安装教程" in texts[1], f"封面标题错位：{texts}"
    assert "NEXFORM" in texts[3], f"封面署名错位：{texts}"
    print(f"  自检通过：封面 {' | '.join(t for t in texts[:4] if t)}")


def main():
    print("1/6 准备 Markdown …")
    md = prepare_markdown()

    print("2/6 pandoc 转换 …")
    tmp_docx = run_pandoc(md)
    doc = Document(tmp_docx)

    print("3/6 套用样式 …")
    style_document(doc)

    print("4/6 图片、题注、表格 …")
    fit_images(doc)
    number_captions(doc)
    style_tables(doc)

    print("5/6 封面与分页 …")
    add_cover(doc)
    add_breaks_and_furniture(doc)
    verify(doc)

    doc.core_properties.title = "LITEARM-SE 机械臂安装教程"
    doc.core_properties.author = "NEXFORM ROBOTICS"

    print("6/6 保存 …")
    doc.save(OUT_DOCX)
    shutil.rmtree(os.path.dirname(tmp_docx), ignore_errors=True)
    print(f"完成 -> {OUT_DOCX}  ({os.path.getsize(OUT_DOCX) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
