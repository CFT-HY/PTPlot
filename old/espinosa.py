import math

def ubarf(vw, alpha):
    return math.sqrt((3.0/4.0)*kappav(vw,alpha)*alpha)

def kappav(vw, alpha):
#    if vw > 0.9:
#        return alpha/(0.73 + 0.083*math.sqrt(alpha) + alpha)
#    print alpha/(0.73 + 0.083*math.sqrt(alpha) + alpha)

    kappaA = math.pow(vw,6.0/5.0)*6.9*alpha/ \
             (1.36 - 0.037*math.sqrt(alpha) + alpha)
    kappaB = math.pow(alpha,2.0/5.0)/ \
             (0.017 + math.pow(0.997 + alpha,2.0/5.0))
    kappaC = math.sqrt(alpha)/(0.135 + math.sqrt(0.98 + alpha))
    kappaD = alpha/(0.73 + 0.083*math.sqrt(alpha) + alpha)

    cs = math.pow(1.0/3.0,0.5)

    xiJ = (math.sqrt((2.0/3.0)*alpha + alpha*alpha) + math.sqrt(1.0/3.0))/(1+alpha)

    if vw < cs:
        return math.pow(cs,11.0/5.0)*kappaA*kappaB/ \
            (math.pow(cs,11.0/5.0)
             - math.pow(vw,11.0/5.0)*kappaB
             + vw*math.pow(cs,6.0/5.0)*kappaA)
    else:
        return math.pow(cs - 1, 3.0)*math.pow(xiJ,5.0/2.0)* \
            math.pow(vw,-5.0/2.0)*kappaC*kappaD/ \
            ((math.pow(xiJ-1,3.0) - math.pow(vw -1,3.0))* \
             math.pow(xiJ,5.0/2.0)*kappaC + math.pow(vw - 1,3.0)*kappaD)
