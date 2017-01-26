# Solar Simple Write Up

# Simple model of a Gas Powered Aircraft
```python
#inPDF: skip
from solarsimple import Mission
from gassolar.environment.wind_speeds import get_windspeed
from gassolar.solar.plotting import windalt_plot, labelLine
from solar.solar_irradiance import get_Eirr
import matplotlib.pyplot as plt
import numpy as np
plt.rcParams.update({'font.size':19})

CON = False
LAT = False
WIND = True

""" contour """

if CON:
    for av in [85, 90, 95]:
        for l in [35, 40, 45]:
            fig, ax = plt.subplots()
            M = Mission(latitude=l)
            M.substitutions.update({"f_{structures}": 
                                   ("sweep", np.linspace(0.2, 0.5, 10))})
            M.substitutions.update({"h_{batt}": 
                                   ("sweep", np.linspace(250, 400, 10))})
            M.substitutions.update({"W_{pay}": 10})
            for vk in M.varkeys["\\eta_{prop}"]:
                M.substitutions.update({vk: 0.75})
            for vk in M.varkeys["p_{wind}"]:
                M.substitutions.update({vk: av/100.0})
            for vk in M.varkeys["CDA_0"]:
                M.substitutions.update({vk: 0.002})
            M.cost = M["b"]
            sol = M.solve("mosek", skipsweepfailures=True)
            x = np.reshape(sol("f_{structures}"), [10, 10])
            y = np.reshape(sol("h_{batt}"), [10, 10])
            z = np.reshape(sol("b"), [10, 10])
            print z
            levels = np.array(range(50, 2000, 50)+ [2300])
            if av == 90:
                v = np.array(range(50, 700, 50)+ [2300])
            else:
                v = np.array(range(50, 400, 50)+ [2300])
            a = ax.contour(x, y, z, levels, colors="k")
            ax.clabel(a, v, inline=1, fmt="%d [ft]")
            ax.set_xlabel("Structural Fraction")
            ax.set_ylabel("Battery Energy Density [Whr/kg]")
            fig.savefig("../../../gassolarpaper/bcontourl%da%d.pdf" % (l, 85), 
                        bbox_inches="tight")

""" latitutde """
if LAT:
    fig, ax = plt.subplots()
    lat = np.arange(20, 50, 1)
    for a in [80, 90, 95]:
        W = []
        for l in lat:
            M = Mission(latitude=l)
            M.substitutions.update({"W_{pay}": 10})
            for vk in M.varkeys["CDA_0"]:
                M.substitutions.update({vk: 0.002})
            for vk in M.varkeys["p_{wind}"]:
                M.substitutions.update({vk: a/100.0})
            M.substitutions.update({"\\rho_{solar}": 0.25})
            M.cost = M["b"]
            try:
                sol = M.solve("mosek")
                W.append(sol("b").magnitude)
            except RuntimeWarning:
                W.append(np.nan)
        ax.plot(lat, W)
    
    ax.set_ylim([0, 1000])
    ax.set_xlim([20, 50])
    ax.grid()
    labels = ["$\\pm$" + item.get_text() for item in ax.get_xticklabels()]
    labels = ["$\\pm$%d" % l for l in np.linspace(20, 50, len(labels))]
    ax.set_xticklabels(labels)
    ax.set_xlabel("Latitude Requirement [deg]")
    ax.set_ylabel("Wing Span [ft]")
    ax.legend(["%d Percentile Winds" % a for a in [80, 90, 95]], loc=2, fontsize=15)
    fig.savefig("../../../gassolarpaper/spanvslatsolarsimple.pdf", bbox_inches="tight")

""" wind operating """
if WIND:
    lat = 29
    M = Mission(latitude=lat)
    for vk in M.varkeys["CDA_0"]:
        M.substitutions.update({vk: 0.002})
    M.cost = M["W"]
    sol1 = M.solve("mosek")
    from gassolar.solar.solar import Mission
    M = Mission(latitude=lat)
    M.cost = M["W_{total}"]
    sol2 = M.solve("mosek")
    fig, ax = windalt_plot(lat, sol1, sol2)
    ax.annotate("structural weight fraction", xy=(66.2, 30), xytext=(46, 10),
                arrowprops=dict(facecolor='black', shrink=0.05, width=1.5,
                                headwidth=10))
    ax.annotate("detailed structural model", xy=(58, 50), xytext=(61, 65),
                arrowprops=dict(facecolor='black', shrink=0.05, width=1.5,
                                headwidth=10))
    fig.savefig("../../../gassolarpaper/windaltoper.pdf", bbox_inches="tight")
