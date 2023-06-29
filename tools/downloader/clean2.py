#!/usr/bin/env python3
import sys, datetime
from lxml import etree

if not len(sys.argv) == 3:
    sys.stderr.write('Usage: %s <input> <output>\n')
    sys.exit(1)

inputfile = sys.argv[1]
outputfile = sys.argv[2]
    
tree = etree.parse(open(inputfile))

# matches annotations: watermark and timestamp
to_remove = tree.xpath("/svg:svg/svg:g/svg:g[re:match(@id, \"text_*\")]",
                       namespaces={"svg": "http://www.w3.org/2000/svg","re": "http://exslt.org/regular-expressions"})

for t in to_remove:
    g = t.getparent()
    g.remove(t)

with open(outputfile, "wb") as o:
    o.write(etree.tostring(tree, pretty_print=True))

    
