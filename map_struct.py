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
    def __init__(self, pid, px, py):
        self.px, self.py = px, py
        self.pid = pid


class MapPoint(Point):
    """
    点表示
    point([px,py]), pid, link_list, rlink_list
    在全局维护list, 
    """
    def __init__(self, pid, px, py):
        super.__init__(pid, px, py)
        self.link_list = []
        self.rlink_list = []

    def add_link(self, edge, node):
        self.link_list.append([edge, node])

    def add_rlink(self, edge, node):
        self.rlink_list.append([edge, node])
