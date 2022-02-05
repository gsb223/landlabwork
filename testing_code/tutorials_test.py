import numpy as np
import matplotlib.pyplot as plt
#%matplotlib inline

dx = 1
x = np.arange(0, 100, dx, dtype=float)
z = np.zeros(x.shape, dtype=float)
D = 0.01

z[x>50] += 100

dt = 0.2 * dx * dx / D
total_time = 1e3
nts = int(total_time/dt)
z_orig = z.copy()
for i in range(nts):
    qs = -D * np.diff(z)/dx
    dzdt = -np.diff(qs)/dx
    z[1:-1] += dzdt*dt

plt.plot(x, z_orig, label="Original Profile")
plt.plot(x, z, label="Diffused Profile")
plt.legend()


from landlab import RasterModelGrid

from landlab.plot.graph import plot_graph
grid = RasterModelGrid((4, 5), xy_spacing=(3,4))
plot_graph(grid, at="node")

plot_graph(grid, at="link")

plot_graph(grid, at="cell")

mg = RasterModelGrid((25, 40), 10.0)

z = mg.add_zeros('topographic__elevation', at='node')

plt.plot(mg.x_of_node, mg.y_of_node, '.')

len(z)

fault_trace_y = 50.0 + 0.25 * mg.x_of_node

z[mg.y_of_node >
  fault_trace_y] += 10.0 + 0.01 * mg.x_of_node[mg.y_of_node > fault_trace_y]

from landlab.plot.imshow import imshow_grid
imshow_grid(mg, 'topographic__elevation')

D = 0.01  # m2/yr transport coefficient
dt = 0.2 * mg.dx * mg.dx / D
dt

mg.set_closed_boundaries_at_grid_edges(True, False, True, False)

len(mg.core_nodes)

qs = mg.add_zeros('sediment_flux', at='link')

for i in range(25):
    g = mg.calc_grad_at_link(z)
    qs[mg.active_links] = -D * g[mg.active_links]
    dzdt = -mg.calc_flux_div_at_node(qs)
    z[mg.core_nodes] += dzdt[mg.core_nodes] * dt

imshow_grid(mg, 'topographic__elevation')







