# litearm-setup

[English](README.md) | [简体中文](README.zh-CN.md)

The setup documentation for the LiteArm robotic manipulator series: the guide as a
PDF, a link to the installation video, and the Markdown source and build pipeline
that produce the guide. Read it before you unpack the arm — bringing the hardware up
needs nothing from the SDK, from ROS, or from a host machine. The guide then walks
through installing the host application, activating the arm, and the first motion
test.

The guide ships in Chinese, because that is the language the product is delivered in.
An English edition of the same guide is kept here alongside it.

## The guide

| File | What it is |
| --- | --- |
| [`LITEARM-SE机械臂使用教程.pdf`](LITEARM-SE机械臂使用教程.pdf) | The Chinese guide, 20 pages, as shipped |
| [`LITEARM-SE机械臂使用教程.md`](LITEARM-SE机械臂使用教程.md) | Its source. Edit this one, never the PDF |
| [`LITEARM-SE-user-guide.pdf`](LITEARM-SE-user-guide.pdf) | The English guide, 22 pages |
| [`LITEARM-SE-user-guide.md`](LITEARM-SE-user-guide.md) | Its source, likewise |
| [`build/`](build/) | The pipeline that turns the Markdown into the PDF |

The two editions are the same document: the same chapters, the same steps, and the
same twenty-one figures under the same numbers. They differ in more than the prose —
the labels drawn into the photographs are in the language of the edition they appear
in, so the compositor writes one set of figures per language and the two sets have to
be regenerated together.

Seven chapters, in the order the work is done — assemble first, connect power and
communication second, then install the host software, so no cable is pulled or caught
while the arm is being flipped, aligned and tightened:

| # | Chapter | Who reads it |
| --- | --- | --- |
| 1 | 前言 (introduction, with 1.1 the install-path guide) | everyone |
| 2 | 开箱清点 (unpacking checklist) | everyone |
| 3 | 桌面固定 (mounting on a desktop) | desktop mounting only |
| 4 | 立柱安装 (assembling the column stand) | column mounting only |
| 5 | 电气连接 (power and communication, including installation notes) | everyone |
| 6 | 软件快速上手 (installing, activating and using the host application) | everyone |
| 7 | Q&A (common questions) | when needed |

Chapters 3 and 4 are **alternatives, not steps**: the arm is either clamped to a
desktop edge with the mounting base and G-clamps, or assembled onto the column
stand. Do both and you will have built two mounts.

**Read 1.1 first.** It is a table that says which chapters your mounting choice
makes mandatory and which one it lets you skip. Chapter titles above are quoted from
the Chinese edition; the English one has the same seven chapters in the same order.

## The installation video

《【硬核开箱】NEXFORM新元体LITEARM SE七轴机械臂来了！》 is published on Bilibili
rather than shipped with this repository:

<https://www.bilibili.com/video/BV17LJy6zEAh/>

## Building the PDF

```bash
bash build/build.sh
```

Building rewrites both PDFs in the repository root from their Markdown sources, three
xelatex passes each.

| Requirement | Notes |
| --- | --- |
| `pandoc` | Markdown to LaTeX |
| `xelatex` | TeX Live, for the CJK typesetting |
| `python3` | the two post-processing steps in `build/` |
| Fonts | Noto Serif CJK SC, Noto Sans CJK SC, Lato |

**Do not edit a PDF.** They are generated, and the next build overwrites them. A
change to the guide lands as two files in one commit — the Markdown and the rebuilt
PDF — because a PDF that lags its source is the one thing nobody notices in review.
Edit the English source only when the change concerns the English wording alone, and
change its figure set only through `build/compose_figures.py`, so that the two
editions cannot drift apart.

**The CJK font is addressed by absolute path** in `build/a3_cjk.tex`
(`\setCJKmainfont[Path=/home/qaz/.local/share/fonts/NotoSerifSC/…]`; the Chinese
edition only, the English one loads no CJK font). On a machine where the Noto Serif
CJK SC single-region files live elsewhere, the build stops with a font error; point
that `Path=` at your own copy. This is the one step that is not portable yet.

## Editing the figures

Figures 1–19 in `images/` and `images-en/` are generated; 20 and 21 are interface
screenshots copied in as taken. The photographs with their handwritten annotations
live in `images/parts/`, and `build/compose_figures.py` crops them, redraws the
in-image labels and stitches the multi-photograph figures together — the crops and
the stitches are shared by both editions, only the labels differ:

```bash
python3 build/compose_figures.py
```

Run it after touching anything under `images/parts/`, then rebuild both PDFs. Do not
run it with `python3 -I`: the isolated mode hides the user site-packages and
`opencv` stops importing.

**The figure files are numbered by position, not by content.** LaTeX numbers the
captions itself from the order the images appear in the Markdown, so the twentieth
figure of an edition must be `images/fig20-*` in the Chinese one and
`images-en/fig20-*` in the English one. Renumber a file and the caption
follows it, while every "see 图 6" or "see Figure 6" in the prose keeps pointing where
it did before. `build/check_doc.py` is what catches that — along with the two editions
drifting apart — and it runs on every pull request:

```bash
python3 build/check_doc.py
```

## Repository layout

```text
litearm-setup/
├── LITEARM-SE机械臂使用教程.md       # the Chinese source — edit this
├── LITEARM-SE机械臂使用教程.pdf      # built by build/build.sh
├── LITEARM-SE-user-guide.md          # the English source
├── LITEARM-SE-user-guide.pdf         # built by build/build.sh
├── build/                          # pandoc -> LaTeX pipeline, figure compositor
│   ├── build.sh                    # markdown -> PDF, three xelatex passes per edition
│   ├── a3_layout.tex               # the layout, shared; four names are substituted
│   ├── a3_cjk.tex                  # the CJK font and line-breaking rules (Chinese only)
│   ├── build_docx.py               # the Chinese document as .docx, for figure editing
│   ├── compose_figures.py          # crops, annotates and stitches images/parts/
│   ├── check_doc.py                # the test suite
│   └── README.md                   # the pipeline in detail, in Chinese
├── images/                         # the Chinese edition's figures
│   ├── fig01-…-fig19….jpg          # composed, one per figure
│   ├── fig20-…-fig21….png          # interface screenshots, used as taken
│   ├── cover_litearm_*.png         # cover art, shared by both editions
│   └── parts/                      # the photographs the figures are built from
└── images-en/                      # the English edition's figures, same file names
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
