```python
#inPDF: skip
from gassolar.solar.solar import Mission as Msolar
from gassolar.gas.gas import Mission as Mgas
from gassolar.environment.wind_speeds import get_windspeed
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({'font.size':15})
fig, ax = plt.subplots()
lat = np.arange(20, 41, 1)
Mg = Mgas()
Mg.substitutions.update({"W_{pay}": 10})
Mg.substitutions.update({"t_Mission, Loiter": 7})
Mg.cost = Mg["MTOW"]
psolar = []
pgas = []
for a in [80, 90, 95]:
    wg = []
    ws = []
    runagains = True
    highestwind = 0
    for l in lat:
        if runagains:
            Ms = Msolar(latitude=l)
            for vk in Ms.varkeys["p_{wind}"]:
                Ms.substitutions.update({vk: a/100.0})
            Ms.cost = Ms["W_{total}"]
            try:
                sol = Ms.solve("mosek")
                ws.append(sol("W_{total}").magnitude)
            except RuntimeWarning:
                ws.append(np.nan)
                runagain = False
        else:
            ws.append(np.nan)
        
        wind = get_windspeed(l, a, 15000, 355)
        cwind = get_windspeed(l, a, np.linspace(0, 15000, 11)[1:], 355)
        if wind > highestwind:
            highestwind = wind
            for vk in Mg.varkeys["V_{wind}"]:
                if "Climb" in vk.models:
                    Mg.substitutions.update({vk: cwind[vk.idx[0]]})
                else:
                    Mg.substitutions.update({vk: wind})
        try:
            sol = Mg.solve("mosek")
            wg.append(sol("MTOW").magnitude)
        except RuntimeWarning:
            wg.append(np.nan)
            print "Fail, Lat: %d" % l
    
    pgas.append(wg)
    psolar.append(ws)

indl = psolar[0].index(max(psolar[0]))
indh = psolar[2].index(max(psolar[2]))
a = (psolar[2][indh]-psolar[0][indl])/(lat[indh]-lat[indl])
b = psolar[0][indl]-a*lat[indl]
c = a*lat[indh+1:indl+1] + b
ax.fill_between(lat[0:indl+1], psolar[0][0:indl+1], np.append(np.array(psolar[-1][0:indh+1]), c), alpha=0.3, facecolor="b", edgecolor="None")
ax.plot(lat, psolar[1], "b", lw=2)
ax.plot(lat, pgas[1], "r", lw=2)
ax.plot(lat, psolar[0], "b")
ax.plot(lat, psolar[2], "b")
ax.fill_between(lat, pgas[0], pgas[2], alpha=0.3, facecolor="r", edgecolor="None")
ax.plot(lat, pgas[0], "r")
ax.plot(lat, pgas[2], "r")
ax.set_ylim([0, 400])
ax.set_xlim([20, 40])
ax.grid()
ax.set_xlabel("Latitude Requirement [deg]")
ax.set_ylabel("Max Take Off Weight [lbf]")
labels = ["$\\pm$" + item.get_text() for item in ax.get_xticklabels()]
labels = ["$\\pm$%d" % l for l in np.linspace(20, 40, len(labels))]
ax.set_xticklabels(labels)
ax.legend(["Gas Powered (7-day endurance)", "Solar-electric Powered"], fontsize=15, loc=2)
fig.savefig("../gassolarpaper/mtowvslat.pdf", bbox_inches="tight")
```
