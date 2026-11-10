#!/usr/bin/env python3
"""把 images/parts/ 下的源图裁切、重画图内标注、必要时横向拼成整图。

中文版与英文版各出一套成图：中文版写进 images/，英文版写进 images-en/。
使用教程里的「图 6 / 图 7」由多张照片并排组成；其余为单张。
为了让 Markdown 每个图只引用一个文件，这里先把它们加工好。

每个图做三件事，顺序固定：裁切（CROPS）-> 重画图内标注（LABELS）-> 拼接（FIGURES）。
裁切框与拼接方式两个语言共用（照片本来就是同一批），只有标注文字分语言，
所以 LABELS 按语言分成两份，箭头和擦除框也跟着各自的文字排。

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
# 语言 -> 成图目录。两张照片的裁切和拼接是共用的，只有标注文字分语言。
OUT_DIRS = {
    "zh": os.path.join(ROOT, "images"),
    "en": os.path.join(ROOT, "images-en"),
}

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
    # —— 2026-11 重拍的一批 ——
    # 都是 7008x4672 的原图缩到 1600px 宽后放进 parts/，下面的坐标因此都在
    # 1600x1067 的空间里。这批照片白底、没有旧红字，所以不用 inpaint，只有新画的
    # 标注。等比裁到 4:3 上下（图 3、图 16 例外），全篇图宽才一致。
    # 图 1 固定在底板上的整机：上边缘切在臂身中部，下边缘留出底板下方的空白放标注。
    "fig01-arm-on-base.jpg": (170, 40, 1450, 1000),
    # 图 2 底板置于桌面边缘：下面那片黑色是桌子的前立面，电源线从底板中间的槽垂下去、
    # 越过桌沿，边缘才看得出来。
    "fig02-base-on-edge.jpg": (250, 60, 1450, 960),
    # 图 3 两张 G 型夹：裁到 1.78:1，右边一片灰底正好放标注。
    "fig03-clamp.jpg": (0, 100, 1600, 1000),
    # 图 4 夹紧固定：整臂加一只 G 型夹，右侧白墙是空的，图注不会被器材压住。
    "fig04-tabletop-done.jpg": (0, 60, 1300, 1035),
    # 图 7 的两张分图：脚杯、脚轮各一张，都裁 4:3，拼起来仍是横条。
    # 右边留够——脚杯、脚轮的轮子都靠画面右侧，裁窄了会把它们切掉半个。
    "fig07a-feet.jpg": (150, 100, 1150, 850),
    "fig07b-casters.jpg": (250, 100, 1250, 850),
    # 图 8 立柱与底板装配：8 颗 M10 都在画面里，下边缘留灰地毯放标注。
    "fig08-column-base.jpg": (0, 100, 1600, 1000),
    # —— 旧照片，未重拍 ——
    # 三张新照片是手机原图，方形/竖构图，统一裁到 1.33:1：只截上下、不动左右，
    # 正文里所有图就还是同一个宽度。裁掉的是背景（人、地毯、空墙），不动器材本体。
    # 1280x1280 -> 1.33:1，从顶部起留在 1280x960
    "fig11-arm-direct.jpg": (0, 180, 1280, 1140),
    # 与图 11 同一张源图（立柱内部走线与直接装配看的是同一处走线），裁切标注一致
    "fig12-column-routing.jpg": (0, 180, 1280, 1140),
    # 图 13 立柱下方出线：俯拍，底板一角在上方，编织线与插头躺在地毯上。
    # 裁 4:3 留出插头与线的走向。
    "fig13-cable-exit.jpg": (300, 0, 1500, 900),
    # 1279x1706 -> 1.12:1。上边缘压在肩部之上（两臂的电源线出处就在那里），
    # 下边缘一直留到左臂末端——按 4:3 裁到 y=1249 会把两条臂从中间切断。
    "fig14-arm-direction.jpg": (0, 290, 1279, 1430),
    # 图 9 换成 2026-11 重拍的顶部安装件：900x675 仍是 4:3。立柱顶端、法兰上的
    # 左右两颗 M6 和上方安装件都在画面里，标注压在上方那块黑板上（白描边），
    # 和旧图的做法一致。
    "fig09-top-mount.jpg": (300, 0, 1200, 675),
    # 图 10 只留中间那张延长件（原因见 FIGURES 的说明）：396x527 -> 396x297 补成 4:3，
    # 与其他图同为 364.5pt 宽 × 273pt 高。**这一张成图比原来高 110pt**（原来三张并排
    # 是 1178px 宽、只有 163pt 高），第 4 章因此排不下、全文从 15 页变成 16 页：
    # 图 10 整张下移到下一页，第 9 页页底空出 236pt。要回 15 页只能把这张再压矮——
    # 6 个 M5 孔本身的跨度就有 229px（y 103–332），压到能塞回第 9 页的 224pt（≈243px）
    # 会把最下面那颗孔的边切掉，所以没压，见 README「实测排版结果」。
    # 切成竖构图更糟：会被 0.52\textheight 顶成 253pt 宽、337pt 高，比全篇的图窄一截。
    # 切掉的上边缘是延长件上方那块没有细节的黑板，下边缘切在螺纹面以下，6 个 M5 孔都在。
    "fig10b-extension.jpg": (0, 70, 396, 367),
    # 图 15 电源接入：左边盘着的电源线与右边的电源模块都在画面里，裁 4:3。
    "fig15-power.jpg": (250, 130, 1450, 1030),
    # 图 16 电源输出：红色开关、插头与黄色 XT60 三者同框，1.73:1。
    "fig16-power-output.jpg": (100, 150, 1400, 900),
    # 图 5（桌面固定 步骤 5，看固定螺丝）与图 17（电气连接 步骤 3，看接线端子）
    # 不再是同一张照片：重拍时各拍了一张，所以两份裁切可以按各自的重点来。
    # 图 5 取俯视那张：控制板四角的螺丝在灰底板上看得清，侧视那张整幅都是黑的。
    "fig05-control-board.jpg": (300, 0, 1500, 900),
    # 图 17 控制板三路接线：上方编织线、左侧细线、下方编织线，右侧立柱底座是同一台机器
    # 的旁证，不进裁剪框也不影响。
    "fig17-controller-board.jpg": (0, 100, 1600, 1000),
    # 图 18 机械臂下方接口：留下接口所在的臂身下段，下方的白台面留给标注。
    "fig18-arm-connector.jpg": (100, 0, 1300, 900),
    # 图 19 电气连接整体：1600x1067 裁成 1300x975（4:3），三样东西和盘成一圈的线都在。
    # 右边留满 285px 白边放「电源模块」——英文 Power supply 比中文宽 86px，右边留窄会顶到图边。
    "fig19-electrical-overall.jpg": (300, 0, 1600, 975),
}

# 源图文件名 -> (字号像素, [(擦除旧字框, 新字左上角, 文字, 箭头 起→终)])，中文版。
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
LABELS_ZH = {
    # 图 1 机械臂固定于安装底板（箭头指底盘法兰上那颗螺栓）
    "fig01-arm-on-base.jpg": (31, [
        (None, (45, 830), "M5 螺丝（固定机械臂）", ((330, 850), (470, 555))),
        (None, (900, 830), "安装底板", ((915, 800), (1020, 470))),
    ]),
    # 图 3 G 型夹夹紧底板。箭头指近处那只夹子下端的压紧螺杆——螺杆是银色，
    # 压在红夹身上看不清，指到螺杆上反而最清楚。
    "fig03-clamp.jpg": (39, [
        (None, (880, 620), "G 型夹 × 2", ((866, 680), (690, 745))),
    ]),
    # 图 5 控制板固定于安装底板。字放在螺丝上方偏右的黑底板上（白描边压得住），
    # 箭头指底板右侧、控制板托板旁边那颗固定螺丝——旧图指的也是这一颗。
    "fig05-control-board.jpg": (29, [
        (None, (830, 300), "固定螺丝", ((852, 350), (792, 408))),
    ]),
    # 图 7 的两张分图。旧照片上烙着「脚杯」「底板背面」两行红字，重拍后画面里
    # 没有字，也就不再有擦除框；旧图那 4 个红圈（M16 孔）新照片上没有对应特征，
    # 标注随之取消——正文把它写在步骤 1 里，图不再重复。
    # 两张拼成 2014px 宽的横条，字号按整图算：2014 ÷ 41 ≈ 49
    "fig07a-feet.jpg": (49, [
        (None, (30, 200), "脚杯", ((180, 220), (545, 292))),
        (None, (30, 650), "底板背面", ((250, 660), (560, 620))),
    ]),
    "fig07b-casters.jpg": (49, [
        (None, (30, 120), "脚轮", ((170, 150), (360, 320))),
    ]),
    "fig08-column-base.jpg": (39, [
        (None, (60, 700), "M10 螺丝 × 8", ((300, 740), (720, 625))),
    ]),
    # 图 9 顶部安装件（900px 宽，字号 8.9 × 900 ÷ 364.5 ≈ 22px）
    # 箭头指法兰左侧那颗 M6（裁后 (145, 570)），文字压在上方黑板上、白描边，同旧图做法
    "fig09-top-mount.jpg": (22, [
        (None, (60, 250), "M6 内六角螺丝 × 4", ((235, 295), (150, 545))),
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
    # 图 13 立柱下方的出线口：箭头指向编织线从底板下沿钻出来的那一点
    "fig13-cable-exit.jpg": (29, [
        (None, (200, 760), "从立柱下方穿出", ((380, 790), (500, 268))),
    ]),
    # 图 14 左右臂方向：整张图就靠这两句标注说明。
    # 左臂根部有上下两根线：上面那根绕到安装件顶上的是电源线，下面那个 U 形回折的
    # 是关节连接线。右臂同理，电源线从根部朝上压进安装件（这个角度被立柱挡住，只能
    # 指到肩关节根部），看得见的那根 U 形回折线同样是关节连接线。
    "fig14-arm-direction.jpg": (31, [
        (None, (40, 300), "电源线朝上", ((230, 330), (505, 130))),
        (None, (1000, 85), "电源线朝上", ((1045, 130), (1018, 188))),
        (None, (1030, 420), "关节连接线", ((1030, 445), (945, 330))),
    ]),
    # 图 15 电源接入（「电源模块」指黑盒子、「电源线」指插头，两条标注都落在右下角的
    # 白底上，不从盘着的线圈中间穿过去）
    "fig15-power.jpg": (29, [
        (None, (330, 230), "电源线", ((450, 255), (640, 330))),
        (None, (770, 330), "电源模块", ((860, 320), (910, 195))),
    ]),
    # 图 16 电源输出
    "fig16-power-output.jpg": (32, [
        (None, (40, 660), "XT60 输出", ((320, 690), (740, 320))),
    ]),
    # 图 17 控制板三路接线：三条线各自标作用，不标端子块——读者要认的是「线接哪儿」，
    # 端子型号照片里本来就看不清。上方编织线通机械臂下方接口、下方黄头编织线通
    # 电源、左侧模压线通 PC。
    "fig17-controller-board.jpg": (39, [
        (None, (30, 40), "接机械臂下方接口", ((420, 70), (690, 170))),
        (None, (480, 800), "接电源", ((620, 790), (675, 500))),
        (None, (30, 620), "USB 线接 PC", ((300, 650), (430, 380))),
    ]),
    # 图 18 机械臂下方接口（箭头指编织线从臂身下端钻出来的那个口）
    "fig18-arm-connector.jpg": (29, [
        (None, (200, 760), "机械臂下方接口", ((460, 750), (720, 400))),
    ]),
    # 图 19 整桌连线（换成 2026-11 白底棚拍这张，三样东西都摆得开，字号 8.9 × 1300 ÷ 364.5 ≈ 32px）。
    # 「控制板」的字写在两个线圈之间那道白缝里（粗编织线到 y≈355，细线从 y≈430 起），
    # 箭头贴着缝往右指控制板左端；「USB 线」写在细线那个圈里面，箭头指 USB-A 金属头；
    # 「电源模块」放在右侧白边，箭头指金属外壳侧面。USB 线指的还是带 USB-A 头的细线，
    # 不是粗编织线。
    "fig19-electrical-overall.jpg": (32, [
        (None, (1035, 195), "电源模块", ((1040, 245), (990, 335))),
        (None, (190, 358), "控制板", ((300, 406), (428, 400))),
        (None, (160, 495), "USB 线", ((245, 535), (128, 634))),
    ]),
}

# 源图文件名 -> (字号像素, [(擦除旧字框, 新字左上角, 文字, 箭头 起→终)])，英文版。
# 字号、裁切框、拼接方式与中文版完全一致（两张成图要并排看，不能一大一小）；
# 变的只有文字，以及被更宽的文字顶开的锚点。
#
# 拉丁字母比汉字宽得多：同样 31px 的字号下，中文「电源线」三个字 93px，
# 英文 "Power cable" 要 186px——右边和下边的标注很容易顶出图外（顶出去就被裁掉，
# annotate() 会为此报一行警告）。所以靠右的锚点（图 14、图 18）比中文版左移了一截，
# 箭头起点仍留在文字下面，让白描边压掉线头、只露出指向器材的那一段，和中文版一样。
# 英文标注用同一支 Noto Sans CJK Bold（它的拉丁面来自 Source Sans），
# 中英两套成图里的标注因此是同一副眉眼，不必再引第二支字体。
LABELS_EN = {
    "fig01-arm-on-base.jpg": (31, [
        (None, (45, 830), "M5 screws (arm mount)", ((345, 850), (470, 555))),
        (None, (900, 830), "Base plate", ((915, 800), (1020, 470))),
    ]),
    "fig03-clamp.jpg": (39, [
        (None, (880, 620), "G-clamps × 2", ((866, 680), (690, 745))),
    ]),
    "fig05-control-board.jpg": (29, [
        (None, (830, 300), "Fixing screw", ((852, 350), (792, 408))),
    ]),
    "fig07a-feet.jpg": (49, [
        (None, (30, 200), "Foot", ((180, 220), (545, 292))),
        (None, (30, 650), "Plate underside", ((290, 660), (560, 620))),
    ]),
    "fig07b-casters.jpg": (49, [
        (None, (30, 120), "Caster", ((190, 150), (360, 320))),
    ]),
    "fig08-column-base.jpg": (39, [
        (None, (60, 700), "M10 screws × 8", ((300, 740), (720, 625))),
    ]),
    "fig09-top-mount.jpg": (22, [
        (None, (60, 250), "M6 socket screws × 4", ((235, 295), (150, 545))),
    ]),
    "fig10b-extension.jpg": (10, [
        (None, (12, 8), "M5 screws × 6", ((78, 44), (196, 62))),
    ]),
    "fig11-arm-direct.jpg": (31, [
        (None, (30, 470), "M5 screws × 6", ((215, 500), (505, 445))),
    ]),
    "fig12-column-routing.jpg": (31, [
        (None, (80, 380), "Power cable", ((285, 405), (665, 215))),
    ]),
    "fig13-cable-exit.jpg": (29, [
        (None, (140, 760), "Exits under the column", ((390, 790), (500, 268))),
    ]),
    # 图 14 的右标注最吃锚点：中文「关节连接线」5 字 155px，英文 "Joint connector"
    # 240px，照 1030 摆会写到 1270、离右缘只剩 9px，故左移到 1000。"Power cable up"
    # 233px 同理摆在右上角 (1000, 85)，下缘写到 1233 仍留 40px 余量。
    "fig14-arm-direction.jpg": (31, [
        (None, (40, 300), "Power cable up", ((295, 335), (505, 130))),
        (None, (1000, 85), "Power cable up", ((1045, 130), (1018, 188))),
        (None, (1000, 420), "Joint connector", ((1030, 445), (945, 330))),
    ]),
    "fig15-power.jpg": (29, [
        (None, (300, 230), "Power cable", ((500, 255), (640, 330))),
        (None, (740, 330), "Power supply", ((860, 320), (910, 195))),
    ]),
    "fig16-power-output.jpg": (32, [
        (None, (40, 660), "XT60 output", ((320, 690), (740, 320))),
    ]),
    "fig17-controller-board.jpg": (39, [
        (None, (30, 40), "to the arm's lower port", ((420, 70), (690, 170))),
        (None, (280, 800), "to the power supply", ((620, 790), (675, 500))),
        (None, (30, 620), "USB to PC", ((250, 650), (430, 380))),
    ]),
    "fig18-arm-connector.jpg": (29, [
        (None, (330, 760), "Arm's lower port", ((560, 750), (720, 400))),
    ]),
    "fig19-electrical-overall.jpg": (32, [
        (None, (1035, 195), "Power supply", ((1040, 245), (990, 335))),
        (None, (118, 358), "Controller board", ((300, 406), (428, 400))),
        (None, (145, 495), "USB cable", ((245, 535), (128, 634))),
    ]),
}

LABELS = {"zh": LABELS_ZH, "en": LABELS_EN}

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


def annotate(img, px, items, where=""):
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
    stroke = max(4, px // 8)
    for _, (x, y), text, _ in items:
        # 写出去的字比图还宽/还高就会被裁掉一截。这里不拦，只报——标注压在照片上，
        # 少一块只有肉眼看图才发现，而英文标注比中文宽得多，最容易撞上。
        x1, y1 = draw.textbbox((x, y), text, font=font, stroke_width=stroke)[2:]
        if x1 > img.width or y1 > img.height:
            print(f"  警告：{where} 的标注 {text!r} 画到 ({x1}, {y1})，"
                  f"超出 {img.width}x{img.height}，会被裁掉")
        draw.text((x, y), text, font=font, fill=LABEL_FILL,
                  stroke_width=stroke, stroke_fill=LABEL_HALO)
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


def prepare(name, locale):
    """读源图 -> 裁切 -> 重画标注。裁切按源图原分辨率，标注坐标按裁切后的图。"""
    path = os.path.join(PARTS_DIR, name)
    if not os.path.exists(path):
        sys.exit(f"缺少源图：{path}")
    img = Image.open(path).convert("RGB")
    if name in CROPS:
        img = img.crop(CROPS[name])
    items = LABELS[locale].get(name)
    if items:
        img = annotate(img, *items, where=f"[{locale}] {name}")
    return img


def compose(out_dir, out_name, part_names, locale):
    parts = [prepare(name, locale) for name in part_names]

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

    dst = os.path.join(out_dir, out_name)
    canvas.save(dst, "JPEG", quality=90)
    print(f"[{locale}] {out_name}  <=  {' + '.join(part_names)}"
          f"  ({canvas.width}x{canvas.height})")


def single(out_dir, out_name, part_name, locale):
    """单张图：裁切 + 重画标注后直接写出。"""
    img = prepare(part_name, locale)
    dst = os.path.join(out_dir, out_name)
    img.save(dst, "JPEG", quality=90, optimize=True)
    print(f"[{locale}] {out_name}  <=  {part_name}（单张）  ({img.width}x{img.height})")


def main():
    if not os.path.isdir(PARTS_DIR):
        sys.exit(f"找不到分图目录：{PARTS_DIR}")
    for locale, out_dir in OUT_DIRS.items():
        os.makedirs(out_dir, exist_ok=True)
        print(f"{locale} -> {os.path.relpath(out_dir, ROOT)}/")
        for out_name, part_names in FIGURES.items():
            compose(out_dir, out_name, part_names, locale)
        for out_name, part_name in SINGLES.items():
            single(out_dir, out_name, part_name, locale)


if __name__ == "__main__":
    main()
