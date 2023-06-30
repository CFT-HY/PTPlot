#!/usr/bin/env python3
import sys
from lxml import etree

if not len(sys.argv) == 3:
    sys.stderr.write('Usage: %s <input> <output>\n')
    sys.exit(1)

inputfile = sys.argv[1]
outputfile = sys.argv[2]
    
tree = etree.parse(open(inputfile))

# watermark
to_remove = tree.xpath("/svg:svg/svg:g/svg:g[@id=\"text_23\"]",
  namespaces={"svg": "http://www.w3.org/2000/svg"})[0]
g = to_remove.getparent()
g.remove(to_remove)

# date stamp
to_remove = tree.xpath("/svg:svg/svg:g/svg:g[@id=\"text_24\"]",
  namespaces={"svg": "http://www.w3.org/2000/svg"})[0]
g = to_remove.getparent()
g.remove(to_remove)


with open(outputfile, "wb") as o:
    o.write(etree.tostring(tree, pretty_print=True))

    
