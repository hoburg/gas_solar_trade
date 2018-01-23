"""Jungle Hawk Owl"""
import numpy as np
from gpkitmodels.GP.aircraft.engine.gas_engine import Engine
from gpkitmodels.GP.aircraft.wing.wing import Wing as WingGP
from gpkitmodels.SP.aircraft.wing.wing import Wing as WingSP
from gpkitmodels.GP.aircraft.fuselage.elliptical_fuselage import Fuselage
from gpkitmodels.GP.aircraft.tail.empennage import Empennage
from gpkitmodels.GP.aircraft.tail.tail_boom import TailBoomState
from gpkitmodels.SP.aircraft.tail.tail_boom_flex import TailBoomFlexibility
from gpkitmodels.tools.summing_constraintset import summing_vars
from gpkit import Model, Variable, Vectorize, units
from flight_segment import FlightSegment
from loiter import Loiter

# pylint: disable=invalid-name

class Aircraft(Model):
    "the JHO vehicle"
    def setup(self, sp=False):

        self.sp = sp

        self.fuselage = Fuselage()
        if sp:
            self.wing = WingSP()
        else:
            self.wing = WingGP()
        self.engine = Engine()
        self.emp = Empennage()

        components = [self.fuselage, self.wing, self.engine, self.emp]
        self.smeared_loads = [self.fuselage, self.engine]

        Wzfw = Variable("W_{zfw}", "lbf", "zero fuel weight")
        Wpay = Variable("W_{pay}", 10, "lbf", "payload weight")
        Wavn = Variable("W_{avn}", 8, "lbf", "avionics weight")
        Wwing = Variable("W_{wing}", "lbf", "wing weight for loading")
        etaprop = Variable("\\eta_{prop}", 0.8, "-", "propulsive efficiency")

        self.emp.substitutions[self.emp.vtail.Vv] = 0.04
        self.emp.substitutions[self.emp.vtail.planform.tau] = 0.08
        self.emp.substitutions[self.emp.htail.planform.tau] = 0.08
        self.wing.substitutions[self.wing.planform.tau] = 0.115

        if not sp:
            self.emp.substitutions[self.emp.htail.Vh] = 0.45
            self.emp.substitutions[self.emp.htail.planform.AR] = 5.0
            self.emp.substitutions[self.emp.htail.mh] = 0.1

        constraints = [
            Wzfw >= sum(summing_vars(components, "W")) + Wpay + Wavn,
            Wwing >= sum(summing_vars([self.wing], "W")),
            self.emp.htail.Vh <= (
                self.emp.htail.planform.S
                * self.emp.htail.lh/self.wing.planform.S**2
                * self.wing.planform.b),
            self.emp.vtail.Vv <= (
                self.emp.vtail.planform.S
                * self.emp.vtail.lv/self.wing.planform.S
                / self.wing.planform.b),
            self.wing.planform.tau*self.wing.planform.croot >= self.emp.tailboom.d0
            ]

        return components, constraints

    def flight_model(self, state):
        return AircraftPerf(self, state)

class AircraftLoadingSP(Model):
    "aircraft loading model"
    def setup(self, aircraft, Wcent, Wwing, V, CL):

        # loading = [aircraft.wing.loading(aircraft.wing, Wcent, Wwing, V, CL)]
        loading = []


        return loading

class AircraftPerf(Model):
    "performance model for aircraft"
    def setup(self, static, state):

        self.wing = static.wing.flight_model(static.wing, state)
        self.fuselage = static.fuselage.flight_model(static.fuselage, state)
        self.engine = static.engine.flight_model(state)
        self.htail = static.emp.htail.flight_model(static.emp.htail, state)
        self.vtail = static.emp.vtail.flight_model(static.emp.vtail, state)
        self.tailboom = static.emp.tailboom.flight_model(static.emp.tailboom,
                                                         state)

        self.dynamicmodels = [self.wing, self.fuselage, self.engine,
                              self.htail, self.vtail, self.tailboom]
        areadragmodel = [self.fuselage, self.htail, self.vtail, self.tailboom]
        areadragcomps = [static.fuselage, static.emp.htail,
                         static.emp.vtail,
                         static.emp.tailboom]

        Wend = Variable("W_{end}", "lbf", "vector-end weight")
        Wstart = Variable("W_{start}", "lbf", "vector-begin weight")
        CD = Variable("C_D", "-", "drag coefficient")
        CDA = Variable("CDA", "-", "area drag coefficient")
        mfac = Variable("m_{fac}", 1.0, "-", "drag margin factor")

        dvars = []
        for dc, dm in zip(areadragcomps, areadragmodel):
            if "Cf" in dm.varkeys:
                dvars.append(dm["Cf"]*dc["S"]/static.wing["S"])
            if "Cd" in dm.varkeys:
                dvars.append(dm["Cd"]*dc["S"]/static.wing["S"])
            if "C_d" in dm.varkeys:
                dvars.append(dm["C_d"]*dc["S"]/static.wing["S"])

        constraints = [Wend == Wend,
                       Wstart == Wstart,
                       CDA/mfac >= sum(dvars),
                       CD >= CDA + self.wing.Cd]

        return self.dynamicmodels, constraints

class Cruise(Model):
    "make a cruise flight segment"
    def setup(self, aircraft, N, altitude=15000, latitude=45, percent=90,
              day=355, R=200):
        fs = FlightSegment(aircraft, N, altitude, latitude, percent, day)

        R = Variable("R", R, "nautical_miles", "Range to station")
        constraints = [R/N <= fs["V"]*fs.be["t"]]

        return fs, constraints

class Climb(Model):
    "make a climb flight segment"
    def setup(self, aircraft, N, altitude=15000, latitude=45, percent=90,
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

        return fs, constraints

class Mission(Model):
    "creates flight profile"
    def setup(self, latitude=38, percent=90, sp=False):

        mtow = Variable("MTOW", "lbf", "max-take off weight")
        Wcent = Variable("W_{cent}", "lbf", "center aircraft weight")
        Wfueltot = Variable("W_{fuel-tot}", "lbf", "total aircraft fuel weight")
        LS = Variable("(W/S)", "lbf/ft**2", "wing loading")

        JHO = Aircraft(sp=sp)

        climb1 = Climb(JHO, 10, latitude=latitude, percent=percent,
                       altitude=np.linspace(0, 15000, 11)[1:])
        # cruise1 = Cruise(JHO, 1, R=200, latitude=latitude, percent=percent)
        loiter1 = Loiter(JHO, 5, latitude=latitude, percent=percent)
        # cruise2 = Cruise(JHO, 1, latitude=latitude, percent=percent)
        # mission = [climb1, cruise1, loiter1, cruise2]
        mission = [climb1, loiter1]

        hbend = JHO.emp.tailboom.tailLoad(JHO.emp.tailboom, JHO.emp.htail,
                                          loiter1.fs.fs)
        vbend = JHO.emp.tailboom.tailLoad(JHO.emp.tailboom, JHO.emp.vtail,
                                          loiter1.fs.fs)
        loading = [JHO.wing.spar.loading(JHO.wing, loiter1.fs.fs),
                   JHO.wing.spar.gustloading(JHO.wing, loiter1.fs.fs),
                   hbend, vbend]

        if sp:
            loading.append(TailBoomFlexibility(JHO.emp.htail,
                                               hbend, JHO.wing))

        constraints = [
            mtow >= climb1["W_{start}"][0],
            Wfueltot >= sum(fs["W_{fuel-fs}"] for fs in mission),
            mission[-1]["W_{end}"][-1] >= JHO["W_{zfw}"],
            Wcent >= Wfueltot + JHO["W_{pay}"] + JHO["W_{avn}"] + sum(summing_vars(JHO.smeared_loads, "W")),
            LS == mtow/JHO.wing["S"],
            JHO.fuselage.Vol >= Wfueltot/JHO.fuselage.rhofuel,
            Wcent == loading[0]["W"],
            Wcent == loading[1]["W"],
            loiter1["V"][0] == loading[1].v,
            JHO["W_{wing}"] == loading[1].Ww,
            loiter1.fs.aircraftPerf.wing.CL[0] == loading[1].cl
            ]

        for i, fs in enumerate(mission[1:]):
            constraints.extend([
                mission[i]["W_{end}"][-1] == fs["W_{start}"][0]
                ])

        loading[0].substitutions[loading[0].Nmax] = 5
        loading[1].substitutions[loading[0].Nmax] = 2

        return JHO, mission, loading, constraints

def test():
    " test for integrated testing "
    model = Mission()
    model.substitutions.update({"t_Mission/Loiter": 6})
    model.cost = model["MTOW"]
    model.solve("mosek")
    model = Mission(sp=True)
    model.substitutions.update({"t_Mission/Loiter": 6})
    model.cost = model["MTOW"]
    model.localsolve("mosek")

if __name__ == "__main__":
    M = Mission()
    M.substitutions.update({"t_Mission/Loiter": 6})
    M.cost = M["MTOW"]
    sol = M.solve("mosek")
