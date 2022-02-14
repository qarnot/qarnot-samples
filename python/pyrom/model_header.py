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