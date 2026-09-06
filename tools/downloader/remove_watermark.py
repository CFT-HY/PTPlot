#!/usr/bin/env python3

"""Remove the watermark from PTPlot figures."""

import sys
import typing as tp

from lxml import etree

#: The script takes the input and output file paths as arguments.
N_ARGS: int = 3

if len(sys.argv) != N_ARGS:
    print("Usage: %s <input> <output>", file=sys.stderr)
    sys.exit(1)

inputfile = sys.argv[1]
outputfile = sys.argv[2]

with open(inputfile, "rb") as file:
    tree = etree.parse(file)

# matches annotations: watermark and timestamp
to_remove = tp.cast("list[etree._Element]", tree.xpath(  # noqa: SLF001
    "/svg:svg/svg:g/svg:g[re:match(@id, \"text_*\")]",
    namespaces={"svg": "http://www.w3.org/2000/svg","re": "http://exslt.org/regular-expressions"}))

for t in to_remove:
    g = t.getparent()
    if g is None:
        raise ValueError(f"The element {t} has no parent.")
    g.remove(t)

with open(outputfile, "wb") as o:
    o.write(etree.tostring(tree, pretty_print=True))
