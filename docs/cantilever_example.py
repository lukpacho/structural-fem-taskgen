### CODE
import calfem.geometry as cfg
import calfem.mesh as cfm
import calfem.vis_mpl as cfv
import calfem.utils as cfu
import calfem.core as cfc
import numpy as np

# Material and Section data
t = 0.1
v = 0.3
E = 50e6
ptype = 1
ep = [ptype,t]
D = cfc.hooke(ptype, E, v)

# Marker constans definitions
mark_fixed = 10
mark_f1 = 1
mark_f2 = 2

# Forces and prescribed displacements
f_val1 = 100
f_val2 = -100


g = cfg.geometry()

points = [[3, 0], [3, 1], [0, 1], [0, 0]]              #1, 2, 3, 4

for xp, yp in points:
    g.point([xp, yp])

g.setPointMarker(ID=0, marker=mark_f1)
g.setPointMarker(ID=1, marker=mark_f2)

splines = [[0,1], [1,2], [2,3], [3,0]]

for s in splines:
    g.spline(s)

g.curve_marker(ID=2, marker=mark_fixed)

g.surface([0, 1, 2, 3])

cfv.figure(fig_size=(10,10))
cfv.draw_geometry(g, draw_points=True, label_curves=True, label_points=True)

mesh = cfm.GmshMesh(g)

mesh.el_type = el_type
mesh.dofs_per_node = dofs_per_node
mesh.el_size_factor = el_size_factor

coords, edof, dofs, bdofs, elementmarkers = mesh.create()

cfv.figure(fig_size=(10,10))
cfv.draw_mesh(coords,
              edof,
              el_type=mesh.el_type,
              dofs_per_node=mesh.dofs_per_node,
              face_color=(0.9, 0.9, 0.9),
              filled=True
              )

n_dofs = np.size(dofs)
ex, ey = cfc.coordxtr(edof, coords, dofs)

K = np.zeros([n_dofs,n_dofs])
for eltopo, elx, ely in zip(edof, ex, ey):
    Ke = cfc.plante(elx, ely, ep, D)
    cfc.assem(eltopo, K, Ke)

bc = np.array([], 'i')
bcVal = np.array([], 'f')

bc, bcVal = cfu.applybc(bdofs, bc, bcVal, mark_fixed, value=0.0, dimension=0)

f = np.zeros([n_dofs, 1])

# dimension = 0 - 'all', 1 - 'x', and 2 - 'y'
cfu.applyforce(bdofs, f, mark_f1, f_val1, dimension=1)
cfu.applyforce(bdofs, f, mark_f2, f_val2, dimension=1)

a, r = cfc.solveq(K, f, bc, bcVal)

ed = cfc.extract_eldisp(edof,a)

es_x_MPa = []
es_y_MPa = []

for i in range(edof.shape[0]):
    es, et = cfc.plants(ex[i,:], ey[i,:], ep, D, ed[i,:])
    es_x_MPa.append(es[0][0]/1000)
    es_y_MPa.append(es[0][1]/1000)

cfv.figure(fig_size=(10,10))
cfv.draw_element_values(es_x_MPa,
                        coords,
                        edof,
                        mesh.dofs_per_node,
                        mesh.el_type,
                        displacements=None,
                        draw_elements=False,
                        draw_undisplaced_mesh=False,
                        title="sigma_x")

cfv.colorbar(shrink=0.3)

### END OF CODE