# -*- coding: utf-8 -*-
# @Time    : 2018/9/10 10:55
# @Author  : 
# @简介    : 道路数据结构
# @File    : map_struct.py

import math


class Segment:
    """
    道路中的线段，
    有方向，SegmentID，begin_point, end_point, road_name
    """
    def __init__(self, begin_point=None, end_point=None, name='', sid=0):
        self.begin_point, self.end_point = begin_point, end_point
        self.name, self.sid = name, sid
        self.entrance, self.exit = None, None


class Vector(object):
    def __init__(self, px, py):
        self.px, self.py = px, py

    def __neg__(self):
        return Vector(-self.px, -self.py)


class Point(object):
    def __init__(self, px, py):
        self.px, self.py = px, py
        self.pid = None


class MapPoint(Point):
    """
    点表示
    px, py, pid, link_list, rlink_list
    在全局维护list, 
    """
    def __init__(self, px, py):
        super(MapPoint, self).__init__(px, py)
        self.link_list = []
        self.rlink_list = []

    def add_link(self, edge, node):
        self.link_list.append([edge, node])

    def add_rlink(self, edge, node):
        self.rlink_list.append([edge, node])

    def __str__(self):
        return "{0:.2f},{1:.2f}".format(self.px, self.py)


class MapSegment(object):
    def __init__(self):
        self.point_list = []

    def add_point(self, map_point):
        self.point_list.append(map_point)