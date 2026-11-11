#!/usr/bin/env python3
"""Fill the cover date of a generated Markdown file with the build day.

The two sources carry `@COVERDATE_ZH@` / `@COVERDATE_EN@` on the title page
instead of a literal date. build.sh runs this after the symbol pass, so a PDF
rebuilt for a content change shows the day it was built:

    版本：V1.1\qquad 日期：@COVERDATE_ZH@      ->  版本：V1.1\qquad 日期：2026年11月11日
    Version 1.1\qquad @COVERDATE_EN@            ->  Version 1.1\qquad 11 November 2026

The date is read in Beijing time, not the build machine's local zone, because
the Feishu documentation center stamps the table row from the last commit in
Beijing time and the two must name the same day.

Usage:
    python3 build/cover_date.py GENERATED.md
"""

import datetime
import sys

BEIJING = datetime.timezone(datetime.timedelta(hours=8))
MONTHS = ("January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December")


def zh(day):
    """`2026-11-11` -> `2026年11月11日`."""
    return "%d年%d月%d日" % (day.year, day.month, day.day)


def en(day):
    """`2026-11-11` -> `11 November 2026`."""
    return "%d %s %d" % (day.day, MONTHS[day.month - 1], day.year)


def stamp(text, now=None):
    """Replace both placeholders in `text`; a token that is absent stays absent."""
    now = now or datetime.datetime.now(BEIJING)
    if now.tzinfo is not None:
        now = now.astimezone(BEIJING)
    day = now.date()
    return (text.replace("@COVERDATE_ZH@", zh(day))
                .replace("@COVERDATE_EN@", en(day)))


def main(argv):
    if len(argv) != 2:
        raise SystemExit(__doc__)
    path = argv[1]
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(stamp(text))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
