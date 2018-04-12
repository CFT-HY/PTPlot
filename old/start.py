#!/usr/bin/env python3
# enable debugging
import cgitb
cgitb.enable()
print("Content-type: text/html\n")

import matplotlib
matplotlib.use("Agg")
import numpy as np
import matplotlib.pyplot as plt
#import cStringIO
import io
import base64

matplotlib.rcParams['axes.unicode_minus'] = False
fig, ax = plt.subplots()
ax.plot(10*np.random.randn(100), 10*np.random.randn(100), 'o')
ax.set_title('Using hyphen instead of Unicode minus')

sio = io.BytesIO()
plt.savefig(sio, format="png")
sio.seek(0)

# Build your matplotlib image in a iostring here
# ......
#

# Initialise the base64 string
#
imgStr = "data:image/png;base64,"

imgStr += base64.b64encode(sio.read()).decode()

print("""<html><body>
# ...a bunch of text and html here...
    <img src="%s"></img>
#...more text and html...
    </body></html>
""" % imgStr)
