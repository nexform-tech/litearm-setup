#!/usr/bin/env python3
"""Check both usage guides' structural invariants. Run before every commit.

    python3 build/check_doc.py

The two editions share one invariant that breaks silently and is expensive to
notice by eye: LaTeX numbers the captions itself, from the order the figures appear
in the Markdown, so the Nth figure of a document must be `images/figNN-*` in the
Chinese edition and `images-en/figNN-*` in the English one. Renumber a figure's
file and the caption follows the file, but every "see **图 N**" / "see **Figure N**"
back reference in the prose keeps pointing where it did before. This script fails on
that mismatch, and on the smaller mistakes that surround it.

The two editions are translations of one document, so they are also required to
carry the same figures in the same order. The nineteenth figure is a photograph and
the twentieth and twenty-first are interface screenshots, but the rule is the same:
a file renumbered after its caption was written breaks a back reference.

Exit status is 0 when everything checks out, 1 with one line per problem.
"""
import collections
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMPOSE = os.path.join(ROOT, "build", "compose_figures.py")
IMAGE_DIRS = ("images", os.path.join("images", "parts"))

FIGURE_REF = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)")

# One entry per edition: the source, the directory its figures are composed into,
# how the prose cites a figure, what a figure is called there, and the phrasings
# that would make a sentence depend on the layout. The guide is rendered both to a
# PDF and to Word, where a page break lands somewhere else, so no sentence may
# depend on where a figure sits on the page.
Doc = collections.namedtuple("Doc", "source figure_dir cited label directional")

DOCS = (
    Doc(
        source="LITEARM-SE机械臂使用教程.md",
        figure_dir="images",
        cited=re.compile(r"图\s*(\d+)"),
        label="图",
        directional=("下图", "上图", "如下图", "如上图", "左图", "右图"),
    ),
    Doc(
        source="LITEARM-SE-user-guide.md",
        figure_dir="images-en",
        cited=re.compile(r"figure\s*(\d+)", re.IGNORECASE),
        label="Figure",
        directional=(
            "figure below", "figure above", "following figure", "next figure",
            "preceding figure", "previous figure", "left figure", "right figure",
            "figure on the left", "figure on the right",
        ),
    ),
)


def fail(problems, message):
    problems.append(message)


def check(doc, problems):
    """Check one edition and return its figure references, in document order."""
    path = os.path.join(ROOT, doc.source)
    if not os.path.exists(path):
        sys.exit(f"missing the guide source: {path}")
    text = open(path, encoding="utf-8").read()

    refs = FIGURE_REF.findall(text)
    if not refs:
        fail(problems, f"{doc.source} references no figure at all")

    # 1. Every referenced image exists, and the Nth one is figNN.
    for number, (alt, target) in enumerate(refs, start=1):
        if not os.path.exists(os.path.join(ROOT, target)):
            fail(problems, f"{doc.source}: {doc.label} {number}: {target} does not exist")
        expected = f"{doc.figure_dir}/fig{number:02d}-"
        if not target.startswith(expected):
            fail(
                problems,
                f"{doc.source}: {doc.label} {number}: figure {number} of the document "
                f"is {target}, but its caption will be numbered {doc.label} {number}. "
                f"Expected a file named {expected}*",
            )

    # 2. No caption repeats a figure number: LaTeX writes "图 N." / "Figure N." itself.
    for number, (alt, target) in enumerate(refs, start=1):
        if doc.cited.search(alt):
            fail(
                problems,
                f"{doc.source}: {doc.label} {number}: the caption {alt!r} contains its "
                f"own figure number; the caption label is added automatically",
            )

    # 3. Every back reference resolves to a figure that exists.
    prose = FIGURE_REF.sub(" ", text).replace("*", "").replace("\\", "")
    for cited in sorted({int(n) for n in doc.cited.findall(prose)}):
        if not 1 <= cited <= len(refs):
            fail(
                problems,
                f"{doc.source}: the prose cites {doc.label} {cited}, but the guide has "
                f"{len(refs)} figures ({doc.label} 1-{doc.label} {len(refs)})",
            )

    # 4. No sentence depends on where a figure sits on the page.
    haystack = prose.lower()
    for phrase in doc.directional:
        if phrase in haystack:
            fail(
                problems,
                f"{doc.source}: the prose says {phrase!r}; cite the figure by number instead",
            )

    return refs


def main():
    problems = []
    checked = [(doc, check(doc, problems)) for doc in DOCS]

    # 5. Both editions carry the same figures, in the same order. They are two
    # translations of one document, so a figure present in only one of them is a
    # content difference, not a translation difference.
    if checked:
        first_doc, first_refs = checked[0]
        first_names = [os.path.basename(target) for _, target in first_refs]
        for doc, refs in checked[1:]:
            if [os.path.basename(target) for _, target in refs] != first_names:
                fail(
                    problems,
                    f"{doc.source} and {first_doc.source} do not carry the same figures "
                    f"in the same order",
                )

    # 6. Every source image the compositor names exists under an image directory.
    compose = open(COMPOSE, encoding="utf-8").read()
    for name in sorted(set(re.findall(r'"([\w.-]+\.(?:jpg|jpeg|png))"', compose))):
        if not any(os.path.exists(os.path.join(ROOT, d, name)) for d in IMAGE_DIRS):
            fail(problems, f"compose_figures.py names {name}, which is in no image directory")

    if problems:
        for problem in problems:
            print(f"FAIL {problem}")
        print(
            f"\n{len(problems)} problem(s); "
            + ", ".join(f"{len(refs)} {doc.label} in {doc.source}" for doc, refs in checked)
        )
        return 1

    for doc, refs in checked:
        print(
            f"OK: {doc.source}: {len(refs)} figures, numbered "
            f"{doc.label} 1-{doc.label} {len(refs)} in document order"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
