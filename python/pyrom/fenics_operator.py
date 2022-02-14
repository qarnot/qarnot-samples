def make_pymor_bindings(V, dx, ds, solver_options):
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
    
    # Function continues here with pymor bindings (see below)