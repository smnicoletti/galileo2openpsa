#!/usr/bin/env python3
"""
GALILEO → Open‑PSA converter (schema‑compliant).
Dependencies: lxml
"""

import re, sys
from lxml import etree

# Parse GALILEO file
DECL = re.compile(r'^\s*toplevel\s+["]?(\w+)["]?;')
EVENT = re.compile(r'^\s*"?(\w+)"?\s+lambda=(\d*\.?\d+)(?:\s+dorm=(\d*\.?\d+))?;')
GATE = re.compile(
    r'^\s*"?(\w+)"?\s+(and|or|not|(\d+)of(\d+)|pand|fdep|spare)\s+(.+);',
    re.IGNORECASE
)

def parse_gal(path):
    top = None
    events, gates = {}, []
    with open(path) as f:
        for line in f:
            if not top:
                if m := DECL.match(line):
                    top = m.group(1)
            if m := EVENT.match(line):
                name, lam, dorm = m.groups()
                events[name] = {'lambda': float(lam), 'dorm': float(dorm) if dorm else None}
            elif m := GATE.match(line):
                name, typ, k, n, comps = m.group(1), m.group(2).lower(), m.group(3), m.group(4), m.group(5)
                nodes = [c.strip().strip('"') for c in comps.split()]
                gates.append({'name': name, 'raw_type': typ, 'k': k, 'n': n, 'comps': nodes})
    return top, events, gates

def build_opsa(top, events, gates):
    root = etree.Element("opsa-mef")
    ft = etree.SubElement(root, "define-fault-tree", name=top)

    for name, ev in events.items():
        be = etree.SubElement(ft, "define-basic-event", name=name)
        # Use <float> for simple, schema-valid numeric value
        etree.SubElement(be, "float", value=f"{ev['lambda']:.6g}")

    for g in gates:
        ge = etree.SubElement(ft, "define-gate", name=g['name'])
        if g['k'] and g['n']:
            alg = etree.SubElement(ge, "atleast", min=g['k'])
        elif g['raw_type'] in ("and","or","not","pand","fdep","spare"):
            alg = etree.SubElement(ge, g['raw_type'])
        else:
            raise ValueError(f"Unsupported gate type: {g['raw_type']}")
        for c in g['comps']:
            tag = "basic-event" if c in events else "gate"
            etree.SubElement(alg, tag, name=c)

    return root

def gal_to_opsa(inp, outp):
    top, evs, gts = parse_gal(inp)
    if not top:
        raise ValueError("Missing 'toplevel' declaration.")
    root = build_opsa(top, evs, gts)
    etree.ElementTree(root).write(outp, pretty_print=True, xml_declaration=True, encoding="UTF-8")

if __name__ == "__main__":
    if len(sys.argv)!=3:
        print("Usage: gal2opsa.py <in.gal> <out.xml>")
        sys.exit(1)
    try:
        gal_to_opsa(sys.argv[1], sys.argv[2])
        print(f"✅ Converted {sys.argv[1]} ➜ {sys.argv[2]}")
    except Exception as e:
        print("❌ Error:", e)
        sys.exit(1)
