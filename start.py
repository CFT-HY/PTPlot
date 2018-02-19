import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import cStringIO
import base64

matplotlib.rcParams['axes.unicode_minus'] = False
fig, ax = plt.subplots()
ax.plot(10*np.random.randn(100), 10*np.random.randn(100), 'o')
ax.set_title('Using hyphen instead of Unicode minus')

format = "png"
sio = cStringIO.StringIO()
plt.savefig(sio, format=format)

# Build your matplotlib image in a iostring here
# ......
#

# Initialise the base64 string
#
imgStr = "data:image/png;base64,"

imgStr += sio.getvalue().encode("base64").strip()

print "Content-type: text/html\n"
print """<html><body>
# ...a bunch of text and html here...
    <img src="%s"></img>
#...more text and html...
    </body></html>
""" % imgStr
