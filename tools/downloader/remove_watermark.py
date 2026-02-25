#!/usr/bin/env python3

"""Remove the watermark from PTPlot figures"""

import sys

from lxml import etree


if len(sys.argv) != 3:
    print("Usage: %s <input> <output>", file=sys.stderr)
    sys.exit(1)

inputfile = sys.argv[1]
outputfile = sys.argv[2]

with open(inputfile, "rb") as file:
    tree = etree.parse(file)

# matches annotations: watermark and timestamp
to_remove = tree.xpath(
    "/svg:svg/svg:g/svg:g[re:match(@id, \"text_*\")]",
    namespaces={"svg": "http://www.w3.org/2000/svg","re": "http://exslt.org/regular-expressions"})

for t in to_remove:
    g = t.getparent()
    g.remove(t)

with open(outputfile, "wb") as o:
    o.write(etree.tostring(tree, pretty_print=True))
