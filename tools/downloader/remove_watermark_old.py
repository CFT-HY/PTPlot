#!/usr/bin/env python3

"""Remove the watermark from PTPlot figures (old version)."""

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

# watermark
to_remove = tp.cast("list[etree._Element]", tree.xpath(  # noqa: SLF001
    "/svg:svg/svg:g/svg:g[@id=\"text_23\"]",
    namespaces={"svg": "http://www.w3.org/2000/svg"}))[0]
g = to_remove.getparent()
if g is None:
    raise ValueError(f"The element {to_remove} has no parent.")
g.remove(to_remove)

# date stamp
to_remove = tp.cast("list[etree._Element]", tree.xpath(  # noqa: SLF001
    "/svg:svg/svg:g/svg:g[@id=\"text_24\"]",
    namespaces={"svg": "http://www.w3.org/2000/svg"}))[0]
g = to_remove.getparent()
if g is None:
    raise ValueError(f"The element {to_remove} has no parent.")
g.remove(to_remove)

with open(outputfile, "wb") as o:
    o.write(etree.tostring(tree, pretty_print=True))
