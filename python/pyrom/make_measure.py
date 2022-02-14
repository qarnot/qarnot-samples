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