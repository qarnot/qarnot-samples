# Operators
mass_op = [FenicsMatrixOperator(M, V, V, solver_options=solver_options) for M in mass_mat]
diff_op = [FenicsMatrixOperator(M, V, V, solver_options=solver_options) for M in diff_mat]
robin_left_op = FenicsMatrixOperator(robin_left_mat, V, V, solver_options=solver_options)
source_op = pmb.VectorOperator(space.make_array([source_mat]))

# Parameter projection
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