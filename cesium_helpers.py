import pandas as pd
import requests
from czml3 import Document, Packet, Preamble
from czml3.properties import (Color, Material, Point, Polygon, Polyline,
                              PolylineMaterial, Position, PositionList,
                              SolidColorMaterial)
from czml3.utils import get_color
from telluric.constants import WGS84_CRS


def fill_height(coords):
    for x, y in coords:
        yield x, y, 0


def flatten_line(coords):
    for point in coords:
        for coord in point:
            yield coord


def packet_from_point(feat, id_=None):
    name = feat.get("name", "point_{}".format(id_) if id_ is not None else "point_0")
    description = feat.get("description", name)
    color = get_color(feat.get("color", 0xff0000))
    point = feat.get_shape(WGS84_CRS)

    return Packet(
        id=id_,
        name=name,
        description=description,
        point=Point(color=color, pixelSize=5),
        position=Position(
            cartographicDegrees=[point.x, point.y, get_elevation(point.x, point.y)]
        ),
    )


def packet_from_line(feat, id_=None):
    name = feat.get("name", "line_{}".format(id_) if id_ is not None else "line_0")
    description = feat.get("description", name)
    color = get_color(feat.get("color", 0xff0000))
    line = feat.get_shape(WGS84_CRS)

    return Packet(
        id=id_,
        name=name,
        description=description,
        polyline=Polyline(
            positions=PositionList(
                cartographicDegrees=list(flatten_line(fill_height(line.coords)))
            ),
            material=PolylineMaterial(solidColor=SolidColorMaterial(color=color)),
        ),
    )


def packet_from_polygon(feat, id_=None):
    name = feat.get(
        "name", "polygon_{}".format(id_) if id_ is not None else "polygon_0"
    )
    description = feat.get("description", name)
    color = get_color(feat.get("color", 0xff0000))
    polygon = feat.get_shape(WGS84_CRS)

    return Packet(
        id=id_,
        name=name,
        description=description,
        polygon=Polygon(
            positions=PositionList(
                cartographicDegrees=list(
                    flatten_line(fill_height(polygon.exterior.coords))
                )
            ),
            material=Material(solidColor=SolidColorMaterial(color=color)),
        ),
    )


GEOM_MAPPING = {
    "Point": packet_from_point,
    "LineString": packet_from_line,
    "Polygon": packet_from_polygon,
}


def packet_from_geofeature(feat):
    try:
        func = GEOM_MAPPING[feat.geometry.type]
    except KeyError as e:
        raise NotImplementedError(
            "No transformation available for {}".format(feat.geometry.type)
        ) from e

    return func(feat)


def czml_from_feature_collection(fc, name):
    packets = []
    for feat in fc:
        packets.append(packet_from_geofeature(feat))

    document = Document([Preamble(name=name), *packets])

    return document

