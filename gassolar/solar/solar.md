# Solar Simple Write Up

# Simple model of a Gas Powered Aircraft
```python
#inPDF: skip
from solar import Mission
import matplotlib.pyplot as plt
import numpy as np
from plotting import windalt_plot, labelLines
from gpkit.tools.autosweep import sweep_1d

LATITUDE = False
WIND = False
CON = True
COMP = False
SENS = False

""" contour """

if CON:
    N = 30 
    plt.rcParams.update({'font.size':19})
    etasolar = np.linspace(0.15, 0.5, N)
    hbatts = np.linspace(250, 400, N)
    x = np.array([etasolar]*N)
    y = np.array([hbatts]*N).T
    z = np.zeros([N, N])
    for av in [80, 85, 90]:
    # for av in [80]:
        for l in [25, 30, 35]:
        # for l in [25]:
            fig, ax = plt.subplots()
            M = Mission(latitude=l)
            M.substitutions.update({"W_{pay}": 10})
            for vk in M.varkeys["\\eta_{prop}"]:
                M.substitutions.update({vk: 0.75})
            for vk in M.varkeys["p_{wind}"]:
                M.substitutions.update({vk: av/100.0})
            h = []
            for i, etas in enumerate(etasolar):
                M.cost = M["b_Mission, Aircraft, Wing"]
                M.substitutions.update({"\\eta_Mission, Aircraft, SolarCells": etas})
                runagain = True
                for j in range(N):
                    if runagain:
                        M.substitutions.update({"h_{batt}": hbatts[N-j-1]})
                        try:
                            sol = M.solve("mosek")
                            z[i, N-j-1] = sol("b_Mission, Aircraft, Wing").magnitude
                        except RuntimeWarning:
                            z[i, N-j-1] = np.nan
                            runagain = False
                    else:
                        z[i, N-j-1] = np.nan

            # parato fontier
            del M.substitutions["h_{batt}"]
            M.cost = M["h_{batt}"]
            lower = etasolar[0]
            upper = etasolar[-1]
            xmin_ = np.linspace(lower, upper, 100)
            tol = 0.01
            notpassing = True
            while notpassing:
                try:
                    bst = sweep_1d(M, tol, M["\\eta_Mission, Aircraft, SolarCells"], [lower, upper], solver="mosek")
                    notpassing = False
                except RuntimeWarning:
                    notpassing = True
                    upper -= 0.05
                    xmin_ = np.linspace(lower, upper, 100)
                    h.append(sol("h_{batt}").magnitude)

            levels = np.array(range(30, 75, 5))
            v = np.array(range(30, 75, 10))
            cols = tuple(["k", "0.5"]*5 + ["k"])
            ls = tuple(["solid", "dashed"]*5 + ["solid"])
            a = ax.contour(x, y, z.T, levels, colors=cols, linestyles=ls)
            ax.clabel(a, v, inline=1, fmt="%d [ft]", fontsize=19)
            ax.set_xlabel("Solar Cell Efficiency")
            ax.set_ylabel("Battery Energy Density [Whr/kg]")
            ax.fill_between(xmin_, 0, bst["cost"].__call__(xmin_), edgecolor="r", lw=2, hatch="/", 
                            facecolor="None")
            ax.text(0.17, 260, "Infeasible", fontsize=19)
            ax.set_xlim([etasolar[0], etasolar[-1]])
            ax.set_ylim([hbatts[0], hbatts[-1]])
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

