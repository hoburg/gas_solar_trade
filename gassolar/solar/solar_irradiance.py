" solar irrandiance model "
import numpy as np
from numpy import sin, tan, cos, arccos, deg2rad
import matplotlib.pyplot as plt
from gpfit.fit import fit
import pandas as pd
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
    p: 2d array [2, 50] Power per unit area [0] and time array [1]
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

    data = {}
    for l in range(20, 61):

        ES, td, tn, p = get_Eirr(l, 355)
        params = [l]

        P = p[0][p[1] > 0]
        t = p[1][p[1] > 0]
        f = np.array([np.trapz(P[:i+1])*(t[0]-t[i])/i for i in
                      range(1, len(P)-1)])
        ends = np.array([P[i]*(t[0]-t[i]) for i in range(1, len(P))][:-1])
        Eday = np.array([P[i]*t[i] for i in range(1, len(P))][:-1])
        C = ends - f
        B = Eday + f

        x = np.log(P[1:-15])
        y = np.log(2*C[:-14])
        cn, rm = fit(x, y, 1, "MA")
        print "RMS error: %.4f" % rm
        fig, ax = plt.subplots()
        yfit = cn.evaluate(x)
        ax.plot(P[1:-15], 2*C[:-14], "o")
        ax.plot(P[1:-15], np.exp(yfit))
        ax.set_xlabel("Minimum Necessary Power $(P/S)_{\mathrm{min}}$ [W/m$^2$]")
        ax.set_ylabel("Battery Energy Needed for Sunrise/Sunset [Whr/m$^2$]")
        ax.grid()
        fig.savefig("irr_plots/Cenergyl%d.pdf" % l)
        plt.close()
        params.append(cn[0].right.c)
        params.append(cn[0].right.exp[list(cn[0].varkeys["u_fit_(0,)"])[0]])

        x = np.log(P[1:-15])
        y = np.log(2*B[:-14])
        cn, rm = fit(x, y, 1, "MA")
        print "RMS error: %.4f" % rm
        fig, ax = plt.subplots()
        yfit = cn.evaluate(x)
        ax.plot(P[1:-15], 2*B[:-14], "o")
        ax.plot(P[1:-15], np.exp(yfit))
        ax.grid()
        ax.set_xlabel("Minimum Necessary Power $(P/S)_{\mathrm{min}}$ [W/m$^2$]")
        ax.set_ylabel("Solar Cell Energy Needed for Daytime [Whr/m$^2$]")
        fig.savefig("irr_plots/Benergy%d.pdf" % l)
        plt.close()
        params.append(cn[0].right.c)
        params.append(cn[0].right.exp[list(cn[0].varkeys["u_fit_(0,)"])[0]])
        data["%d" % l] = params


    df = pd.DataFrame(data).transpose()
    colnames = ["latitude", "Cc", "Ce", "Bc", "Be"]
    df.columns = colnames
    df.to_csv("solarirrdata.csv")

    # tday = np.array([2*n for n in t])
    # tnight = 24-tday
    # x = np.log(P[1:-10])
    # y = np.log(tnight[1:-10])
    # cn, rm = fit(x, y, 1, "MA")
    # print "RMS error: %.4f" % rm
    # yfit = cn.evaluate(x)
    # fig, ax = plt.subplots()
    # ax.plot(P[1:], tnight[1:], "--")
    # ax.plot(P[1:-10], np.exp(yfit))
    # fig.savefig("pvstday.pdf")
