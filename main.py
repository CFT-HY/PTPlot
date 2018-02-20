#!/usr/bin/env python3
# enable debugging
import cgitb
cgitb.enable()
print(r"Content-type: text/html")

import math, sys, string
import base64
import cgi
import time

start = time.time()

import SNR, powerspectrum

form = cgi.FieldStorage()

def print_start():
    print(r"""
    <html>
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
    print(r"""
    <p>
    Generating this page took approximately {0:0.1f} seconds.
    </p>
    """.format(time.time() - start))
    
    print(r"""
    <p><em><a href="https://bitbucket.org/dweir/ptplot">PTPlot</a></em>
    by
    <a href="http://www.helsinki.fi/~weir/">David Weir</a>
    on behalf of the LISA Cosmology Working Group
    </p>
    </body>
    </html>""")

def print_form():
    print(r"""
    <form action="main.py" method="post">
    Wall velocity $v_\mathrm{w}$:
    <input type="text" name="vw" value="0.9">
    <br/>
    Phase transition temperature $T_*$:
    <input type="text" name="Tstar" value="120"> GeV
    <br/>
    <input type="submit" value="Submit">
    </form>
    <p>(all other parameters have 'reasonable' defaults;
    in particular, $\alpha_{T_*} \approx 0.1$,
    and $H_*/\beta =0.1$ - these will be adjustable soon)</p>
    <p>Todo:
    <ul>
    <!-- <li>SNR plot</li> -->
    <li>Tidy up backend</li>
    <li>Adjust all parameters</li>
    <li>Download PDF</li>
    <!-- <li>Change sensitivity curve/mission profile</li> -->
    <li>Preselect benchmark points</li>
    </ul>
    """)


def print_parameter_error(what):
    print(r"""
    <div style="color: red">
    <p>There is an error in your parameters:</p>
    <blockquote>%s</blockquote>
    </div>"""
          % what)
    


print_start()
    
if "vw" not in form or "Tstar" not in form:
    print_form()
    print_end()
    sys.exit(0)


def vw_error():
    print_parameter_error("""
    vw must be a floating point number
    between 0 and 1""")
    print_form()
    print_end()
    sys.exit(0)


try:
    vw = float(form["vw"].value)
except (KeyError, ValueError) as e:
    vw_error()

if vw <= 0 or vw > 1:
    vw_error()
    
def Tstar_error():
    print_parameter_error("""
    $T_*$ must be a floating point number
    between 0 and 1000""")
    print_form()
    print_end()
    sys.exit(0)

    
try:
    Tstar = float(form["Tstar"].value)

except (KeyError, ValueError) as e:
    Tstar_error()
    
if Tstar <= 0 or Tstar > 1000:
    Tstar_error()

    

def inline_image(image_sio):

    imgStr = "data:image/png;base64,"

    imgStr += base64.b64encode(image_sio.read()).decode()

    print("""
    <img src="%s"></img>
    """ % (imgStr))

sio_PS = powerspectrum.get_PS_image(Tstar=Tstar, vw=vw)
sio_SNR = SNR.get_SNR_image(Tstar=Tstar, vw=vw)
    
inline_image(sio_PS)
inline_image(sio_SNR)

print_form()
print_end()
