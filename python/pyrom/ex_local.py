from model import make_fom, make_param_space
import pymor.basic as pmb

fom = make_fom('mesh.xml')
param_space = make_param_space(fom)

param_set = param_space.sample_randomly(120)
T = fom.solution_space.empty()
for mu in param_set:
  T.append(fom.solve(mu))
  
reduction_basis = pod(U_train, product=fom.h1_0_semi_product, modes=25)
reductor = pmb.InstationaryRBReductor(fom, 
                                      RB=reduction_basis, 
                                      product=fom.h1_0_semi_product)
rom = reductor.reduce()