"""Jungle Hawk Owl"""
import numpy as np
from gpkitmodels.aircraft.GP_submodels.gas_engine import Engine
from gpkitmodels.aircraft.GP_submodels.wing import Wing
from gpkitmodels.aircraft.GP_submodels.fuselage import Fuselage
from gpkitmodels.aircraft.GP_submodels.empennage import Empennage
from gpkitmodels.aircraft.GP_submodels.tail_boom import TailBoomState
from gpkitmodels.aircraft.GP_submodels.tail_boom_flex import TailBoomFlexibility
from gpkitmodels.helpers import summing_vars
from gpkit import Model, Variable, Vectorize, units
from flight_segment import FlightSegment
from loiter import Loiter

# pylint: disable=invalid-name

class Aircraft(Model):
    "the JHO vehicle"
    def __init__(self, Wfueltot, DF70=False, **kwargs):
        self.flight_model = AircraftPerf
        self.fuselage = Fuselage(Wfueltot)
        self.wing = Wing(spar="TubeSpar")
        self.engine = Engine(DF70)
        self.empennage = Empennage()

        components = [self.fuselage, self.wing, self.engine, self.empennage]
        self.smeared_loads = [self.fuselage, self.engine]

        self.loading = AircraftLoading

        Wzfw = Variable("W_{zfw}", "lbf", "zero fuel weight")
        Wpay = Variable("W_{pay}", 10, "lbf", "payload weight")
        Wavn = Variable("W_{avn}", 8, "lbf", "avionics weight")

        constraints = [
            Wzfw >= sum(summing_vars(components, "W")) + Wpay + Wavn,
            self.empennage.horizontaltail["V_h"] <= (
                self.empennage.horizontaltail["S"]
                * self.empennage.horizontaltail["l_h"]/self.wing["S"]**2
                * self.wing["b"]),
            self.empennage.verticaltail["V_v"] <= (
                self.empennage.verticaltail["S"]
                * self.empennage.verticaltail["l_v"]/self.wing["S"]
                / self.wing["b"]),
            self.wing["C_{L_{max}}"]/self.wing["m_w"] <= (
                self.empennage.horizontaltail["C_{L_{max}}"]
                / self.empennage.horizontaltail["m_h"])
            ]

        Model.__init__(self, None, [components, constraints],
                       **kwargs)

class AircraftLoading(Model):
    "aircraft loading model"
    def __init__(self, aircraft, Wcent, **kwargs):

        loading = [aircraft.wing.loading(aircraft.wing, Wcent)]
        loading.append(aircraft.empennage.loading(aircraft.empennage))
        loading.append(aircraft.fuselage.loading(aircraft.fuselage, Wcent))

        tbstate = TailBoomState()
        loading.append(TailBoomFlexibility(aircraft.empennage.horizontaltail,
                                           aircraft.empennage.tailboom,
                                           aircraft.wing, tbstate, **kwargs))

        Model.__init__(self, None, loading, **kwargs)

class AircraftPerf(Model):
    "performance model for aircraft"
    def __init__(self, static, state, **kwargs):

        self.wing = static.wing.flight_model(static.wing, state)
        self.fuselage = static.fuselage.flight_model(static.fuselage, state)
        self.engine = static.engine.flight_model(static.engine, state)
        self.htail = static.empennage.horizontaltail.flight_model(
            static.empennage.horizontaltail, state)
        self.vtail = static.empennage.verticaltail.flight_model(
            static.empennage.verticaltail, state)
        self.tailboom = static.empennage.tailboom.flight_model(
            static.empennage.tailboom, state)

        self.dynamicmodels = [self.wing, self.fuselage, self.engine,
                              self.htail, self.vtail, self.tailboom]
        areadragmodel = [self.fuselage, self.htail, self.vtail, self.tailboom]
        areadragcomps = [static.fuselage, static.empennage.horizontaltail,
                         static.empennage.verticaltail,
                         static.empennage.tailboom]

        Wend = Variable("W_{end}", "lbf", "vector-end weight")
        Wstart = Variable("W_{start}", "lbf", "vector-begin weight")
        CD = Variable("C_D", "-", "drag coefficient")
        CDA = Variable("CDA", "-", "area drag coefficient")
        mfac = Variable("m_{fac}", 1.7, "-", "drag margin factor")

        dvars = []
        for dc, dm in zip(areadragcomps, areadragmodel):
            if "C_f" in dm.varkeys:
                dvars.append(dm["C_f"]*dc["S"]/static.wing["S"])
            if "C_d" in dm.varkeys:
                dvars.append(dm["C_d"]*dc["S"]/static.wing["S"])

        constraints = [Wend == Wend,
                       Wstart == Wstart,
                       CDA/mfac >= sum(dvars),
                       CD >= CDA + self.wing["C_d"]]

        Model.__init__(self, None, [self.dynamicmodels, constraints], **kwargs)

class Cruise(Model):
    "make a cruise flight segment"
    def __init__(self, aircraft, N, altitude=15000, latitude=45, percent=90,
                 day=355, R=200):
        fs = FlightSegment(aircraft, N, altitude, latitude, percent, day)

        R = Variable("R", R, "nautical_miles", "Range to station")
        constraints = [R/N <= fs["V"]*fs.be["t"]]

        Model.__init__(self, None, [fs, constraints])

class Climb(Model):
    "make a climb flight segment"
    def __init__(self, aircraft, N, altitude=15000, latitude=45, percent=90,
                 day=355, dh=15000):
        fs = FlightSegment(aircraft, N, altitude, latitude, percent, day)

        with Vectorize(N):
            hdot = Variable("\\dot{h}", "ft/min", "Climb rate")

        deltah = Variable("\\Delta_h", dh, "ft", "altitude difference")
        hdotmin = Variable("\\dot{h}_{min}", 100, "ft/min",
                           "minimum climb rate")

        constraints = [
            hdot*fs.be["t"] >= deltah/N,
            hdot >= hdotmin,
            fs.slf["T"] >= (0.5*fs["\\rho"]*fs["V"]**2*fs["C_D"]
                            * fs.aircraft.wing["S"] + fs["W_{start}"]*hdot
                            / fs["V"]),
            ]

        Model.__init__(self, None, [fs, constraints])

class Mission(Model):
    "creates flight profile"
    def __init__(self, DF70=False, **kwargs):

        mtow = Variable("MTOW", "lbf", "max-take off weight")
        Wcent = Variable("W_{cent}", "lbf", "center aircraft weight")
        Wfueltot = Variable("W_{fuel-tot}", "lbf", "total aircraft fuel weight")
        LS = Variable("(W/S)", "lbf/ft**2", "wing loading")

        JHO = Aircraft(Wfueltot, DF70)
        loading = JHO.loading(JHO, Wcent)

        climb1 = Climb(JHO, 10, altitude=np.linspace(0, 15000, 11)[1:])
        cruise1 = Cruise(JHO, 1, R=200)
        loiter1 = Loiter(JHO, 5)
        cruise2 = Cruise(JHO, 1)
        mission = [climb1, cruise1, loiter1, cruise2]

        constraints = [
            mtow >= climb1["W_{start}"][0],
            Wfueltot >= sum(fs["W_{fuel-fs}"] for fs in mission),
            mission[-1]["W_{end}"][-1] >= JHO["W_{zfw}"],
            Wcent >= Wfueltot + sum(summing_vars(JHO.smeared_loads, "W")),
            LS == mtow/JHO.wing["S"]
            ]

        for i, fs in enumerate(mission[1:]):
            constraints.extend([
                mission[i]["W_{end}"][-1] == fs["W_{start}"][0]
                ])

        cost = 1/loiter1["t_Mission, Loiter"]

        Model.__init__(self, cost, [JHO, mission, loading, constraints],
                       **kwargs)

if __name__ == "__main__":
    M = Mission()
    sol = M.solve("mosek")
    print sol.table()