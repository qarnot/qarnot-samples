end_time = 3*60
dt = 1
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