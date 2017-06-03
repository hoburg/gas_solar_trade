from solar import Mission

M = Mission(latitude=20, day=140, sp=True)
M.cost = M["W_{total}"]
sol = M.localsolve("mosek")
print sol.table()
