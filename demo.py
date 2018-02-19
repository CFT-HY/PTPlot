#!/usr/bin/env python3
# enable debugging
import cgitb
cgitb.enable()
print("Content-type: text/html\n")

import math, sys, string

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import io, base64
import scipy.optimize as spopt
import cgi
import curves

form = cgi.FieldStorage()
if "vw" not in form:
    print("""<html><body>
    <form action="demo.py">
    Wall velocity: <input type="text" name="vw" value="0.44">
    <input type="submit" value="Submit">
    </form>
    </body></html>""")
    sys.exit(0)


vw = float(form["vw"].value)
curves_ps = curves.PowerSpectrum(vw)

# setup latex plotting
plt.rc('text', usetex=True)
plt.rc('font', family='serif')
# make font size bigger
matplotlib.rcParams.update({'font.size': 16})
# but make legend smaller
matplotlib.rcParams.update({'legend.fontsize': 14})

f, sensitivity \
    = np.loadtxt('Sens_L6A2M5N2P2D28.txt',usecols=[0,3],unpack=True)

plt.fill_between(f,sensitivity,1,alpha=0.3, label=r'LISA sensitivity')
plt.plot(f, curves_ps.power_spectrum_sw(f), 'r', label=r'$\Omega_\mathrm{sw}$')
plt.plot(f, curves_ps.power_spectrum_turb(f), 'b', label=r'$\Omega_\mathrm{turb}$')
plt.plot(f, curves_ps.power_spectrum(f), 'k', label=r'Total')
plt.xlabel(r'$f\,\mathrm{(Hz)}$')
plt.ylabel(r'$h^2 \, \Omega_\mathrm{GW}(f)$')
plt.xlim([1e-5,0.1])
plt.ylim([1e-16,1e-8])
plt.yscale('log', nonposy='clip')
plt.xscale('log', nonposx='clip')
plt.legend(loc='upper right')
plt.tight_layout()

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
    <img src="%s"></img>
<form action="demo.py">
  Wall velocity: <input type="text" name="vw" value="0.44">
  <input type="submit" value="Submit">
</form>
    </body></html>
""" % imgStr)
