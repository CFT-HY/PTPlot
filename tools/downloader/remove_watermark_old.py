#!/usr/bin/env python3

"""Remove the watermark from PTPlot figures (old version)"""

import sys

from lxml import etree


if len(sys.argv) != 3:
    print("Usage: %s <input> <output>", file=sys.stderr)
    sys.exit(1)

inputfile = sys.argv[1]
outputfile = sys.argv[2]

with open(inputfile, "rb") as file:
    tree = etree.parse(file)

# watermark
to_remove = tree.xpath(
    "/svg:svg/svg:g/svg:g[@id=\"text_23\"]",
    namespaces={"svg": "http://www.w3.org/2000/svg"})[0]
g = to_remove.getparent()
g.remove(to_remove)

# date stamp
to_remove = tree.xpath(
    "/svg:svg/svg:g/svg:g[@id=\"text_24\"]",
    namespaces={"svg": "http://www.w3.org/2000/svg"})[0]
g = to_remove.getparent()
g.remove(to_remove)

with open(outputfile, "wb") as o:
    o.write(etree.tostring(tree, pretty_print=True))
