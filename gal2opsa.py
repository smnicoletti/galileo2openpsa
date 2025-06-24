#!/usr/bin/env python3
"""
GALILEO → Open‑PSA MEF XML converter (strict schema‑compliant version).
Dependencies: lxml
"""

import re, sys
from lxml import etree

# Parse declarations, events, and all gate types
DECL = re.compile(r'^\s*toplevel\s+["]?(\w+)["]?;')
EVENT = re.compile(r'^\s*"?(\w+)"?\s+lambda=(\d*\.?\d+)(?:\s+dorm=(\d*\.?\d+))?;')
GATE = re.compile(r'^\s*"?(\w+)"?\s+(\w+)\s+(.+);', re.IGNORECASE)

# Schema-compliant gates only
SUPPORTED_GATES = {"and", "or", "not"}
def is_kofn(gtype): return re.fullmatch(r"\d+of\d+", gtype)

def parse_gal(path):
    top = None
    events, gates = {}, []
    unsupported = []

    with open(path) as f:
        for lineno, line in enumerate(f, 1):
            if not top and (m := DECL.match(line)):
                top = m.group(1)
            elif m := EVENT.match(line):
                name, lam, dorm = m.groups()
                events[name] = {
                    'lambda': float(lam),
                    'dorm': float(dorm) if dorm else None
                }
            elif m := GATE.match(line):
                name, gtype, comps = m.group(1), m.group(2).lower(), m.group(3)
                comp_list = [c.strip().strip('"') for c in comps.split()]
                if gtype not in SUPPORTED_GATES and not is_kofn(gtype):
                    unsupported.append((lineno, name, gtype))
                gates.append({'name': name, 'raw_type': gtype, 'comps': comp_list})
    
    if unsupported:
        for ln, name, typ in unsupported:
            print(f"❌ Unsupported gate type '{typ}' in gate '{name}' on line {ln}")
        raise ValueError("Unsupported gates detected. Only 'and', 'or', 'not', and k-of-n are supported.")

    return top, events, gates

def build_opsa(top, events, gates):
    root = etree.Element("opsa-mef")
    ft = etree.SubElement(root, "define-fault-tree", name=top)

    for name, ev in events.items():
        be = etree.SubElement(ft, "define-basic-event", name=name)
        etree.SubElement(be, "float", value=f"{ev['lambda']:.6g}")

    for g in gates:
        ge = etree.SubElement(ft, "define-gate", name=g['name'])

        if is_kofn(g['raw_type']):
            k, n = map(str, g['raw_type'].split("of"))
            etree.SubElement(ge, "atleast", min=k)
        else:
            etree.SubElement(ge, g['raw_type'])

        for c in g['comps']:
            tag = "basic-event" if c in events else "gate"
            etree.SubElement(ge[-1], tag, name=c)

    return root

def gal_to_opsa(inp, outp):
    top, events, gates = parse_gal(inp)
    if not top:
        raise ValueError("Missing 'toplevel' declaration.")
    root = build_opsa(top, events, gates)
    etree.ElementTree(root).write(outp, pretty_print=True, xml_declaration=True, encoding="UTF-8")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: gal2opsa.py <input.gal> <output.xml>")
        sys.exit(1)
    try:
        gal_to_opsa(sys.argv[1], sys.argv[2])
        print(f"✅ Converted {sys.argv[1]} ➜ {sys.argv[2]}")
    except Exception as e:
        print("❌ Error:", e)
        sys.exit(1)
