# litearm-setup

[English](README.md) | [简体中文](README.zh-CN.md)

LiteArm 系列机械臂的安装文档：以 PDF 形式发布的安装教程、安装视频，以及生成它们的
Markdown 源文件与构建流程。请在开箱前先读它——硬件上电本身不需要 SDK、不需要 ROS，
也不需要上位机。

教程正文为中文，因为这是随产品发货时的文档语言，也是安装视频的讲解语言。

## 安装教程

| 文件 | 说明 |
| --- | --- |
| [`LITEARM-SE机械臂安装教程.pdf`](LITEARM-SE机械臂安装教程.pdf) | 教程正文，14 页，即随产品交付的版本 |
| [`LITEARM-SE机械臂安装教程.md`](LITEARM-SE机械臂安装教程.md) | 源文件。要改就改它，不要改 PDF |
| [`build/`](build/) | 把 Markdown 变成 PDF 的构建流程 |

正文共 6 章，按实际操作的先后顺序排列——先装配、后接电与通信，这样在翻转、对位、
拧紧机械臂的过程中不会有线缆被扯动或被夹住：

| # | 章节 | 适用读者 |
| --- | --- | --- |
| 1 | 前言（含 1.1 安装路径指引） | 所有人 |
| 2 | 开箱清点 | 所有人 |
| 3 | 桌面固定 | 仅桌面固定方案 |
| 4 | 立柱安装 | 仅立柱方案 |
| 5 | 电气连接 | 所有人 |
| 6 | 安装注意事项 | 所有人 |

第 3 章与第 4 章是**二选一的两种方案，不是前后两步**：机械臂要么用安装底座加 G 型夹
固定在桌面边缘，要么装配到立柱上。两个都做，等于装了两套支架。

**先读 1.1。** 那张表说明你选的安装方式会让哪些章节成为必读、哪些可以跳过。

## 安装视频

6 分钟，960×544，在真实机械臂上完整走了一遍流程。它以 Release 附件的形式发布，而不
直接放在仓库里——73 MB 的体积会让每个只想下载 PDF 的人都在 clone 时把它拉下来：

<https://github.com/nexform-tech/litearm-setup/releases/latest>

## 构建 PDF

```bash
bash build/build.sh
```

构建会用 Markdown 源文件重新生成仓库根目录下的 `LITEARM-SE机械臂安装教程.pdf`。

| 依赖 | 说明 |
| --- | --- |
| `pandoc` | Markdown 转 LaTeX |
| `xelatex` | TeX Live，用于中文排版 |
| `python3` | `build/` 下的两个后处理步骤 |
| 字体 | Noto Serif CJK SC、Noto Sans CJK SC、Lato |

**不要直接修改 PDF。** 它是生成物，下一次构建就会覆盖。对教程的修改应当以两个文件
的形式落在同一个 commit 里——Markdown 和重新构建出的 PDF——因为「PDF 落后于源文件」
恰恰是 review 时最不容易被发现的问题。

**中文字体在 `build/a3_layout.tex` 里是按绝对路径引用的**
（`\setCJKmainfont[Path=/home/qaz/.local/share/fonts/NotoSerifSC/…]`）。如果机器上
Noto Serif CJK SC 的分区文件装在别处，构建会在字体处报错停下；把那个 `Path=` 指向
你自己的副本即可。这是目前唯一还不具备可移植性的一步。

## 修改插图

`images/` 是生成物。带手写标注的照片放在 `images/parts/`，由
`build/compose_figures.py` 负责裁切、重绘照片内的标注文字，并把由多张照片组成的插图
拼合起来：

```bash
python3 build/compose_figures.py
```

改动 `images/parts/` 下的任何文件后都要跑一次，然后重新构建 PDF。不要用
`python3 -I` 运行它：隔离模式会屏蔽用户的 site-packages，`opencv` 会导入失败。

**插图文件是按位置编号的，不是按内容。** LaTeX 会按图片在 Markdown 中出现的顺序自动
给图题编号，所以正文里的第 20 张图必须是 `images/fig20-…jpg`。重命名一个文件，图题
会跟着它变，而正文里每一处「见图 6」仍然指着原来的位置。`build/check_doc.py` 就是用来
发现这种不一致的，它在每个 pull request 上都会跑：

```bash
python3 build/check_doc.py
```

## 仓库结构

```text
litearm-setup/
├── LITEARM-SE机械臂安装教程.md     # 源文件——改它
├── LITEARM-SE机械臂安装教程.pdf    # 由 build/build.sh 构建
├── build/                          # pandoc -> LaTeX 流程与插图合成脚本
│   ├── build.sh                    # Markdown -> PDF，三遍 xelatex
│   ├── build_docx.py               # 同一份文档的 .docx，用于编辑插图
│   ├── compose_figures.py          # 裁切、标注、拼合 images/parts/
│   ├── check_doc.py                # 测试脚本
│   └── README.md                   # 构建流程的详细说明
└── images/
    ├── fig01-…-fig17….jpg          # 生成物，每张插图一个文件
    └── parts/                      # 拼成插图的原始照片
```

`build/README.md` 详细记录了排版上的各项决定——页面尺寸、能让两页各放一张插图的图片
宽度、以及印出来仍然清晰的标注字号——以及每个决定背后的实测数据。

## 相关仓库

| 仓库 | 用途 |
| --- | --- |
| [litearm-docs](https://github.com/nexform-tech/litearm-docs) | 产品文档源文件与已发布的文档站点 |
| [litearm-description](https://github.com/nexform-tech/litearm-description) | 各 LiteArm 型号的 URDF 描述 |
| [litearm-studio](https://github.com/nexform-tech/litearm-studio) | 上位机与桌面工作台 |
| [litearm-python](https://github.com/nexform-tech/litearm-python) | Python SDK |
| [litearm-cpp](https://github.com/nexform-tech/litearm-cpp) | C++ SDK |
| [litearm-ros2](https://github.com/nexform-tech/litearm-ros2) | ROS 2 驱动 |

## 仓库规范

本仓库遵循 NEXFORM ROBOTICS 的仓库统一规范：agent 操作规则见 [AGENTS.md](AGENTS.md)，
提交信息使用 Conventional Commits，合并到 `main` 后由 semantic-release 自动发版。

## 许可

Copyright © 2026 NEXFORM ROBOTICS，以
[Apache License 2.0](LICENSE) 授权。
