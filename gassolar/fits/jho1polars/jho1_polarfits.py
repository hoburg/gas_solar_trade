"jho1_polarfits.py"
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from gpfit.fit import fit
import sys
from gpkitmodels.GP.aircraft.wing.wing import Wing
import inspect
import os

GENERATE = False
plt.rcParams.update({'font.size':15})

def text_to_df(filename):
    "parse XFOIL polars and concatente data in DataFrame"
    lines = list(open(filename))
    for i, l in enumerate(lines):
        lines[i] = l.split("\n")[0]
        for j in 10-np.arange(9):
            if " "*j in lines[i]:
                lines[i] = lines[i].replace(" "*j, " ")
            if "---" in lines[i]:
                start = i
    data = {}
    titles = lines[start-1].split(" ")[1:]
    for t in titles:
        data[t] = []

    for l in lines[start+1:]:
        for i, v in enumerate(l.split(" ")[1:]):
            data[titles[i]].append(v)

    df = pd.DataFrame(data)
    return df

def fit_setup(Re_range):
    "set up x and y parameters for gp fitting"
    CL = []
    CD = []
    RE = []
    fig, ax = plt.subplots()
    for r in Re_range:
        dataf = text_to_df("jho1.ncrit09.Re%dk.pol" % r)
        if r < 150:
            cl = dataf["CL"].values.astype(np.float)
            cd = dataf["CD"].values.astype(np.float)
            CL.append(np.hstack([cl[cl >= 1.0]]*1))
            CD.append(np.hstack([cd[cl >= 1.0]]*1))
        elif r < 200:
            cl = dataf["CL"].values.astype(np.float)
            cd = dataf["CD"].values.astype(np.float)
            CL.append(cl[cl >= 0.9])
            CD.append(cd[cl >= 0.9])
        else:
            CL.append(dataf["CL"].values.astype(np.float))
            CD.append(dataf["CD"].values.astype(np.float))
        ax.plot(dataf["CL"].values.astype(np.float), dataf["CD"].values.astype(np.float))
        ax.legend(["%d" % re for re in Re_range])
        RE.append([r*1000.0]*len(CL[-1]))

    fig.savefig("polarstest.pdf")

    u1 = np.hstack(CL)
    u2 = np.hstack(RE)
    w = np.hstack(CD)
    u = [u1, u2]
    xx = np.log(u2)
    x = np.log(u)
    y = np.log(w)
    return x, y

def return_fit(cl, re):
    "polar fit for the JHO1 airfoil"
    cd = (0.0247*cl**2.49*re**-1.11 + 2.03e-7*cl**12.7*re**-0.338 +
          6.35e10*cl**-0.243*re**-3.43 + 6.49e-6*cl**-1.9*re**-0.681)**(1/3.72)
    # SMA function, K=3, max RMS error = 0.00489
    return cd

def plot_fits(re, cnstr, x, y):
    "plot fit compared to data"
    # colors = ["k", "m", "b", "g", "y"]
    colors = ["#084081", "#0868ac", "#2b8cbe", "#4eb3d3", "#7bccc4"]
    assert len(re) == len(colors)
    lre, ind = np.unique(X[1], return_index=True)
    xre = np.exp(lre)
    xcl = [np.exp(X[0][ind[i-1]:ind[i]]) for i in range(1, len(ind))]
    cds = [np.exp(Y[ind[i-1]:ind[i]]) for i in range(1, len(ind))]
    yfit = cnstr.evaluate(x)
    cdf = [np.exp(yfit[ind[i-1]:ind[i]]) for i in range(1, len(ind))]
    fig, ax = plt.subplots()
    i = 0
    for r, cl, cd, fi in zip(xre, xcl, cds, cdf):
        roundre = int(np.round(r)/1000)
        if roundre in re:
            ax.plot(cl, cd, "o", mec=colors[i], mfc="none", mew=1.5)
            ax.plot(cl, fi, c=colors[i], label="Re = %dk" % roundre, lw=2)
            i += 1
    ax.set_xlabel("$C_L$")
    ax.set_ylabel("$c_{d_p}$")
    ax.legend(loc=2)
    ax.grid()
    return fig, ax

if __name__ == "__main__":
    Re = np.arange(150, 750, 50)
    X, Y = fit_setup(Re) # call fit(X, Y, 4, "SMA") to get fit
    np.random.seed(0)
    cn, err = fit(X, Y, 4, "SMA")
    print "RMS error: %.5f" % err
    df = cn.get_dataframe(X)
    if GENERATE:
        path = os.path.dirname(inspect.getfile(Wing))
        df.to_csv(path + os.sep + "jho_fitdata.csv")
    else:
        df.to_csv("jho_fitdata.csv")

    # replot = np.array([150, 200, 300, 350, 400])
    replot = np.array([300, 350, 400, 450, 500])
    F, A = plot_fits(replot, cn, X, Y)
    if len(sys.argv) > 1:
        path = sys.argv[1]
        F.savefig(path + "jho1polarfit1.eps", bbox_inches="tight")
    else:
        F.savefig("jho1polarfit1.eps", bbox_inches="tight")
