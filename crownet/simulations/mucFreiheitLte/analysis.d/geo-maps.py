# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
from re import I
from folium.plugins import MousePosition
from pyproj.proj import Proj
import geopandas as g
import os
import pandas as pd
import geopandas as gpd
from roveranalyzer.utils import Project
import contextily  as ctx
from shapely.geometry import Polygon, box, Point
from matplotlib import pyplot as plt
from matplotlib.patches import Patch
import numpy as np
import random
import random


class OppIniWriter:

    @classmethod
    def MF_Subway(cls):
        offset = np.array([692152.0894735109, 5337384.6661008])  # x / y (easting/  northing)
        bound = np.array([415.0, 415.0])
        return cls(Project.UTM_32N, offset, bound)

    def __init__(self, source_crs, offset, bound, seed=42) -> None:
        self.nodes = []
        self._node_count = 0
        self.crs = Project.WSG84_lat_lon
        self.to_lat_lon : Project = Project(source_crs=source_crs, dest_crs=Project.WSG84_lat_lon)
        self.offset = offset
        self.bound = bound
        self.seed = seed

    def add_point(self, x: float, y:float):
        _p = np.array([x, y])
        if all(_p >= 0) and all(_p <= self.bound):
            _d = Point(self.offset + _p)
            self.nodes.append([self._node_count, _d.x, _d.y])
            self._node_count += 1
        else:
            raise ValueError("Out of bound")

    def to_geo_frame(self, epsg=Project.OpenStreetMaps):

        geo = [Point(x, y) for _, x, y in self.nodes]
        df = pd.DataFrame(self.nodes, columns=["id","x", "y"])
        df = gpd.GeoDataFrame(df, geometry=geo, crs=Project.UTM_32N)
        df = df.to_crs(epsg=epsg.replace("EPSG:", "")) # Google
        return df
    
    def write_config(self, writer, config=""):
        _df = self.to_geo_frame(Project.WSG84_lat_lon)

        writer.write(config)
        writer.write("\n")
        writer.write(f"*.numMisc = {len(self.nodes)}\n")
        for id, row in _df.iterrows():
            writer.write(f"*.misc[{id}].mobility.initialLatitude = {row.geometry.y}deg\n")
            writer.write(f"*.misc[{id}].mobility.initialLongitude = {row.geometry.x}deg\n")
        writer.write("\n")


    def uniform(self, num_nodes):
        rnd = random.Random(self.seed)
        for i in range(num_nodes):
            self.add_point(rnd.uniform(0.0, self.bound[0]), rnd.uniform(0.0, self.bound[1]))
        
        
class ClickHandler:
    def __init__(self, offset) -> None:
        self.offset = offset

    def on_click(self, event):
        x = round( event.xdata - self.offset[0], 2)
        y = round( event.ydata - self.offset[1], 2)
        print(f"peds.append([-1, '#187EAA', '#187EAA', Point([{x}, {y}] + offset)])")

    def on_click_geo(self, event):
        s = g.GeoSeries([Point([event.xdata, event.ydata])], crs=f"EPSG:{WGS84_pseudo_m}")
        s = s.to_crs(epsg=WGS84_lat_lon)
        print(f"peds.append([-1, '#187EAA', '#187EAA', Point([{s.loc[0].x}, {s.loc[0].y}])]")


w = OppIniWriter.MF_Subway()
w.uniform(100)

class W:
    def write(self, x):
        print(x, end='')

# with open("muc_subway_100_uniform.ini", "w", encoding="utf-8") as f:
    # f.write(f"# python seed for random placement {w.seed}\n")
    # w.write_config(writer = f, config="[Config muc_subway_100_uniform]")

ax = w.to_geo_frame().plot()
ax.get_figure().show()


print("done.")


# %%
