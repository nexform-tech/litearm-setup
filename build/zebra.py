#!/usr/bin/env python3
# A3 斑马纹：给 longtable 偶数数据行（第 2、4、6… 行，即数据行索引 1,3,5…）行首加 \rowcolor{zebra}。
# 只改写 \endhead 之后、\bottomrule 之前的数据区；\tabularnewline 全部原样保留。
import sys
path = sys.argv[1]
t = open(path, encoding="utf-8").read()

def process_env(env):
    ihead = env.find("\\endhead")
    imid = env.find("\\midrule")
    if ihead == -1 and imid == -1:
        return env
    k = (ihead + len("\\endhead")) if ihead != -1 else (imid + len("\\midrule"))
    head = env[:k]
    tail = env[k:]
    br = tail.find("\\bottomrule")
    data = tail[:br] if br != -1 else tail
    endtxt = tail[br:] if br != -1 else ""
    parts = data.split("\\tabularnewline")
    deco = []
    rowidx = 0
    for part in parts:
        if not part.strip():
            deco.append(part)
            continue
        seg = part
        if rowidx % 2 == 1:
            stripped = seg.lstrip("\n")
            n_lead = len(seg) - len(stripped)
            seg = seg[:n_lead] + "\\rowcolor{zebra} " + stripped
        deco.append(seg)
        rowidx += 1
    return head + "\\tabularnewline".join(deco) + endtxt

out = []
i = 0
while True:
    s = t.find("\\begin{longtable}", i)
    if s == -1:
        out.append(t[i:])
        break
    e = t.find("\\end{longtable}", s)
    if e == -1:
        out.append(t[i:])
        break
    out.append(t[i:s])
    out.append(process_env(t[s:e + len("\\end{longtable}")]))
    i = e + len("\\end{longtable}")
open(path, "w", encoding="utf-8").write("".join(out))
print("zebra: patched", path)
