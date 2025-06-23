#!/usr/bin/env python3
"""
GALILEO → Open-PSA converter (schema-compliant incl. cov/repair/repl/dorm).

Dependencies
------------
pip install lxml
"""

import re, sys
from lxml import etree

# ─────────── regexes ───────────
DECL = re.compile(r'^\s*toplevel\s+"?(\w+)"?;')
EVENT = re.compile(
    r'^\s*"?(\w+)"?\s+'
    r'lambda=(\d*\.?\d+)'          # λ
    r'(?:\s+cov=(\d*\.?\d+))?'     # coverage
    r'(?:\s+res=(\d*\.?\d+))?'     # repair
    r'(?:\s+repl=(\d*\.?\d+))?'    # replacement
    r'(?:\s+dorm=(\d*\.?\d+))?'    # dormancy
    r'\s*;'
)
GATE = re.compile(
    r'^\s*"?(\w+)"?\s+'
    r'(and|or|not|(\d+)of(\d+)|pand|fdep|spare)\s+'
    r'(.+);',
    re.IGNORECASE,
)

# ─────────── parse GAL ───────────
def parse_gal(path):
    top, events, gates = None, {}, []
    with open(path, encoding="utf-8") as fh:
        for ln in fh:
            if (not top) and (m := DECL.match(ln)):
                top = m.group(1)

            if m := EVENT.match(ln):
                name, lam, cov, res, repl, dorm = m.groups()
                events[name] = {
                    "lambda": float(lam),
                    "cov":   float(cov)   if cov   else None,
                    "res":   float(res)   if res   else None,
                    "repl":  float(repl)  if repl  else None,
                    "dorm":  float(dorm)  if dorm  else None,
                }

            elif m := GATE.match(ln):
                name, typ, k, n, comps = m.group(1), m.group(2).lower(), m.group(3), m.group(4), m.group(5)
                gates.append(
                    {
                        "name": name,
                        "raw_type": typ,
                        "k": k,
                        "n": n,
                        "comps": [c.strip().strip('"') for c in comps.split()],
                    }
                )
    return top, events, gates

# ─────────── helpers ───────────
def add_attributes(be_elem, ev):
    extras = {
        "coverage":    ev["cov"],
        "repair":      ev["res"],
        "replacement": ev["repl"],
        "dormancy":    ev["dorm"],
    }
    if any(v is not None for v in extras.values()):
        attrs = etree.SubElement(be_elem, "attributes")
        for key, val in extras.items():
            if val is not None:
                etree.SubElement(attrs, "attribute", name=key, value=f"{val:.6g}")

def build_opsa(top, events, gates):
    root = etree.Element("opsa-mef")
    ft   = etree.SubElement(root, "define-fault-tree", name=top)

    for name, ev in events.items():
        be = etree.SubElement(ft, "define-basic-event", name=name)
        add_attributes(be, ev)                              # attributes (if any)
        etree.SubElement(be, "float", value=f"{ev['lambda']:.6g}")  # expression

    for g in gates:
        ge  = etree.SubElement(ft, "define-gate", name=g["name"])
        alg = (
            etree.SubElement(ge, "atleast", min=g["k"])
            if g["k"] and g["n"] else
            etree.SubElement(ge, g["raw_type"])
        )
        for c in g["comps"]:
            etree.SubElement(alg, "basic-event" if c in events else "gate", name=c)

    return root

# ─────────── CLI wrapper ───────────
def gal_to_opsa(src, dst):
    top, evs, gts = parse_gal(src)
    if not top:
        raise ValueError("Missing 'toplevel' declaration.")
    etree.ElementTree(build_opsa(top, evs, gts)).write(
        dst, pretty_print=True, xml_declaration=True, encoding="UTF-8"
    )

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: gal2opsa.py <input.gal> <output.xml>")
        sys.exit(1)
    try:
        gal_to_opsa(sys.argv[1], sys.argv[2])
        print(f"✅ Converted {sys.argv[1]} → {sys.argv[2]}")
    except Exception as exc:
        print("❌ Error:", exc)
        sys.exit(1)
