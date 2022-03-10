import enum
from typing import Tuple

class Corner(enum.IntEnum):
    BL = 1
    BR = 2
    TL = 4
    TR = 8

def bbox_middle(bbox: Tuple[float,float,float,float]):
    return (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2

def bbox_width(bbox: Tuple[float,float,float,float]):
    return bbox[2] - bbox[0]

def bbox_height(bbox: Tuple[float,float,float,float]):
    return bbox[3] - bbox[1]