def make_fom(filename, option={'solver': 'cg', 'preconditioner': 'ilu'}):
    '''Returns the full order model specified from the mesh filename and solver options'''
    mesh = load_mesh(filename)
    dx, ds = make_measures(mesh)
    V = make_space(mesh)
    option = {'solver': 'cg', 'preconditioner': 'ilu'}
    return make_pymor_bindings(V, dx, ds, option)


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