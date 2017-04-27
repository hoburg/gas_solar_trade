"print sensitivities"
from gassolar.solar.solar import Mission
import matplotlib.pyplot as plt
import numpy as np
import sys

def sens_table(sols, models, varnames, filename, solar, latns=[],
               title="Sensitivities", label="sens"):
    sens = {}
    latexns = {}
    for vname, latn in zip(varnames, latns):
        sen = sols[0]["sensitivities"]["constants"][vname]
        if hasattr(sen, "__len__"):
            val = max(np.abs(sen.values()))
            sen = sum(sen.values())
        sens[vname] = sen
        latexns[vname] = latn

    vnmsorted = []
    latnsorted = []
    for s in sorted(np.absolute(sens.values()), reverse=True):
        vn = [se for se in sens if abs(sens[se]) == s][0]
        vnmsorted.append(vn)
        latnsorted.append(latexns[vn])

    with open(filename, "w") as f:
        f.write("\\begin{longtable}{lccccccccccccc}\n")
        f.write("\\caption{%s}\\\\\n" % title)
        f.write("\\toprule\n")
        f.write("\\toprule\n")
        f.write("\\label{t:%s}\n" % label)
        if solar:
            f.write("\\multirow{2}{*}{Variable} & 25th Latitude & 30th Latitude & 25th Latitude & 30th Latitude \\\\\n")
            f.write("& 85th Percentile Winds & 85th Percentile Winds & 90th Percentile Winds & 90th Percentile Winds \\\\\n")
        else:
            f.write("Variable & 5 Day Endurance & 7 Day Endurance & 9 Day Endurance\\\\\n")
        f.write("\\midrule\n")

        for vnm, ltnm in zip(vnmsorted, latnsorted):
            sens = []
            for s in sols:
                sen = s["sensitivities"]["constants"][vnm]
                if hasattr(sen, "__len__"):
                    val = max(np.abs(sen.values()))
                    vk = [svk for svk in sen if abs(sen[svk])==val][0]
                    sen = sum(sen.values())
                sens.append(sen)
            vals = ltnm + "&" + " & ".join(["%.3g" % x for x in sens])
            f.write(vals + "\\\\\n")
        f.write("\\bottomrule\n")
        f.write("\\end{longtable}")

def plot_sens(model, sol, varnames):
    fig, ax = plt.subplots()
    pss = []
    ngs = []
    sens = {}
    for vname in varnames:
        sen = sol["sensitivities"]["constants"][vname]
        if hasattr(sen, "__len__"):
            val = max(np.abs(sen.values()))
            vk = [svk for svk in sen if abs(sen[svk])==val][0]
            # sen = sol["sensitivities"]["constants"][vk]
            sen = sum(sen.values())
        else:
            vk = model[vname]
        sens[vk] = sen

    labels = []
    for s in sorted(np.absolute(sens.values()), reverse=True):
        vn = [se for se in sens if abs(sens[se]) == s][0]
        labels.append(model[vn].descr["label"])
        if sens[vn] > 0:
            pss.append(sens[vn])
            ngs.append(0)
        else:
            ngs.append(abs(sens[vn]))
            pss.append(0)

    ind = np.arange(0.5, len(varnames) + 0.5, 1)
    ax.bar(ind - 0.25, pss, 0.5, color="#4D606E")
    ax.bar(ind - 0.25, ngs, 0.5, color="#3FBAC2")
    ax.set_xlim([0.0, ind[-1]+0.5])
    ax.set_xticks(ind)
    ax.set_xticklabels(labels, rotation=-45, ha="left")
    ax.legend(["Positive", "Negative"])
    ax.set_ylabel("sensitivities")
    return fig, ax


if __name__ == "__main__":
    sols = []
    Ms = []
    for l in [25, 29]:
        for p in [85, 90]:
            M = Mission(latitude=l)
            M.cost = M["W_{total}"]
            Ms.append(M)
            for vk in M.varkeys["p_{wind}"]:
                M.substitutions.update({vk: p/100.0})
            sol = M.solve("mosek")
            sols.append(sol)

    varns =  ["p_{wind}", "\\eta_Mission, Aircraft, SolarCells",
              "\\eta_{charge}", "\\eta_{discharge}", "\\rho_{solar}",
              "t_{night}", "(E/S)_{irr}", "h_{batt}", "W_{pay}",
              "\\eta_{prop}"]
    latns =  ["$p_{\\mathrm{wind}}$", "$\\eta_{\\mathrm{solar}}$",
              "$\\eta_{\\mathrm{charge}}$", "$\\eta_{\\mathrm{discharge}}$",
              "$\\rho_{\\mathrm{solar}}$",
              "$t_{\\mathrm{night}}$", "$(E/S)_{\\mathrm{irr}}$",
              "$h_{\\mathrm{batt}}$", "$W_{\\mathrm{pay}}$",
              "$\\eta_{\\mathrm{prop}}$"]

    fig, ax = plot_sens(M, sols[3], varns)

    varnsw = ["e", "t_{min}_Mission, Aircraft, Wing, WingSkin", "\\rho_{CFRP}", "\\eta_{discharge}", "\\eta_{charge}", "h_{batt}", "\\eta_Mission, Aircraft, SolarCells", "\\rho_{solar}", "\\eta_{prop}", "\\sigma_{CFRP}"]
    figw, axw = plot_sens(Ms[2], sols[2], varnsw)

    if len(sys.argv) > 1:
        path = sys.argv[1]
        sens_table(sols, Ms, varns, solar=True, filename=path.replace("figs/", "") + "sens.generated.tex", latns=latns, title="Solar-Electric Powered Aircraft Sensitivities")
        fig.savefig(path + "solarsensbar.pdf", bbox_inches="tight")
        figw.savefig(path + "solarsensbarw.pdf", bbox_inches="tight")
    else:
        sens_table(sols, Ms, varns, solar=True, filename="sens.generated.tex", latns=latns)
        fig.savefig("solarsensbar.pdf", bbox_inches="tight")
        figw.savefig("solarsensbarw.pdf", bbox_inches="tight")

