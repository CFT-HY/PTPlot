import math
import scipy.optimize
import numpy as np

def ubarf(vw, alpha):
    return math.sqrt((3.0/4.0)*kappav(vw,alpha)*alpha)

def kappav(vw, alpha):

    kappaA = math.pow(vw,6.0/5.0)*6.9*alpha/ \
             (1.36 - 0.037*math.sqrt(alpha) + alpha)
    kappaB = math.pow(alpha,2.0/5.0)/ \
             (0.017 + math.pow(0.997 + alpha,2.0/5.0))
    kappaC = math.sqrt(alpha)/(0.135 + math.sqrt(0.98 + alpha))
    kappaD = alpha/(0.73 + 0.083*math.sqrt(alpha) + alpha)
    
    cs = math.pow(1.0/3.0,0.5)

    xiJ = (math.sqrt((2.0/3.0)*alpha + alpha*alpha) + math.sqrt(1.0/3.0))/(1+alpha)

    deltaK = -0.9*math.log((math.sqrt(alpha)/(1 + math.sqrt(alpha))))
            
    if vw < cs:
        return math.pow(cs,11.0/5.0)*kappaA*kappaB/ \
                ((math.pow(cs,11.0/5.0)
                 - math.pow(vw,11.0/5.0))*kappaB
                 + vw*math.pow(cs,6.0/5.0)*kappaA)
    elif vw > xiJ:
        return math.pow(xiJ - 1, 3.0)*math.pow(xiJ,5.0/2.0)* \
                math.pow(vw,-5.0/2.0)*kappaC*kappaD/ \
                ((math.pow(xiJ-1,3.0) - math.pow(vw -1,3.0))* \
                 math.pow(xiJ,5.0/2.0)*kappaC + math.pow(vw - 1,3.0)*kappaD)
    else:
        return kappaB + (vw - cs)*deltaK \
                + (math.pow(vw-cs,3.0)/math.pow(xiJ-cs,3.0))*(kappaC-kappaB-(xiJ-cs)*deltaK)

    
def ubarf_to_alpha(vw, this_ubarf):
    def ubarf_to_alpha_inner(vw, this_ubarf):

        def alphatrue(alpha):
            return ubarf(vw, alpha) - this_ubarf

        return scipy.optimize.brentq(alphatrue, 0.0000001, 1000.0, xtol=1e-5)
        

    vfunc = np.vectorize(ubarf_to_alpha_inner)
    return vfunc(vw, this_ubarf)
