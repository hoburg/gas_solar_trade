"print sensitivities"

def sens_table(sols, varnames):
    with open("../../gassolarpaper/gassens.generated.tex", "w") as f:
        f.write("\\begin{longtable}{lccccccccccccc}\n")
        f.write("\\caption{Gas Sensitivities}\\\\\n")
        f.write("\\toprule\n")
        f.write("\\toprule\n")
        f.write("\\label{t:sens}\n")
        f.write("Variable & 5 Day Endurance & 7 Day Endurance & 9 Day Endurance\\\\\n")
        f.write("\\midrule\n")
        for vname in varnames:
            sens = []
            for s in sols:
                sen = s["sensitivities"]["constants"][vname]
                if hasattr(sen, "__len__"):
                    sen = s["sensitivities"]["constants"][max(sen)]
                sens.append(sen)
            vals = "$" + vname + "$ &" + " & ".join(["%.3g" % x for x in sens])
            f.write(vals + "\\\\\n")
        f.write("\\bottomrule\n")
        f.write("\\end{longtable}")
