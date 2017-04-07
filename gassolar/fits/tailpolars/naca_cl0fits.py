"naca_polarfits.py"
import numpy as np
import sys
import pandas as pd
import matplotlib.pyplot as plt
import gpkitmodels.GP.aircraft.tail.tail_aero as TailAero
from gpfit.fit import fit
import os
plt.rcParams.update({'font.size':15})

GENERATE = True
REFAC = 1e6
NACAFAC = 100

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
    df = df.astype(float)
    return df

def fit_setup(naca_range, re_range):
    "set up x and y parameters for gp fitting"
    tau = [[float(n)]*len(re_range) for n in naca_range]
    re = [re_range]*len(naca_range)
    cd = []
    for n in naca_range:
        for r in re_range:
            dataf = text_to_df("naca%s.cl0.Re%dk.pol" % (n, r))
            cd.append(dataf["CD"])

    u1 = np.hstack(re)
    u2 = np.hstack(tau)
    w = np.hstack(cd)
    u1 = u1.astype(np.float)*1000
    u2 = u2.astype(np.float)/100
    w = w.astype(np.float)
    u = [u1, u2]
    x = np.log(u)
    y = np.log(w)
    return x, y

def plot_fits(naca_range, cnstr, x, y):
    "plot fit compared to data"

    fig, ax = plt.subplots()
    colors = ["#084081", "#0868ac", "#2b8cbe", "#4eb3d3", "#7bccc4"]
    assert len(colors) == len(naca_range)
    lna, ind = np.unique(x[1], return_index=True)
    xna = np.exp(lna)*100
    xre = np.array([np.exp(x[0][ind[i-1]:ind[i]]) for i in range(1, len(ind))])*1e3
    cds = [np.exp(y[ind[i-1]:ind[i]]) for i in range(1, len(ind))]
    yfit = cnstr.evaluate(x)
    cdf = [np.exp(yfit[ind[i-1]:ind[i]]) for i in range(1, len(ind))]
    fig, ax = plt.subplots()
    i = 0
    nacaint = np.array([int(n) for n in naca_range])
    for na, re, cd, fi in zip(xna, xre, cds, cdf):
        na = int(round(na))
        if na in nacaint:
            ax.plot(re, cd, "o", mec=colors[i], mfc="none", mew=1.5)
            ax.plot(re, fi, c=colors[i],
                    label="NACA" + naca_range[nacaint == na][0], lw=2)
            i += 1
    ax.legend(fontsize=15)
    ax.set_xlabel("$Re$")
    ax.set_ylabel("$c_{d_p}$")
    ax.grid()
    return fig, ax

if __name__ == "__main__":
    Re = range(200, 950, 50)
    NACA = np.array(["0005", "0008", "0009", "0010", "0015", "0020"])
    X, Y = fit_setup(NACA, Re) # call fit(X, Y, 4, "SMA") to get fit
    np.random.seed(0)
    cn, err = fit(X, Y, 4, "MA")
    print "RMS error: %.5f    Max Err: %.5f" % (err[0], err[1])
    df = cn.get_dataframe(X)
    if GENERATE:
        path = os.path.dirname(TailAero.__file__)
        df.to_csv(path + os.sep + "tail_dragfit.csv")
    else:
        df.to_csv("tail_dragfit.csv")

    F, A = plot_fits(NACA[1:], cn, X, Y)
    if len(sys.argv) > 1:
        path = sys.argv[1]
        F.savefig(path + "taildragpolar.pdf", bbox_inches="tight")
    else:
        F.savefig("taildragpolar.pdf", bbox_inches="tight")

