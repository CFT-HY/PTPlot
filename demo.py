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
import SNR_Ubarf_Rstar_read

form = cgi.FieldStorage()

def print_start():
    print("""<html>
    <head>
    <title>PTPlot</title>
    <script type="text/x-mathjax-config">
    MathJax.Hub.Config({tex2jax: {inlineMath: [['$','$']]}});
    </script>
    <script type="text/javascript" async
    src='https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.2/MathJax.js?config=TeX-AMS_SVG'></script>
    </head>
    <body>
    <h1>PTPlot</h1>""")

def print_end():
    print("""
    <p><em><a href="https://bitbucket.org/dweir/ptplot">PTPlot</a></em>
    by
    <a href="http://www.helsinki.fi/~weir/">David Weir</a>
    on behalf of the LISA Cosmology Working Group
    </p>
    </body>
    </html>""")

def print_form():
    print(r"""<form action="demo.py" method="post">
    Wall velocity $v_\mathrm{w}$: <input type="text" name="vw" value="0.44">
    <br/>
    Phase transition temperature $T_*$: <input type="text" name="Tstar" value="180"> GeV
    <input type="submit" value="Submit">
    </form>
    <p>(all other parameters have 'reasonable' defaults; in particular,
    $\alpha_{T_*} \approx 0.1$, and $H_*/\beta =0.1$ - these will be adjustable soon)</p>
    <p>Todo:
    <ul>
    <li>SNR plot</li>
    <li>Adjust all parameters</li>
    <li>Download PDF</li>
    <li>Change sensitivity curve/mission profile</li>
    <li>Preselect benchmark points</li>
    </ul>
    """)

def print_parameter_error(what):
    print("""
    <p>There is an error in your parameters:</p>
    <blockquote>%s</blockquote>""" % what)
    

print_start()
    
if "vw" not in form:
    print_form()
    print_end()
    sys.exit(0)


try:
    vw = float(form["vw"].value)
except ValueError:
    print_parameter_error("""
    <p>vw must be a floating point number
    between 0 and 1</p>""")
    print_form()
    print_end()
    sys.exit(0)

if vw <= 0 or vw > 1:
    print_parameter_error("""
    <p>vw must be a floating point number
    between 0 and 1</p>""")
    print_form()
    print_end()
    sys.exit(0)

try:
    Tstar = float(form["Tstar"].value)
except ValueError:
    print_parameter_error("""
    <p>Tstar must be a floating point number
    between 0 and 1000</p>""")
    print_form()
    print_end()
    sys.exit(0)

if Tstar <= 0 or Tstar > 1000:
    print_parameter_error("""
    <p>Tstar must be a floating point number
    between 0 and 1000</p>""")
    print_form()
    print_end()
    sys.exit(0)

    
    
curves_ps = curves.PowerSpectrum(vw=vw, Tstar=Tstar)

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
plt.close()

sio_SNR = SNR_Ubarf_Rstar_read.get_SNR_image()



# Build your matplotlib image in a iostring here
# ......
#

def plot_image(image_sio):

    # Initialise the base64 string
    #
    imgStr = "data:image/png;base64,"

    imgStr += base64.b64encode(image_sio.read()).decode()

    print("""
    <img src="%s"></img>
    """ % (imgStr))

    
plot_image(sio)
plot_image(sio_SNR)

print_form()
print_end()
