# litearm-setup

[English](README.md) | [简体中文](README.zh-CN.md)

The installation documentation for the LiteArm robotic manipulator series: the guide
as a PDF, a link to the installation video, and the Markdown source and build
pipeline that produce the guide. Read it before you unpack the arm — bringing the
hardware up needs nothing from the SDK, from ROS, or from a host machine.

The guide is written in Chinese, because that is the language the document ships in
with the product.

## The guide

| File | What it is |
| --- | --- |
| [`LITEARM-SE机械臂安装教程.pdf`](LITEARM-SE机械臂安装教程.pdf) | The guide, 15 pages, as shipped |
| [`LITEARM-SE机械臂安装教程.md`](LITEARM-SE机械臂安装教程.md) | The source. Edit this one, never the PDF |
| [`build/`](build/) | The pipeline that turns the Markdown into the PDF |

Six chapters, in the order the work is done — assemble first, connect power and
communication second, so no cable is pulled or caught while the arm is being
flipped, aligned and tightened:

| # | Chapter | Who reads it |
| --- | --- | --- |
| 1 | 前言 (introduction, with 1.1 the install-path guide) | everyone |
| 2 | 开箱清点 (unpacking checklist) | everyone |
| 3 | 桌面固定 (mounting on a desktop) | desktop mounting only |
| 4 | 立柱安装 (assembling the column stand) | column mounting only |
| 5 | 电气连接 (power and communication) | everyone |
| 6 | 安装注意事项 (installation notes) | everyone |

Chapters 3 and 4 are **alternatives, not steps**: the arm is either clamped to a
desktop edge with the mounting base and G-clamps, or assembled onto the column
stand. Do both and you will have built two mounts.

**Read 1.1 first.** It is a table that says which chapters your mounting choice
makes mandatory and which one it lets you skip.

## The installation video

《【硬核开箱】NEXFORM新元体LITEARM SE七轴机械臂来了！》 is published on Bilibili
rather than shipped with this repository:

<https://www.bilibili.com/video/BV17LJy6zEAh/>

## Building the PDF

```bash
bash build/build.sh
```

Building rewrites `LITEARM-SE机械臂安装教程.pdf` in the repository root from the
Markdown source.

| Requirement | Notes |
| --- | --- |
| `pandoc` | Markdown to LaTeX |
| `xelatex` | TeX Live, for the CJK typesetting |
| `python3` | the two post-processing steps in `build/` |
| Fonts | Noto Serif CJK SC, Noto Sans CJK SC, Lato |

**Do not edit the PDF.** It is generated, and the next build overwrites it. A change
to the guide lands as two files in one commit — the Markdown and the rebuilt PDF —
because a PDF that lags its source is the one thing nobody notices in review.

**The CJK font is addressed by absolute path** in `build/a3_layout.tex`
(`\setCJKmainfont[Path=/home/qaz/.local/share/fonts/NotoSerifSC/…]`). On a machine
where the Noto Serif CJK SC single-region files live elsewhere, the build stops with
a font error; point that `Path=` at your own copy. This is the one step that is not
portable yet.

## Editing the figures

`images/` is generated. The photographs with their handwritten annotations live in
`images/parts/`, and `build/compose_figures.py` crops them, redraws the in-image
labels and stitches the multi-photograph figures together:

```bash
python3 build/compose_figures.py
```

Run it after touching anything under `images/parts/`, then rebuild the PDF. Do not
run it with `python3 -I`: the isolated mode hides the user site-packages and
`opencv` stops importing.

**The figure files are numbered by position, not by content.** LaTeX numbers the
captions itself from the order the images appear in the Markdown, so the twentieth
figure in the document must be `images/fig20-something.jpg`. Renumber a file and the
caption follows it, while every "see 图 6" in the prose keeps pointing where it did
before. `build/check_doc.py` is what catches that, and it runs on every pull request:

```bash
python3 build/check_doc.py
```

## Repository layout

```text
litearm-setup/
├── LITEARM-SE机械臂安装教程.md     # the source — edit this
├── LITEARM-SE机械臂安装教程.pdf    # built by build/build.sh
├── build/                          # pandoc -> LaTeX pipeline, figure compositor
│   ├── build.sh                    # markdown -> PDF, three xelatex passes
│   ├── build_docx.py               # the same document as .docx, for figure editing
│   ├── compose_figures.py          # crops, annotates and stitches images/parts/
│   ├── check_doc.py                # the test suite
│   └── README.md                   # the pipeline in detail, in Chinese
└── images/
    ├── fig01-…-fig19….jpg          # generated, one per figure
    └── parts/                      # the photographs the figures are built from
```

`build/README.md` describes the typesetting decisions in detail — the page geometry,
the figure width that keeps two figures on a page, the label font size that survives
printing — along with the measurements behind each of them. It is in Chinese, like
the document it describes.

## Related repositories

| Repository | Role |
| --- | --- |
| [litearm-docs](https://github.com/nexform-tech/litearm-docs) | Product documentation source and published documentation site |
| [litearm-description](https://github.com/nexform-tech/litearm-description) | URDF descriptions of every LiteArm model |
| [litearm-studio](https://github.com/nexform-tech/litearm-studio) | Host application and desktop studio |
| [litearm-python](https://github.com/nexform-tech/litearm-python) | Python SDK |
| [litearm-cpp](https://github.com/nexform-tech/litearm-cpp) | C++ SDK |
| [litearm-ros2](https://github.com/nexform-tech/litearm-ros2) | ROS 2 driver |

## Repository standards

This repository follows the shared NEXFORM ROBOTICS repository standards: the agent
operating rules in [AGENTS.md](AGENTS.md), Conventional Commits, and automated
semantic-release versioning on every merge to `main`.

## License

Copyright © 2026 NEXFORM ROBOTICS. Licensed under the
[Apache License 2.0](LICENSE).
