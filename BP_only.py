from os import path, listdir
import pandas as pd
import numpy as np
import geopandas as gpd
import sys
sys.path.append(r'C:\Program Files\CARIS\HIPS and SIPS\12.1\python\3.11')
from caris.coverage import *
import caris
from hips_project import *
import create_bounding_polygon as BP
import urllib
import ast


def Create_BoundingPolygon(surface):
    """***Replaces the Bounding Box section***
        Creates a Bounding Polygon utilizing the Boundary Polygon script develope by Yan B. This Bounding polygon is used for:
        1. BDB Queries
        2. Loaded as the Bounding Polygon for the Surface
        3. Metadata information for CHSDir or other gometry metadata
    """

    Sur = surface
    

    ## Run the Compute Parameters and the create_bp function from the Bounding Polygon Script.
    Para = BP.compute_parameters(Sur)
    Poly = BP.create_bp(Sur, Para[0], Para[1])

d = r'C:\Users\legermi\Desktop\Surfaces'
dir_lst = listdir(d)


for f in dir_lst:
    if f.endswith(".csar"):
        print(f)
        Create_BoundingPolygon(f'C:\\Users\\legermi\\Desktop\\Surfaces\\{f}')
