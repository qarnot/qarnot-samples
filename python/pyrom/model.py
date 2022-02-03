import dolfin as df
from pymor.models.basic import InstationaryModel


''''These are the geometric constants that were used for the mesh creation
They are needed for subdomains definition'''
die_l = 20/1000
die_h = 3/1000
die_w = die_l
casing_l = 30/1000
casing_h = 5/1000
casing_w = casing_l
paste_h = 0.2/1000
block_l = 40/1000
block_h = 5/1000
block_w = 40/1000

domain_dict = {'block':1,
               'paste':2,
               'casing':3,
               'die':4}


def load_mesh(filename):
    return df.Mesh(filename)


def make_measures(mesh):
    '''Defines subdomains for the mesh and returns associated measures'''
    tol = 1e-7  # Constant for numerical precision

    boundary_air = df.CompiledSubDomain('on_boundary && x[2] > 0 - tol',
                                tol=tol)

    sub_die = df.CompiledSubDomain('x[0] <= xb + tol && x[0] >= -xb - tol \
                                 && x[1] <= yb + tol && x[1] >= -yb - tol \
                                 && x[2] <= z1 + tol && x[2] >= z0 - tol',
                                   tol=tol, xb = die_l/2, yb = die_w/2,
                                   z1 = -paste_h-casing_h+die_h, z0 = -paste_h-casing_h)

    sub_casing = df.CompiledSubDomain('x[0] <= xb + tol && x[0] >= -xb - tol \
                                 && x[1] <= yb + tol && x[1] >= -yb - tol \
                                 && x[2] <= z1 + tol && x[2] >= z0 - tol',
                                   tol=tol, xb = casing_l/2, yb = casing_w/2,
                                   z1 = -paste_h, z0 = -paste_h-casing_h)

    sub_paste = df.CompiledSubDomain('x[0] <= xb + tol && x[0] >= -xb - tol \
                                 && x[1] <= yb + tol && x[1] >= -yb - tol \
                                 && x[2] <= z1 + tol && x[2] >= z0 - tol',
                                   tol=tol, xb = casing_l/2, yb = casing_w/2,
                                   z1 = 0, z0 = -paste_h)

    markers = df.MeshFunction('size_t', mesh, 3)
    markers.set_all(domain_dict['block'])
    sub_casing.mark(markers, domain_dict['casing'])
    sub_die.mark(markers, domain_dict['die'])
    sub_paste.mark(markers, domain_dict['paste'])

    boundary_markers = df.MeshFunction('size_t', mesh, 2)
    boundary_markers.set_all(0)
    boundary_air.mark(boundary_markers, 1)

    dx = df.Measure('dx', domain=mesh, subdomain_data=markers)
    ds = df.Measure('ds', domain=mesh, subdomain_data=boundary_markers)
    return dx, ds


def make_space(mesh):
    return df.FunctionSpace(mesh, 'P', 1)


class InstationaryParametricMassModel(InstationaryModel):
    '''This simple class encapsulate pymor.InstationaryModel which can't have a parametric mass.
    We simply assemble the mass the before handing everything to the base class. It causes no problem
    since the mass is not time dependant'''
    def __init__(self, T, initial_data, operator, rhs, mass=None, time_stepper=None, num_values=None,
                 output_functional=None, products=None, error_estimator=None, visualizer=None, name=None):
        super().__init__(T, initial_data, operator, rhs, mass, time_stepper, num_values, 
                         output_functional, products, error_estimator, visualizer, name)

    def _compute_solution(self, mu=None, **kwargs):
        mu = mu.with_(t=0.)
        U0 = self.initial_data.as_range_array(mu)
        U = self.time_stepper.solve(operator=self.operator,
                                        rhs=self.rhs,
                                        initial_data=U0,
                                        mass=self.mass.assemble(mu),
                                        initial_time=0, end_time=self.T, mu=mu, num_values=self.num_values)
        return U


def make_pymor_bindings(V, dx, ds, solver_options):
    '''Assemble the Fenics operator and binds them to pymor.Operator with parameter separation
    Returns the full order model (pymor.Model)'''
    import pymor.basic as pmb
    from pymor.bindings.fenics import FenicsVectorSpace, FenicsMatrixOperator
    from pymor.algorithms.timestepping import ImplicitEulerTimeStepper

    space = FenicsVectorSpace(V)

    # Operators matrix
    u = df.TrialFunction(V)
    v = df.TestFunction(V)
    mass_mat = [df.assemble(df.inner(u, v)*dx(i)) for i in domain_dict.values()]
    diff_mat = [df.assemble(df.inner(df.grad(u), df.grad(v))*dx(i)) for i in domain_dict.values()]
    robin_left_mat = df.assemble(u*v*ds(1))
    source_mat = df.assemble(v*dx(domain_dict['die']))

    # Norms matrix
    l2_mat = df.assemble(df.inner(u, v)*df.dx)
    l2_0_mat = l2_mat.copy()
    h1_mat = df.assemble(df.inner(df.grad(u), df.grad(v))*dx)
    h1_0_mat = h1_mat.copy()

    # Operators
    mass_op = [FenicsMatrixOperator(M, V, V, solver_options=solver_options) for M in mass_mat]
    diff_op = [FenicsMatrixOperator(M, V, V, solver_options=solver_options) for M in diff_mat]
    robin_left_op = FenicsMatrixOperator(robin_left_mat, V, V, solver_options=solver_options)
    source_op = pmb.VectorOperator(space.make_array([source_mat]))

    # Param projection
    project_lamb = [pmb.ProjectionParameterFunctional(f'lamb_{dom}', 1, 0) for dom in domain_dict.keys()]
    project_capa = [pmb.ProjectionParameterFunctional(f'capa_{dom}', 1, 0) for dom in domain_dict.keys()]

    # Separated operator
    mass = pmb.LincombOperator(mass_op, project_capa)

    op = pmb.LincombOperator([*diff_op,
                              robin_left_op],
                             [*project_lamb,
                              pmb.ExpressionParameterFunctional('h[0]', {'h':1})])

    rhs = pmb.LincombOperator([source_op],
                              [pmb.ExpressionParameterFunctional('phi[0]', {'phi':1})])

    end_time = 10*60
    dt = 5
    fom = InstationaryParametricMassModel(
                            T = end_time, 
                            initial_data=space.make_array([df.project(df.Constant(0), V).vector()]),
                            operator=op,
                            rhs=rhs,
                            mass=mass,
                            time_stepper=ImplicitEulerTimeStepper(end_time//dt),
                            num_values= None,
                            products={'l2': FenicsMatrixOperator(l2_mat, V, V),
                                       'l2_0': FenicsMatrixOperator(l2_0_mat, V, V),
                                       'h1': FenicsMatrixOperator(h1_mat, V, V),
                                       'h1_0_semi': FenicsMatrixOperator(h1_0_mat, V, V)},
                            visualizer = None
                            )
    return fom
    

def make_param_space():
    ''''Define ranges for parameter values and return the associated parameter space
        Return:
            pymor.ParameterSpace: the parametre space'''
    import pymor.basic as pmb
    params = pmb.Parameters({
                    'lamb_die': 1,
                    'lamb_block': 1,
                    'lamb_paste': 1,
                    'lamb_casing': 1,
                    'capa_die': 1,
                    'capa_block': 1,
                    'capa_paste': 1,
                    'capa_casing': 1,
                    'h': 1,
                    'phi': 1})

    capa_range = (10**5, 10**7)
    param_range = {'lamb_die': (5, 100),
                   'lamb_block': (100, 500),
                   'lamb_paste' : (0.5, 10),
                   'lamb_casing': (10, 200),
                   'capa_die': capa_range,
                   'capa_block': capa_range,
                   'capa_paste': capa_range,
                   'capa_casing': capa_range,
                   'h' : (5, 100),
                   'phi': (2 / die_h / die_l / die_l, 30 / die_h/ die_l / die_l)}
    return pmb.ParameterSpace(params, param_range)


def make_fom(filename, option={'solver': 'cg', 'preconditioner': 'ilu'}):
    '''Returns the full order model specified from the mesh filename and solver options'''
    mesh = load_mesh(filename)
    dx, ds = make_measures(mesh)
    V = make_space(mesh)
    option = {'solver': 'cg', 'preconditioner': 'ilu'}
    return make_pymor_bindings(V, dx, ds, option)


def used_time():
    '''The timestamps used (time step is 10s) for building the ROM without taking too much time
    Emphasis is put on the transitory part because solution are more diverse there'''
    return [1, 3, 6, 12, 18, 24, 36, 48, 60, 72, 84, 96, 108, 120]


def str_radica_ind(radica, index):
    return f'/{radica}_{index}'


def dump_sol(hdf_file: df.HDF5File, U_list, index: int, partition: str):
    '''Write solution U_list[index] to hdf5 file under the giver partition'''
    u_dump = df.Function(U_list.space.V, U_list._list[index].real_part.impl)
    hdf_file.write(u_dump, partition)


def dump_sol_list(filename: str, U_list, radica: str='sol'):
    '''Write solution list to hdf5 file, on the partition /{radica}'''
    hdf_file = df.HDF5File(U_list.space.V.mesh().mpi_comm(), filename, 'w')
    for i in range(len(U_list)):
        dump_sol(hdf_file, U_list, i, str_radica_ind(radica, i))
    hdf_file.close()
    

def load_sol_list(filename: str, space, radica: str='sol'):
    '''Load solution from filename that are in the form /{radica}_i'''
    hdf = df.HDF5File(space.V.mesh().mpi_comm(), filename, 'r')
    vecs = []
    i = 0
    while hdf.has_dataset(str_radica_ind(radica, i)):
        u_load = df.Function(space.V)
        hdf.read(u_load, str_radica_ind(radica, i))
        vecs.append(u_load.vector())
        i += 1
    hdf.close()
    return space.make_array(vecs)
        
