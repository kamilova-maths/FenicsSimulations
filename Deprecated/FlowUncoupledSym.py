from dolfin import *
from mshr import *
import matplotlib.pyplot as plt
import numpy as np
# Define mesh and geometry - We solve for half of the domain we need, and impose symmetry

# This is a bit misleading, as we have a square domain, which is the rescaled version of a rectangular domain, so we are
# solving on the rescaled domain, the rescaled equations. Then we plot the rescaled version of u and v

mesh = RectangleMesh(Point(0, 0), Point(0.2, 1), 60, 60)
n = FacetNormal(mesh)

# Define Taylor--Hood function space W
V = VectorElement("CG", triangle, 2)
Q = FiniteElement("CG", triangle, 1)
W = FunctionSpace(mesh, MixedElement([V, Q]))

# Define Function and TestFunction(s)
w = Function(W)
(u, p) = split(w)
(v, q) = split(TestFunction(W))

# Define the viscosity and bcs

mu = Constant(1.0)
u_in = Constant(-2.0)
u_c = Constant(-1.0)

# Note, x[0] is r and x[1] is x, and x[1] == 0 is the bottom.
inflow = 'near(x[1], 1.0) && x[0]<=0.1'
weird = 'near(x[1], 1.0) && x[0]>=0.1'
wall = 'near(x[0], 0.2)'
centre = 'near(x[0], 0.0)'
outflow = 'near(x[1], 0.0)'
bcP_inflow = DirichletBC(W.sub(1), 1.0, inflow)
bcu_inflow = DirichletBC(W.sub(0), (0.0, u_in), inflow)
bcP_weird = DirichletBC(W.sub(1), 0.0, weird)
bcu_wall = DirichletBC(W.sub(0), (0.0, u_c), wall)
bcu_outflow = DirichletBC(W.sub(0), (0.0, u_c), outflow)
bcu_symmetry = DirichletBC(W.sub(0).sub(0), Constant(0.0), centre)
bcP_out = DirichletBC(W.sub(1), Constant(0.0), outflow)
bcs = [bcu_wall, bcu_inflow, bcP_weird, bcu_symmetry, bcu_outflow]

# Define stress tensor
x = SpatialCoordinate(mesh)


# We only include the scaling for the derivatives, as the velocity scaling is already introduced in usc
def epsilon(v):
    return (as_tensor([[2*v[0].dx(0), v[0].dx(1) + v[1].dx(0), 0],
                          [v[1].dx(0) + v[0].dx(1), 2*v[1].dx(1), 0],
                          [0, 0, 0]]))


def epsilonns(v):
    return (as_tensor([[v[0].dx(0), v[1].dx(0), 0],
                          [v[0].dx(1), v[1].dx(1), 0],
                          [0, 0, 0]]))


# stress tensor
def sigma(v, p):
    return mu*epsilon(v)-Id(p)


def Id(p):
    return as_tensor([[p, 0, 0],
                      [0, p, 0],
                     [0, 0, p]])


def cond(v):
    return sym(as_tensor([[v[0].dx(0), v[0].dx(1)],
                          [v[1].dx(0), v[1].dx(1)]]))


def sigmabc(v, p):
    return 2*mu*cond(v) - p*Identity(2)


# Define the variational form
f = Constant((0, -1)) # Nothing happens when I change this
# The vectors defined in Fenics are automatically dimensional. We introduce the aspect ratio here, turning the dimensional
# v and u into the non-dimensional ones vsc and usc, noting that usc[0] = (1/asp)*u[0] (or equivalently, we multiply the
# second component by asp.

colors = MeshFunction("size_t", mesh, mesh.topology().dim() - 1)
colors.set_all(0)  # default to zero
# We match the colours to the defined sketch in the Fenics chapter
CompiledSubDomain("near(x[0], 0.0)").mark(colors, 4)
CompiledSubDomain("near(x[1], 1.0) && x[0]<=0.1").mark(colors, 0)
CompiledSubDomain("near(x[1], 1.0) && x[0]>=0.1").mark(colors, 1)
CompiledSubDomain("near(x[0], 0.2)").mark(colors, 2)  # wall

CompiledSubDomain("near(x[1], 0.0)").mark(colors, 3)  # outflow

# Create the measure
ds = Measure("ds", subdomain_data=colors)
# For the governing equations, we have to also multiply by the determinant of the Jacobian, which is asp. All of the
# terms have to be multiplied by asp, which, as they are equal to zero, means we can just remove asp. Note as well that
# the Jacobian for this rescaling is symmetric, so inv(J)*Transp(J) = I, so everything is also multiplied by I.

a1 = -(inner(mu*epsilon(u), epsilon(v))) * dx + p*div(v) * dx
a2 = (- div(u) * q - dot(f, v)) * dx

# For the boundary terms, note that ds(3) is the only one here that varies along x[1], which is where the asp rescaling
# is. Therefore we have to multiply only that term by (1/asp), or equivalently, multiply the other terms by asp.
b1 = - dot(dot(sigmabc(u, 0.0), v), n) * ds(1)
b3 = - dot(dot(mu*sym(grad(u)), v), n) * ds(3)
b4 = - dot(dot(sigmabc(u, 0.0), v), n) * ds(4)
F = a1 + a2

# Solve problem
solve(F == 0, w, bcs)

# Plot solutions
(u, p) = w.split()
File("Results/velocitySym.pvd") << u

# flux = inner(u, u)*ds(2)
# total_flux1 = assemble(flux)
# print("Total flux is", total_flux1)

# energy = 0.5*dot(grad(u), grad(u))*dx
# E = assemble(energy)
# print("Energy is ", energy)

# W2 = VectorFunctionSpace(mesh, V, 2)
# flux_u = project(-grad(u), W2)
# plot(flux_u, title='flux field')
# plt.show()
# flux_x, flux_y = flux_u.split(deepcopy=True) # extract components
# plot(flux_x, title='x-component of flux (-grad(u))')
# plt.show()
# plot(flux_y, title='y-component of flux (-grad(u))')
# plt.show()
#
# c = plot(p, title='pressure')
# plt.colorbar(c)
# plt.show()
#
# c = plot(u, title='velocity')
# plt.colorbar(c)
# plt.show()