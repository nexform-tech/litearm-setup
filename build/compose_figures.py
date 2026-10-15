#!/usr/bin/env python3
"""把 images/parts/ 下的源图裁切、重画图内标注、必要时横向拼成 images/ 下的整图。

安装教程里的「图 6 / 图 7 / 图 10 / 图 12」由多张照片并排组成；其余为单张。
为了让 Markdown 每个图只引用一个文件，这里先把它们加工好。

每个图做三件事，顺序固定：裁切（CROPS）-> 重画图内标注（LABELS）-> 拼接（FIGURES）。

用法：
    python3 build/compose_figures.py

替换某张原图或改了裁切/标注后，重新运行本脚本即可。
"""
import math
import os
import sys

try:
    import cv2
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("需要 Pillow / numpy / opencv-python：pip install Pillow numpy opencv-python")


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTS_DIR = os.path.join(ROOT, "images", "parts")
OUT_DIR = os.path.join(ROOT, "images")

GUTTER = 14  # 分图之间的留白（像素）
BG = (255, 255, 255)

# 图内标注重画：原图里烙在照片上的红字只有 ~20px 高、又是半透明浅红，
# 缩到版心宽度后约 8pt，压在花灰地毯或黑铁件上基本认不出。这里统一重画成
# 「深红字 + 白描边」，必要时补一条细红箭头；旧字先用 inpaint 抹掉。
# 目标是成图上 ≈10.4pt，各图按自己的缩放比折成像素字号（见 LABELS 的注释）。
LABEL_FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
LABEL_FONT_INDEX = 2   # NotoSansCJK-Bold.ttc 内 SC 面
LABEL_FILL = (176, 24, 24)
LABEL_HALO = (255, 255, 255)

# 源图裁切框 (左, 上, 右, 下)，按源图原分辨率。装订前先把竖构图裁成横构图，
# 让全篇图宽一致、页面不被高图顶空——裁掉的只是背景，不动器材本体。
# 没列出的图不裁。
CROPS = {
    # 596x873 -> 1.3:1，保留下半段（臂装在立柱上的那一段），截掉上方空墙
    "fig11-arm-direct.jpg": (0, 300, 596, 753),
    # 左右臂两张竖长条各自截到同样高度，拼起来才是横图；左右臂的差别全在顶部
    "fig12a-left-arm.jpg": (0, 0, 298, 400),
    "fig12b-right-arm.jpg": (0, 0, 294, 400),
    # 606x650 -> 1.3:1
    "fig13-power.jpg": (0, 0, 606, 455),
    # 473x914 -> 1.3:1，保留电源输出口与黄色接头那一段；从铭牌以下起裁，免得糊半个标签
    "fig14-power-output.jpg": (0, 290, 473, 650),
    # 1279x1706 -> 1.3:1，保留接线小板整体。同一张照片出现两次：
    # 图 5（桌面固定 步骤 5，看固定螺丝）与图 15（电气连接 步骤 3，看接线端子），
    # 标注不同，故各留一份源图、按图号分开命名。
    "fig05-control-board.jpg": (0, 400, 1279, 1361),
    "fig15-controller-board.jpg": (0, 400, 1279, 1361),
    # 832x687 -> 1.3:1，上下各去一点杂边
    "fig16-arm-connector.jpg": (0, 31, 832, 656),
}

# 源图文件名 -> (字号像素, [(擦除旧字框, 新字左上角, 文字, 箭头 起→终)])
# 全篇图都由 a3_layout.tex 排成 0.70\linewidth = 364.5pt 宽，字号按「成图上的点数」
# 折回源图像素：px = 8.9 × 成图宽度像素 ÷ 364.5，即 px ≈ 成图宽度px ÷ 41。
# 8.9pt 略大于图注的 8.5pt，比正文 11pt 小——标注重在能认出来，不该抢正文。
# 例：图 14 的源图裁完只有 473px 宽，12px 就够；图 1 的源图 1318px 宽，同样大小要写 32px。
# 拼接图的分图按**合成后**的整图宽度算比例（如 fig07a 的 26px 来自整图 1060px），
# 不是按分图自己那几百像素——分图缩放后还要再随整图缩一次。
# 擦除框/锚点/箭头都按该源图（裁切后）的分辨率；擦除框填 None 表示那里没有旧字要抹。
# 改了 a3_layout.tex 的 \setkeys{Gin}{width=...}，这里的 px 必须按新宽度整体重算，
# 否则标注会跟着图一起被放大或缩小。
LABELS = {
    # 图 1 机械臂固定于安装底板（箭头指底盘法兰上那颗螺栓，中心约 (675,627)）
    "fig01-arm-on-base.jpg": (32, [
        (None, (60, 790), "M5 螺丝（固定机械臂）", ((430, 800), (660, 638))),
        (None, (830, 790), "安装底板", ((830, 775), (795, 625))),
    ]),
    # 图 3 G 型夹夹紧底板
    "fig03-clamp.jpg": (32, [
        (None, (930, 330), "G 型夹 × 2", ((925, 378), (808, 486))),
    ]),
    # 图 5 控制板固定于安装底板（箭头指控制板右上方那颗大十字螺丝，中心约 (1042,495)）
    "fig05-control-board.jpg": (31, [
        (None, (1000, 300), "固定螺丝", ((1070, 360), (1042, 478))),
    ]),
    "fig07a-feet.jpg": (26, [
        ((311, 41, 359, 62), (313, 38), "脚杯", None),
        ((85, 249, 171, 268), (66, 245), "底板背面", None),
        # 4 个角上的红圈原本没有任何说明，读者不知道圈的是什么
        (None, (420, 92), "M16 孔 × 4", ((470, 126), (489, 145))),
    ]),
    "fig07b-casters.jpg": (26, [
        (None, (118, 103), "脚轮", ((152, 140), (188, 200))),
    ]),
    "fig08-column-base.jpg": (25, [
        (None, (700, 428), "M10 螺丝 × 8", ((694, 456), (600, 392))),
    ]),
    "fig09-top-mount.jpg": (27, [
        (None, (260, 243), "M6 内六角螺丝 × 4", ((360, 300), (383, 358))),
    ]),
    "fig10a-teleop.jpg": (29, [
        (None, (108, 58), "机械臂", ((152, 100), (128, 205))),
    ]),
    "fig10b-extension.jpg": (29, [
        (None, (18, 48), "M5 螺丝 × 6", ((128, 92), (212, 145))),
    ]),
    "fig10c-arm-on-extension.jpg": (29, [
        (None, (250, 32), "延长件", ((268, 74), (228, 120))),
    ]),
    # 图 11 机械臂直接装到立柱
    "fig11-arm-direct.jpg": (15, [
        (None, (30, 385), "M5 螺丝 × 6", ((145, 390), (330, 200))),
    ]),
    # 图 12 左右臂方向：整张图就靠这两句标注说明
    "fig12a-left-arm.jpg": (15, [
        (None, (150, 25), "电源线朝上", ((168, 52), (138, 200))),
    ]),
    "fig12b-right-arm.jpg": (15, [
        (None, (10, 20), "电源线朝下", ((95, 42), (238, 58))),
    ]),
    # 图 13 电源接入（「电源线」指向插头本体，不是它旁边的空白）
    "fig13-power.jpg": (15, [
        (None, (20, 415), "电源模块", ((72, 405), (95, 300))),
        (None, (430, 55), "电源线", ((452, 88), (505, 400))),
    ]),
    # 图 14 电源输出
    "fig14-power-output.jpg": (12, [
        (None, (20, 325), "XT60 输出", ((118, 330), (255, 218))),
    ]),
    # 图 15 控制板三路接线：三条线各自标作用，不标端子块——读者要认的是「线接哪儿」，
    # 端子型号照片里本来就看不清。上方编织线通机械臂下方接口、下方黄头编织线通
    # 电源、左侧模压线通 PC。
    "fig15-controller-board.jpg": (31, [
        (None, (775, 205), "接机械臂下方接口", ((775, 258), (712, 180))),
        (None, (330, 810), "接电源", ((425, 835), (686, 882))),
        (None, (20, 300), "USB 线接 PC", ((215, 355), (250, 500))),
    ]),
    # 图 16 机械臂下方接口
    "fig16-arm-connector.jpg": (20, [
        (None, (640, 520), "机械臂下方接口", ((640, 500), (468, 318))),
    ]),
    # 图 17 整桌连线（USB 线指带 USB-A 金属头的细线，不是旁边那根粗编织线）
    "fig17-electrical-overall.jpg": (32, [
        (None, (880, 250), "电源模块", ((880, 290), (835, 340))),
        (None, (40, 390), "控制板", ((215, 400), (500, 290))),
        (None, (320, 115), "USB 线", ((352, 146), (336, 224))),
    ]),
}

# 单张图：输出名 -> images/parts/ 下的源图名
SINGLES = {
    "fig01-arm-on-base.jpg": "fig01-arm-on-base.jpg",
    "fig02-base-on-edge.jpg": "fig02-base-on-edge.jpg",
    "fig03-clamp.jpg": "fig03-clamp.jpg",
    "fig04-tabletop-done.jpg": "fig04-tabletop-done.jpg",
    "fig05-control-board-mount.jpg": "fig05-control-board.jpg",
    "fig08-column-base.jpg": "fig08-column-base.jpg",
    "fig09-top-mount.jpg": "fig09-top-mount.jpg",
    "fig11-arm-direct.jpg": "fig11-arm-direct.jpg",
    "fig13-power.jpg": "fig13-power.jpg",
    "fig14-power-output.jpg": "fig14-power-output.jpg",
    "fig15-controller-board.jpg": "fig15-controller-board.jpg",
    "fig16-arm-connector.jpg": "fig16-arm-connector.jpg",
    "fig17-electrical-overall.jpg": "fig17-electrical-overall.jpg",
}


def _draw_arrow(draw, start, end, width, head):
    """细红线箭头，风格对齐照片里原有的标注线。"""
    draw.line([start, end], fill=LABEL_FILL, width=width)
    ang = math.atan2(end[1] - start[1], end[0] - start[0])
    for delta in (2.618, -2.618):  # ±150°
        draw.line([end, (end[0] + head * math.cos(ang + delta),
                         end[1] + head * math.sin(ang + delta))],
                  fill=LABEL_FILL, width=width)


def annotate(img, px, items):
    """抹掉旧标注并按规则重画（只改内存里的这张图，不动源文件）。"""
    boxes = [box for box, _, _, _ in items if box]
    if boxes:
        mask = np.zeros((img.height, img.width), dtype=np.uint8)
        for x0, y0, x1, y1 in boxes:
            # 外扩 2px，把旧字的抗锯齿边缘一并盖住
            mask[max(0, y0 - 2):y1 + 3, max(0, x0 - 2):x1 + 3] = 255
        cleaned = cv2.inpaint(np.asarray(img)[:, :, ::-1], mask, 5, cv2.INPAINT_TELEA)
        img = Image.fromarray(cleaned[:, :, ::-1])

    draw = ImageDraw.Draw(img)
    width, head = max(2, px // 10), px * 0.55
    for _, _, _, arrow in items:  # 先画线，文字的白描边再压上去
        if arrow:
            _draw_arrow(draw, arrow[0], arrow[1], width, head)

    font = ImageFont.truetype(LABEL_FONT, px, index=LABEL_FONT_INDEX)
    for _, (x, y), text, _ in items:
        draw.text((x, y), text, font=font, fill=LABEL_FILL,
                  stroke_width=max(4, px // 8), stroke_fill=LABEL_HALO)
    return img

# 输出文件名 -> 从左到右组成该图的分图
FIGURES = {
    "fig06-column.jpg": [
        "fig06a-column-front.jpg",
        "fig06b-column-iso.jpg",
    ],
    "fig07-feet-casters.jpg": [
        "fig07a-feet.jpg",
        "fig07b-casters.jpg",
    ],
    "fig10-teleop.jpg": [
        "fig10a-teleop.jpg",
        "fig10b-extension.jpg",
        "fig10c-arm-on-extension.jpg",
    ],
    "fig12-arm-direction.jpg": [
        "fig12a-left-arm.jpg",
        "fig12b-right-arm.jpg",
    ],
}


def prepare(name):
    """读源图 -> 裁切 -> 重画标注。裁切按源图原分辨率，标注坐标按裁切后的图。"""
    path = os.path.join(PARTS_DIR, name)
    if not os.path.exists(path):
        sys.exit(f"缺少源图：{path}")
    img = Image.open(path).convert("RGB")
    if name in CROPS:
        img = img.crop(CROPS[name])
    if name in LABELS:
        img = annotate(img, *LABELS[name])
    return img


def compose(out_name, part_names):
    parts = [prepare(name) for name in part_names]

    # 以最矮的分图为准统一高度，避免放大导致画质下降
    target_h = min(p.height for p in parts)
    scaled = [
        p.resize((round(p.width * target_h / p.height), target_h), Image.LANCZOS)
        for p in parts
    ]

    total_w = sum(s.width for s in scaled) + GUTTER * (len(scaled) - 1)
    canvas = Image.new("RGB", (total_w, target_h), BG)

    x = 0
    for s in scaled:
        canvas.paste(s, (x, 0))
        x += s.width + GUTTER

    dst = os.path.join(OUT_DIR, out_name)
    canvas.save(dst, "JPEG", quality=90)
    print(f"{out_name}  <=  {' + '.join(part_names)}  ({canvas.width}x{canvas.height})")


def single(out_name, part_name):
    """单张图：裁切 + 重画标注后直接写出。"""
    img = prepare(part_name)
    dst = os.path.join(OUT_DIR, out_name)
    img.save(dst, "JPEG", quality=90, optimize=True)
    print(f"{out_name}  <=  {part_name}（单张）  ({img.width}x{img.height})")


def main():
    if not os.path.isdir(PARTS_DIR):
        sys.exit(f"找不到分图目录：{PARTS_DIR}")
    for out_name, part_names in FIGURES.items():
        compose(out_name, part_names)
    for out_name, part_name in SINGLES.items():
        single(out_name, part_name)


if __name__ == "__main__":
    main()
