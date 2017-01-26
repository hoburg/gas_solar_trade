# Gas Simple Write Up

# Simple model of a Gas Powered Aircraft
```python
#inPDF: skip
from gas import Mission
from gassolar.environment.wind_speeds import get_windspeed
import matplotlib.pyplot as plt
from gpkit.tools.autosweep import sweep_1d
import numpy as np
plt.rcParams.update({'font.size':19})

END = False 
LAT = False 
DRAG = False
BSFC = False
LD = True

""" MTOW vs Endurance """

if END:
    plt.rcParams.update({'font.size':15})
    M = Mission()
    # M.cost = M["b_Mission, Aircraft, Wing"]
    M.cost = M["MTOW"]
    fig, ax = plt.subplots()
    lower = 1
    upper = 12 
    xmin_ = np.linspace(lower, upper, 100)
    tol = 0.05
    for p in [85, 90, 95]:
        notpassing = True
        while notpassing:
            wind = get_windspeed(38, p, 15000, 355)
            cwind = get_windspeed(38, p, np.linspace(0, 15000, 11)[1:], 355)
            for vk in M.varkeys["V_{wind}"]:
                if "Climb" in vk.models:
                    M.substitutions.update({vk: cwind[vk.idx[0]]})
                else:
                    M.substitutions.update({vk: wind})
            try:
                bst = sweep_1d(M, tol, M["t_Mission, Loiter"], [lower, upper], solver="mosek")
                notpassing = False
            except RuntimeWarning:
                notpassing = True
                upper -= 0.1
                xmin_ = np.linspace(lower, upper, 100)
    
        ax.plot(xmin_, bst["cost"].__call__(xmin_), lw=2)
    ax.grid()
    ax.set_ylim([0, 1000])
    ax.set_xlabel("Endurance [days]")
    ax.set_ylabel("Max Take Off Weight [lbf]")
    ax.legend(["%d Percentile Winds" % a for a in [85, 90, 95]], loc=2, fontsize=15)
    fig.savefig("../../gassolarpaper/mtowvsendurance.pdf", bbox_inches="tight")

""" latitutde mtow """
if LAT:
    plt.rcParams.update({'font.size':15})
    fig, ax = plt.subplots()
    lat = np.arange(0, 60, 1)
    M = Mission()
    M.substitutions.update({"W_{pay}": 10})
    M.substitutions.update({"t_Mission, Loiter": 7})
    # M.cost = M["b_Mission, Aircraft, Wing"]
    M.cost = M["MTOW"]
    for a in [80, 90, 95]:
        mtow = []
        wind = []
        for l in lat:
            wind.append(get_windspeed(l, a, 15000, 355))
            maxwind = max(wind)
            for v in M.varkeys["V_{wind}"]:
                M.substitutions.update({v: maxwind})
            try:
                sol = M.solve("mosek")
                # mtow.append(sol("b_Mission, Aircraft, Wing").magnitude)
                mtow.append(sol("MTOW").magnitude)
            except RuntimeWarning:
                mtow.append(np.nan)
        ax.plot(lat, mtow, lw=2)
    
    ax.set_ylim([0, 800])
    ax.set_xlim([20, 45])
    ax.grid()
    ax.set_xlabel("Latitude [deg]")
    ax.set_ylabel("Max Take Off Weight [lbf]")
    labels = ["$\\pm$" + item.get_text() for item in ax.get_xticklabels()]
    labels = ["$\\pm$%d" % l for l in np.linspace(20, 45, len(labels))]
    ax.set_xticklabels(labels)
    ax.legend(["%d Percentile Winds" % a for a in [80, 90, 95]], loc=2, fontsize=15)
    fig.savefig("../../gassolarpaper/mtowvslatgas.pdf", bbox_inches="tight")

if DRAG:
    M = Mission()
    M.cost = M["MTOW"]
    for e in M.varkeys["\\eta_{prop}"]:
        M.substitutions.update({e: 0.75})
    fig, ax = plt.subplots(3)
    wind = get_windspeed(38, 90, 15000, 355)
    cwind = get_windspeed(38, 90, np.linspace(0, 15000, 11)[1:], 355)
    for vk in M.varkeys["V_{wind}"]:
        if "Climb" in vk.models:
            M.substitutions.update({vk: cwind[vk.idx[0]]})
        else:
            M.substitutions.update({vk: wind})
    M.substitutions.update({"t_Mission, Loiter": ("sweep", np.linspace(1, 10, 10))})
    sol = M.solve("mosek", skipsweepfailures=True)
    
    ax[0].plot(sol("t_Mission, Loiter"), [np.average(sv) for sv in sol("CDA_Mission, Loiter, FlightSegment, AircraftPerf")])
    ax[0].plot([1,10], [0.01, 0.01])
    ax[0].legend(["Component Drag Build Up", "Simple Model Approximation"], loc=3)
    ax[0].set_ylabel("Non-wing Drag Coefficient $C_{d_0}$")
    ax[0].set_xlabel("Endurance [days]")
    ax[0].grid()
    ax[1].plot(sol("t_Mission, Loiter"), [sum([sol(sv)[i] for sv in sol("W") if len(M[sv].descr["models"])==3]).magnitude/sol("MTOW")[i].magnitude for i in range(10)])
    ax[2].plot(sol("t_Mission, Loiter"), [np.average(sol("BSFC_Mission, Loiter, FlightSegment, AircraftPerf, EnginePerf")[i]) for i in range(10)])
    fig.savefig("analysis.pdf", bbox_inches="tight")

if BSFC:
    M = Mission()
    M.cost = M["MTOW"]
    for e in M.varkeys["\\eta_{prop}"]:
        M.substitutions.update({e: 0.75})
    fig, ax = plt.subplots()
    wind = get_windspeed(38, 90, 15000, 355)
    cwind = get_windspeed(38, 90, np.linspace(0, 15000, 11)[1:], 355)
    for vk in M.varkeys["V_{wind}"]:
        if "Climb" in vk.models:
            M.substitutions.update({vk: cwind[vk.idx[0]]})
        else:
            M.substitutions.update({vk: wind})
    M.substitutions.update({"t_Mission, Loiter": 7})
    sol = M.solve("mosek")
    pr = np.linspace(0, 1, 100)
    bsfcp = (0.00866321 * pr**-7.70161 + 1.38628 
             * pr**1.12922)**(1/18.5563)*0.316
    ax.plot(pr, bsfcp, linewidth=2)
    pm = sol("P_{total}_Mission, Loiter, FlightSegment, AircraftPerf, EnginePerf")/sol("P_{shaft-max}_Mission, Loiter, FlightSegment, AircraftPerf, EnginePerf")
    bsfcm = sol("BSFC_Mission, Loiter, FlightSegment, AircraftPerf, EnginePerf")
    ax.plot(pm, bsfcm, "o", mfc="None", ms=7, mew=1.5)
    ax.legend(["BSFC to Power Curve", "BSFC Mission Values"], fontsize=15)
    ax.set_xlabel("Percent Power")
    ax.set_ylabel("BSFC [kg/kW/hr]")
    ax.set_ylim([0, 1])
    ax.grid()
    fig.savefig("../../gassolarpaper/bsfcmission.pdf", bbox_inches="tight")

def return_cd(cl, re): 
    cd = (0.0247*cl**2.49*re**-1.11 + 2.03e-7*cl**12.7*re**-0.338 +
          6.35e10*cl**-0.243*re**-3.43 + 6.49e-6*cl**-1.9*re**-0.681)**(1/3.72)
    return cd

from gassolar.solar.plotting import labelLines
if LD:
    M = Mission()
    M.cost = 1/M["t_Mission, Loiter"]
    for e in M.varkeys["\\eta_{prop}"]:
        M.substitutions.update({e: 0.75})
    fig, ax = plt.subplots()
    wind = get_windspeed(38, 90, 15000, 355)
    cwind = get_windspeed(38, 90, np.linspace(0, 15000, 11)[1:], 355)
    for vk in M.varkeys["V_{wind}"]:
        if "Climb" in vk.models:
            M.substitutions.update({vk: cwind[vk.idx[0]]})
        else:
            M.substitutions.update({vk: wind})
    M.substitutions.update({"MTOW": 200})
    sol = M.solve("mosek")
    re = sol("Re_Mission, Loiter, FlightSegment, AircraftPerf, WingAero")[-1]
    clm = sol("C_L_Mission, Loiter, FlightSegment, AircraftPerf, WingAero")
    cdm = sol("c_{dp}_Mission, Loiter, FlightSegment, AircraftPerf, WingAero")
    cl = np.linspace(0.2, 1.5, 100)
    cd = return_cd(cl, re)
    cl15 = cl**1.5/cd
    clmax = cl[cl15 == max(cl15)]
    cdmax = cd[cl15 == max(cl15)]
    l = ax.plot(clmax, cdmax, "^", mfc="None", ms=7, mew=1.5, 
                label="$C_L^{1.5}/c_{d_p}$")
    lines1 = [l[0]]
    l = ax.plot(clm, cdm, "o", mfc="None", ms=7, mew=1.5, 
                label="With Wind Constraint")
    lines1.append(l[0])
    
    for vk in M.varkeys["m_{fac}"]:
        if "Loiter" in vk.descr["models"] and "FlightState" in vk.descr["models"]:
            M.substitutions.update({vk:0.01})
    sol = M.solve("mosek")
    clw = sol("C_L_Mission, Loiter, FlightSegment, AircraftPerf, WingAero")
    cdw = sol("c_{dp}_Mission, Loiter, FlightSegment, AircraftPerf, WingAero")
    l = ax.plot(clw, cdw, "s", mfc="None", ms=7, mew=1.5, 
                label="Without Wind Constraint")
    lines1.append(l[0])
    l = ax.plot(cl, cd, linewidth=2, label="Re=%3.fk" % (re/1000.), c="b", zorder=1)
    lines = [l[0]]
    re = sol("Re_Mission, Loiter, FlightSegment, AircraftPerf, WingAero")
    for i, r, col in zip(range(5), re, ["", "m", "m", "c", "c"]):
        cd = return_cd(cl, r)
        cl15 = cl**1.5/cd
        clmax = cl[cl15 == max(cl15)]
        cdmax = cd[cl15 == max(cl15)]
        if i == 2 or i == 4:
            l = ax.plot(cl, cd, linewidth=2, label="Re=%3.fk" % (r/1000.), c=col, zorder=1)
            lines.append(l[0])
        ax.plot(clmax, cdmax, "^", mfc="None", ms=7, mew=1.5)
        
    labelLines(lines, fontsize=12, zorder=2.5, align=False, 
               xvals=[0.95, 0.75, 0.6])
    ax.set_xlabel("$C_L$")
    ax.set_ylabel("$c_{d_p}$")
    ax.legend(["max($C_L^{1.5}/C_D$)", "With Wind Constraint", "Without Wind Constraint"], fontsize=15, loc=2)
    ax.grid()
    fig.savefig("../../gassolarpaper/polarmission.pdf", bbox_inches="tight")

```
