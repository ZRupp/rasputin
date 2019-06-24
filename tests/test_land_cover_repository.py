from pathlib import Path
import numpy as np
from pyproj import Proj
from shapely.geometry import Polygon
from rasputin.reader import GeoPolygon
from rasputin import triangulate_dem as td
from rasputin.globcov_repository import GlobCovRepository, GeoPoints, LandCoverType
from rasputin.reader import RasterRepository
import os


def test_coordinates_to_indices():
    dx = dy = 10  # Raster resolution
    M, N = 100, 100  # Number of rows and columns in raster
    x0 = 0  # Model x tie point
    y1 = 100  # Model y tie point
    points = td.point2_vector([[5.0, 95.0], [15.0, 85.0]])
    res = np.asarray(td.coordinates_to_indices(x0, y1, dx, dy, M, N, points))
    assert res[0].tolist() == [0, 0]
    assert res[1].tolist() == [1, 1]


def test_extract_land_types():
    path = Path('/Users/skavhaug/projects/rasputin_data/globcov')
    xy = np.array([[8, 60], [8.1, 61]], dtype='d')
    proj = Proj(init="EPSG:4326")
    domain = GeoPolygon(projection=proj, polygon=Polygon())
    geo_points = GeoPoints(xy=xy, projection=proj)
    gcr = GlobCovRepository(path=path)
    gcr.read(land_type=LandCoverType.crop_type_2, geo_points=geo_points, domain=domain)


def test_construct_triangulation_with_land_types():
    assert "RASPUTIN_DATA_DIR" in os.environ
    data_dir = Path(os.environ["RASPUTIN_DATA_DIR"])
    lt_repo = GlobCovRepository(path=data_dir / "globcov")
    dem_repo = RasterRepository(directory=data_dir / "dem_archive")
    x0 = 8.54758671814368
    y0 = 60.898468
    input_coordinate_system = Proj(init="EPSG:4326")
    target_coordinate_system = Proj(init="EPSG:32633")
    polygon = Polygon.from_bounds(xmin=x0 - 0.01,
                                  xmax=x0 + 0.01,
                                  ymin=y0 - 0.01,
                                  ymax=y0 + 0.01)
    domain = GeoPolygon(polygon=polygon,
                        projection=input_coordinate_system).transform(target_projection=target_coordinate_system)
    raster_data_list, cpp_polygon = dem_repo.read(domain=domain)
    points, faces = td.lindstrom_turk_by_ratio(raster_data_list,
                                               cpp_polygon,
                                               1.1)
    assert len(faces)
    assert len(points)
    centers = np.asarray(td.cell_centers(points, faces))[:, :2]
    land_types = lt_repo.land_cover(land_types=None,
                                    geo_points=GeoPoints(xy=centers,
                                                         projection=target_coordinate_system),
                                    domain=domain)
    assert len(land_types) == len(faces)