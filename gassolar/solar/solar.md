# Solar Simple Write Up

# Simple model of a Gas Powered Aircraft
```python
#inPDF: skip
from solar import Mission
import matplotlib.pyplot as plt
import numpy as np
from plotting import windalt_plot, labelLines

LATITUDE = False
WIND = False
CON = True
COMP = False
SENS = False

""" contour """

if CON:
    plt.rcParams.update({'font.size':19})
    etasolar = np.linspace(0.15, 0.5, 10)
    hbatts = np.linspace(250, 400, 10)
    x = np.array([etasolar]*10)
    y = np.array([hbatts]*10).T
    z = np.zeros([10, 10])
    for av in [80, 85, 90]:
        for l in [25, 30, 35]:
            fig, ax = plt.subplots()
            M = Mission(latitude=l)
            M.substitutions.update({"W_{pay}": 10})
            for vk in M.varkeys["\\eta_{prop}"]:
                M.substitutions.update({vk: 0.75})
            for vk in M.varkeys["p_{wind}"]:
                M.substitutions.update({vk: av/100.0})
            M.cost = M["b_Mission, Aircraft, Wing"]
            for i, etas in enumerate(etasolar):
                M.substitutions.update({"\\eta_Mission, Aircraft, SolarCells": etas})
                for j, hbs in enumerate(hbatts):
                    M.substitutions.update({"h_{batt}": hbs})
                    try:
                        sol = M.solve("mosek")
                        z[i, j] = sol("b_Mission, Aircraft, Wing").magnitude
                        print sol("b_Mission, Aircraft, Wing").magnitude
                        print sol("h_{batt}")
                        print "Pass: Latitude = %d, Percentile Winds = %d" % (l, av)
                    except RuntimeWarning:
                        z[i, j] = np.nan
                        print "Fail: Latitude = %d, Percentile Winds = %d" % (l, av)
            print z
            levels = np.array(range(30, 2000, 10)+ [2300])
            if av == 90:
                v = np.array(range(30, 700, 10)+ [2300])
            else:
                v = np.array(range(30, 400, 10)+ [2300])
            a = ax.contour(x, y, z, levels, colors="k")
            ax.clabel(a, v, inline=1, fmt="%d [ft]")
            ax.set_xlabel("Solar Cell Efficiency")
            ax.set_ylabel("Battery Energy Density [Whr/kg]")
            fig.savefig("../../gassolarpaper/bcontourl%da%d.pdf" % (l, av), 
                        bbox_inches="tight")

""" objective comparison """
if COMP:
    plt.rcParams.update({'font.size':15})
    fig, ax = plt.subplots()
    fig2, ax2 = plt.subplots()
    lat = np.arange(20, 40, 1)
    l1 = []
    l2 = []
    for obj in ["b_Mission, Aircraft, Wing", "S_Mission, Aircraft, SolarCells"]:
        W = []
        SS = []
        runagain = True
        for l in lat:
            if runagain:
                M = Mission(latitude=l)
                M.substitutions.update({"W_{pay}": 10})
                for vk in M.varkeys["p_{wind}"]:
                    M.substitutions.update({vk: 90/100.0})
                M.substitutions.update({"\\rho_{solar}": 0.25})
                M.cost = M[obj]
                try:
                    sol = M.solve("mosek")
                    W.append(sol("b_Mission, Aircraft, Wing").magnitude)
                    SS.append(sol("S_Mission, Aircraft, SolarCells").magnitude)
                except RuntimeWarning:
                    W.append(np.nan)
                    SS.append(np.nan)
                    runagain = False
            else:
                W.append(np.nan)
                SS.append(np.nan)
        if obj[0] == "b":
            ty = "b"
        else:
            ty = "r--"
        ll = ax.plot(lat, W, "%s" % ty, lw=2)
        ll1 = ax2.plot(lat, SS, '%s' % ty, lw=2)
    
    ax.set_ylim([0, 150])
    ax.set_xlim([20, 35])
    ax2.set_ylim([0, 300])
    ax2.set_xlim([20, 35])
    ax.grid()
    ax2.grid()
    ax.set_xlabel("Latitude Requirement [deg]")
    ax2.set_xlabel("Latitude Requirement [deg]")
    ax.set_ylabel("Wing Span $b$ [ft]")
    ax2.set_ylabel("Solar Cell Area $S_{\\mathrm{solar}}$ [ft$^2$]")
    labels = ["$\\pm$" + item.get_text() for item in ax.get_xticklabels()]
    labels = ["$\\pm$%d" % l for l in np.linspace(20, 35, len(labels))]
    ax.set_xticklabels(labels)
    ax2.set_xticklabels(labels)
    ax.legend(["Objective: min($b$)", "Objective: min($S_{\mathrm{solar}}$)"], loc=2, fontsize=15)
    ax2.legend(["Objective: min($b$)", "Objective: min($S_{\mathrm{solar}}$)"], loc=2, fontsize=15)
    fig.savefig("../../gassolarpaper/solarobjcomp.pdf", bbox_inches="tight")
    fig2.savefig("../../gassolarpaper/solarobjcomp2.pdf", bbox_inches="tight")

""" latitutde """
if LATITUDE:
    plt.rcParams.update({'font.size':15})
    fig, ax = plt.subplots()
    lat = np.arange(21, 40, 1)
    for a in [80, 90, 95]:
        W = []
        runagain = True
        for l in lat:
            if runagain:
                M = Mission(latitude=l)
                for vk in M.varkeys["p_{wind}"]:
                    M.substitutions.update({vk: a/100.0})
                # M.cost = M["b_Mission, Aircraft, Wing"]
                M.cost = M["W_{total}"]
                try:
                    sol = M.solve("mosek")
                    # W.append(sol("b_Mission, Aircraft, Wing").magnitude)
                    W.append(sol("W_{total}").magnitude)
                except RuntimeWarning:
                    W.append(np.nan)
                    runagain = False
            else:
                W.append(np.nan)
        ax.plot(lat, W, lw=2)
    
    ax.set_ylim([0, 500])
    ax.set_xlim([20, 45])
    ax.grid()
    ax.set_xlabel("Latitude Requirement [deg]")
    ax.set_ylabel("Max Take Off Weight [lbf]")
    labels = ["$\\pm$" + item.get_text() for item in ax.get_xticklabels()]
    labels = ["$\\pm$%d" % l for l in np.linspace(20, 45, len(labels))]
    ax.set_xticklabels(labels)
    ax.legend(["%d Percentile Winds" % a for a in [80, 90, 95]], loc=2, fontsize=15)
    fig.savefig("../../gassolarpaper/mtowvslatsolar.pdf", bbox_inches="tight")

""" wind operating """
if WIND:
    M = Mission(latitude=30)
    M.cost = M["W_{total}"]
    sol = M.solve("mosek")
    fig, ax = windalt_plot(31, sol)
    fig.savefig("../../gassolarpaper/windaltoper.pdf", bbox_inches="tight")

from print_sens import sens_table
if SENS:
    sols = []
    for l in [25, 30]:
        for p in [85, 90]:
            M = Mission(latitude=l)
            M.cost = M["W_{total}"]
            for vk in M.varkeys["p_{wind}"]:
                M.substitutions.update({vk: p/100.0})
            sol = M.solve("mosek")
            sols.append(sol)
            
    sens_table(sols, ["p_{wind}", "\\eta_Mission, Aircraft, SolarCells", "\\eta_{charge}", "\\eta_{discharge}", "\\rho_{solar}", "t_{night}", "(E/S)_{irr}", "m_{fac}_Mission, Aircraft, Wing", "h_{batt}", "W_{pay}", "\\eta_{prop}"])
```

