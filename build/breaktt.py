#!/usr/bin/env python3
# 在行内 \texttt{...} 的代码里，于断点字符（_ . = / ( ,）后插入 \allowbreak，
# 让长标识符允许换行（对齐 A3 开发手册排版）。仅处理 \texttt 内联片段，不动 verbatim。
# 若 \allowbreak 后紧跟字母/数字，补一个空格做控制序列分隔符（TeX 会吞掉，不产生可见空格）。
import sys
path = sys.argv[1]
s = open(path, encoding="utf-8").read()
BRK = "\\allowbreak"
BREAK_CHARS = set("_.=/(") | {","}   # 断点后紧跟这些字符才插入（_ . = / ( ,）
ALNUM = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

def ins_brk(after_what_nextchar):
    # 返回 (prefix, used)？改为返回要追加的字符串：\allowbreak + (必要时空格)
    if after_what_nextchar in ALNUM:
        return BRK + " "
    return BRK

def find_tt(t, i):
    j = t.find("\\texttt", i)
    if j == -1:
        return None
    k = j + len("\\texttt")
    while k < len(t) and t[k] in " \t":
        k += 1
    if k >= len(t) or t[k] != "{":
        return None
    depth = 0
    p = k
    while p < len(t):
        c = t[p]
        if c == "\\":
            p += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                break
        p += 1
    if depth != 0:
        return None
    return (k + 1, p, p + 1)  # (content_start, content_end, idx_after_closing_brace)

def transform(content):
    res = []
    j = 0
    m = len(content)
    while j < m:
        c = content[j]
        if c == "\\":
            if j + 1 < m:
                esc = content[j + 1]
                res.append("\\")
                res.append(esc)
                nxt = content[j + 2] if j + 2 < m else ""
                if esc == "_":
                    res.append(ins_brk(nxt))
                j += 2
                continue
            res.append(c)
            j += 1
            continue
        if c in BREAK_CHARS:
            nxt = content[j + 1] if j + 1 < m else ""
            res.append(c)
            res.append(ins_brk(nxt))
            j += 1
            continue
        res.append(c)
        j += 1
    return "".join(res)

out = []
i = 0
while True:
    r = find_tt(s, i)
    if not r:
        out.append(s[i:])
        break
    cs, ce, ni = r
    out.append(s[i:cs])
    out.append(transform(s[cs:ce]))
    out.append(s[ce:ni])
    i = ni
open(path, "w", encoding="utf-8").write("".join(out))
print("breaktt: patched", path)
