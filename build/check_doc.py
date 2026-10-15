#!/usr/bin/env python3
"""Check the installation guide's structural invariants. Run before every commit.

    python3 build/check_doc.py

The document has one invariant that breaks silently and is expensive to notice by
eye: LaTeX numbers the captions itself, from the order the figures appear in the
Markdown, so the Nth figure in the document must be `images/figNN-*.jpg`. Renumber
a figure's file and the caption follows the file, but every "see **图 N**" back
reference in the prose keeps pointing where it did before. This script fails on
that mismatch, and on the smaller mistakes that surround it.

Exit status is 0 when everything checks out, 1 with one line per problem.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GUIDE = os.path.join(ROOT, "LITEARM-SE机械臂安装教程.md")
COMPOSE = os.path.join(ROOT, "build", "compose_figures.py")
IMAGE_DIRS = ("images", os.path.join("images", "parts"))

FIGURE_REF = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)")
CITED = re.compile(r"图\s*(\d+)")
# The guide is rendered both to a PDF and to Word, where a page break lands
# somewhere else, so no sentence may depend on where a figure sits on the page.
DIRECTIONAL = ("下图", "上图", "如下图", "如上图", "左图", "右图")


def fail(problems, message):
    problems.append(message)


def main():
    problems = []

    if not os.path.exists(GUIDE):
        sys.exit(f"missing the guide source: {GUIDE}")
    text = open(GUIDE, encoding="utf-8").read()

    refs = FIGURE_REF.findall(text)
    if not refs:
        fail(problems, "the guide references no figure at all")

    # 1. Every referenced image exists, and the Nth one is figNN.
    for number, (alt, target) in enumerate(refs, start=1):
        if not os.path.exists(os.path.join(ROOT, target)):
            fail(problems, f"图 {number}: {target} does not exist")
        expected = f"images/fig{number:02d}-"
        if not target.startswith(expected):
            fail(
                problems,
                f"图 {number}: figure {number} of the document is {target}, "
                f"but its caption will be numbered 图 {number}. "
                f"Expected a file named {expected}*.jpg",
            )

    # 2. No caption repeats a figure number: LaTeX writes "图 N." itself.
    for number, (alt, target) in enumerate(refs, start=1):
        if CITED.search(alt):
            fail(
                problems,
                f"图 {number}: the caption {alt!r} contains its own figure number; "
                f"the caption label is added automatically",
            )

    # 3. Every back reference resolves to a figure that exists.
    prose = FIGURE_REF.sub(" ", text).replace("*", "").replace("\\", "")
    for cited in sorted({int(n) for n in CITED.findall(prose)}):
        if not 1 <= cited <= len(refs):
            fail(
                problems,
                f"the prose cites 图 {cited}, but the guide has "
                f"{len(refs)} figures (图 1-图 {len(refs)})",
            )

    # 4. No sentence depends on where a figure sits on the page.
    for phrase in DIRECTIONAL:
        if phrase in prose:
            fail(problems, f"the prose says {phrase!r}; cite the figure by number instead")

    # 5. Every source image the compositor names exists under images/.
    compose = open(COMPOSE, encoding="utf-8").read()
    for name in sorted(set(re.findall(r'"([\w.-]+\.(?:jpg|jpeg|png))"', compose))):
        if not any(os.path.exists(os.path.join(ROOT, d, name)) for d in IMAGE_DIRS):
            fail(problems, f"compose_figures.py names {name}, which is in no image directory")

    if problems:
        for problem in problems:
            print(f"FAIL {problem}")
        print(f"\n{len(problems)} problem(s); {len(refs)} figures checked")
        return 1

    print(f"OK: {len(refs)} figures, numbered 图 1-图 {len(refs)} in document order")
    return 0


if __name__ == "__main__":
    sys.exit(main())
