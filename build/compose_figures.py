#!/usr/bin/env python3
"""把 images/parts/ 下的源图裁切、重画图内标注、必要时横向拼成 images/ 下的整图。

安装教程里的「图 6 / 图 7」由多张照片并排组成；其余为单张。
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
    # 三张新照片是手机原图，方形/竖构图，统一裁到 1.33:1：只截上下、不动左右，
    # 正文里所有图就还是同一个宽度。裁掉的是背景（人、地毯、空墙），不动器材本体。
    # 1280x1280 -> 1.33:1，从顶部起留在 1280x960
    "fig11-arm-direct.jpg": (0, 180, 1280, 1140),
    # 与图 11 同一张源图（立柱内部走线与直接装配看的是同一处走线），裁切标注一致
    "fig12-column-routing.jpg": (0, 180, 1280, 1140),
    # 1280x1280 -> 1.85:1，俯拍的地面本来就只有中间一条有用：上边缘压在底板之上
    # （出线点在图高 1/8 处），下边缘切在编织线走向电源的那一段。
    # **这一张不能按 4:3 裁**：留成 4:3 是 273pt 高，与同样必须留高的图 14 排不满
    # 一页，图 14 会被整张顶到下一页、在页底空出 300pt 以上。压扁图 13 是两者
    # 都放得下的唯一办法。
    "fig13-cable-exit.jpg": (0, 250, 1280, 940),
    # 1279x1706 -> 1.12:1。上边缘压在肩部之上（两臂的电源线出处就在那里），
    # 下边缘一直留到左臂末端——按 4:3 裁到 y=1249 会把两条臂从中间切断。
    "fig14-arm-direction.jpg": (0, 290, 1279, 1430),
    # 1100x825 -> 1.335:1。左边那整条是**还没装到立柱上**的另一条臂，读者会当成装
    # 好的第三臂，所以从 x=430 起裁、一点不留（x=410 还会在左边沿留下它轴端的黑边）。
    # 上边缘切掉 40px 只切到黑顶板；下边缘留到 542，让 M6 那颗螺钉的红圈（底 492）
    # 不贴边。裁后 670x502 仍是 4:3，成图高 273pt 与裁之前相同——第 4 章多占的一页
    # 全部来自图 10（见下），不是这张。
    "fig09-top-mount.jpg": (430, 40, 1100, 542),
    # 图 10 只留中间那张延长件（原因见 FIGURES 的说明）：396x527 -> 396x297 补成 4:3，
    # 与其他图同为 364.5pt 宽 × 273pt 高。**这一张成图比原来高 110pt**（原来三张并排
    # 是 1178px 宽、只有 163pt 高），第 4 章因此排不下、全文从 15 页变成 16 页：
    # 图 10 整张下移到下一页，第 9 页页底空出 236pt。要回 15 页只能把这张再压矮——
    # 6 个 M5 孔本身的跨度就有 229px（y 103–332），压到能塞回第 9 页的 224pt（≈243px）
    # 会把最下面那颗孔的边切掉，所以没压，见 README「实测排版结果」。
    # 切成竖构图更糟：会被 0.52\textheight 顶成 253pt 宽、337pt 高，比全篇的图窄一截。
    # 切掉的上边缘是延长件上方那块没有细节的黑板，下边缘切在螺纹面以下，6 个 M5 孔都在。
    "fig10b-extension.jpg": (0, 70, 396, 367),
    # 606x650 -> 1.3:1
    "fig15-power.jpg": (0, 0, 606, 455),
    # 473x914 -> 1.3:1，保留电源输出口与黄色接头那一段；从铭牌以下起裁，免得糊半个标签
    "fig16-power-output.jpg": (0, 290, 473, 650),
    # 1279x1706 -> 1.3:1，保留接线小板整体。同一张照片出现两次：
    # 图 5（桌面固定 步骤 5，看固定螺丝）与图 17（电气连接 步骤 3，看接线端子），
    # 标注不同，故各留一份源图、按图号分开命名。
    "fig05-control-board.jpg": (0, 400, 1279, 1361),
    "fig17-controller-board.jpg": (0, 400, 1279, 1361),
    # 832x687 -> 1.3:1，上下各去一点杂边
    "fig18-arm-connector.jpg": (0, 31, 832, 656),
}

# 源图文件名 -> (字号像素, [(擦除旧字框, 新字左上角, 文字, 箭头 起→终)])
# 全篇图都由 a3_layout.tex 排成 0.70\linewidth = 364.5pt 宽，字号按「成图上的点数」
# 折回源图像素：px = 8.9 × 成图宽度像素 ÷ 364.5，即 px ≈ 成图宽度px ÷ 41。
# 8.9pt 略大于图注的 8.5pt，比正文 11pt 小——标注重在能认出来，不该抢正文。
# 例：图 16 的源图裁完只有 473px 宽，12px 就够；图 1 的源图 1318px 宽，同样大小要写 32px。
# 拼接图的分图按**合成后**的整图宽度算比例（如 fig07a 的 26px 来自整图 1060px），
# 不是按分图自己那几百像素——分图缩放后还要再随整图缩一次；图 10 从三张并排改成
# 单张出图后不再拼接，就按它自己的 396px 算（10px）。
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
    # 图 9 顶部安装件（裁掉左臂后 670px 宽，字号 8.9 × 670 ÷ 364.5 ≈ 16px）
    # 箭头指剩下那颗看得见的 M6（裁后约 (214, 408)），文字落在左侧黑顶板上
    "fig09-top-mount.jpg": (16, [
        (None, (25, 235), "M6 内六角螺丝 × 4", ((62, 272), (196, 392))),
    ]),
    # 图 10 现在只有中间这张延长件（fig10a「整体遥操形态」、fig10c「机械臂装至延长件」
    # 两张用户不要了，源图还留在 parts/ 供以后取用，LABELS 里不再摆它们的标注）。
    # 延长件这张裁成 4:3 后 396px 宽，字号 8.9 × 396 ÷ 364.5 ≈ 10px
    "fig10b-extension.jpg": (10, [
        (None, (12, 8), "M5 螺丝 × 6", ((78, 44), (196, 62))),
    ]),
    # 图 11 / 图 12 是同一张源图（docx 在步骤 7、步骤 8 各用一次），但两张的**重点不同**，
    # 所以标注也不同：图 11 讲装配，箭头指底盘法兰上的六角螺丝；图 12 讲走线，
    # 箭头指穿进安装板长孔的那根编织线。别把两条标注抄成一样。
    "fig11-arm-direct.jpg": (31, [
        (None, (30, 470), "M5 螺丝 × 6", ((215, 500), (505, 445))),
    ]),
    "fig12-column-routing.jpg": (31, [
        (None, (80, 380), "电源线", ((255, 405), (665, 215))),
    ]),
    # 图 13 立柱下方的出线口：箭头指向编织线从底板下沿钻出来的那一点 (裁后 ~590, 85)
    "fig13-cable-exit.jpg": (31, [
        (None, (60, 510), "从立柱下方穿出", ((300, 545), (590, 120))),
    ]),
    # 图 14 左右臂方向：整张图就靠这两句标注说明。
    # 左臂根部有上下两根线：上面那根绕到安装件顶上的是电源线，下面那个 U 形回折的
    # 是关节连接线。右臂的电源线在立柱另一面（这个角度看不见），看得见的只有下面
    # 那根关节连接线——所以右臂标的是「关节连接线」，不是原来的「电源线朝下」。
    # 两臂电源线都朝上这件事，写在正文的「注意」里，不在图上硬指（右臂那根指不到）。
    "fig14-arm-direction.jpg": (31, [
        (None, (40, 300), "电源线朝上", ((230, 330), (505, 130))),
        (None, (1030, 420), "关节连接线", ((1030, 445), (945, 330))),
    ]),
    # 图 15 电源接入（「电源线」指向插头本体，不是它旁边的空白）
    "fig15-power.jpg": (15, [
        (None, (20, 415), "电源模块", ((72, 405), (95, 300))),
        (None, (430, 55), "电源线", ((452, 88), (505, 400))),
    ]),
    # 图 16 电源输出
    "fig16-power-output.jpg": (12, [
        (None, (20, 325), "XT60 输出", ((118, 330), (255, 218))),
    ]),
    # 图 17 控制板三路接线：三条线各自标作用，不标端子块——读者要认的是「线接哪儿」，
    # 端子型号照片里本来就看不清。上方编织线通机械臂下方接口、下方黄头编织线通
    # 电源、左侧模压线通 PC。
    "fig17-controller-board.jpg": (31, [
        (None, (775, 205), "接机械臂下方接口", ((775, 258), (712, 180))),
        (None, (330, 810), "接电源", ((425, 835), (686, 882))),
        (None, (20, 300), "USB 线接 PC", ((215, 355), (250, 500))),
    ]),
    # 图 18 机械臂下方接口
    "fig18-arm-connector.jpg": (20, [
        (None, (640, 520), "机械臂下方接口", ((640, 500), (468, 318))),
    ]),
    # 图 19 整桌连线（USB 线指带 USB-A 金属头的细线，不是旁边那根粗编织线）
    "fig19-electrical-overall.jpg": (32, [
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
    # 图 10 只留延长件那一张，所以从拼接改成了单张，输出名也跟着改
    # （原来的 images/fig10-teleop.jpg 是「遥操形态」三连图，已不再生成）
    "fig10-extension.jpg": "fig10b-extension.jpg",
    "fig11-arm-direct.jpg": "fig11-arm-direct.jpg",
    "fig12-column-routing.jpg": "fig12-column-routing.jpg",
    "fig13-cable-exit.jpg": "fig13-cable-exit.jpg",
    "fig14-arm-direction.jpg": "fig14-arm-direction.jpg",
    "fig15-power.jpg": "fig15-power.jpg",
    "fig16-power-output.jpg": "fig16-power-output.jpg",
    "fig17-controller-board.jpg": "fig17-controller-board.jpg",
    "fig18-arm-connector.jpg": "fig18-arm-connector.jpg",
    "fig19-electrical-overall.jpg": "fig19-electrical-overall.jpg",
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
    # 图 10 原来是 fig10a/b/c 三张并排的「遥操形态」。用户砍掉左右两张，只留中间
    # 延长件那张，于是它不再需要拼接，挪到下面的 SINGLES 里出图。
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
