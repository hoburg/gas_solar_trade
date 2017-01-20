import numpy as np
from numpy import sin, arctan, tan, cos, arcsin, arccos, deg2rad, rad2deg
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size':15})

def get_Eirr(latitude, day):
    """
    day is juilian day, measured from Jan 1st
    latitude is in degrees
    Returns:
    -------
    ESirr: Solar energy per unit area of from the sun Whr/m^2
    tday: time of daylight
    tnight: time of daylight
    """
    assert isinstance(day, int)

    beta = 2*np.pi*(day-1)/365
    lat = deg2rad(latitude)
    delta = (0.006918 - 0.399912*cos(beta) + 0.070257*sin(beta) -
             0.006758*cos(2*beta) + 0.000907*sin(2*beta) -
             0.002697*cos(3*beta) + 0.00148*sin(3*beta))
    tstart = 12/np.pi*arccos(-tan(delta)*tan(lat))
    tend = -tstart
    t = np.linspace(tstart, tend, 50)
    costhsun = sin(delta)*sin(lat) + cos(delta)*cos(lat)*cos(2*np.pi*t/24)

    r0 = 149.597e6 # avg distance from earth to sun km
    Reo = r0*(1 + 0.017*sin(2*np.pi*(day-93)/365))
    Psun = 63372630 # energy from sun surface W/m^2
    Rsun = 695842 # radius of the sun, km
    P0 = Psun*4*np.pi*Rsun**2/4/np.pi/Reo**2
    tau = np.exp(-0.175/costhsun)
    P = P0*costhsun# *tau
    E = np.trapz(P)*(abs(tend-tstart))/50.0
    tday = tstart*2
    tnight = 24-tstart*2
    plot = [P, t]
    return E, tday, tnight, plot

if __name__ == "__main__":
    ES, td, tn, p = get_Eirr(45, 31+28+21)
    fig, ax = plt.subplots()
    ax.plot(p[1], p[0])
    ax.set_xlabel("Time [hr]")
    ax.set_ylabel("Available Solar Power [W/m$^2$]")
    ax.grid()
    fig.savefig("lat45.pdf", bbox_inches="tight")

