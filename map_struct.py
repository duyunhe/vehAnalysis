# -*- coding: utf-8 -*-
# @Time    : 2018/9/10 10:55
# @Author  : 
# @简介    : 道路数据结构
# @File    : map_struct.py


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


class LinkDesc(object):
    def __init__(self, line, seq, ort):
        self.line, self.seq, self.ort = line, seq, ort


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

    def add_link(self, link_desc, point):
        """
        :param link_desc: LinkDesc, (line, seq, ort)
        :param point: MapPoint (link to next point)
        :return: 
        """
        self.link_list.append([link_desc, point])

    def add_rlink(self, link_desc, point):
        """
        for oneway side, add one reverse link
        :param link_desc: LinkDesc, (line, seq, ort)
        :param point: MapPoint (link to prev point)
        :return: 
        """
        self.rlink_list.append([link_desc, point])

    def __str__(self):
        return "{0:.2f},{1:.2f}".format(self.px, self.py)


class MapSegment(object):
    def __init__(self, lid):
        self.point_list = []
        self.name, self.rank, self.ort = None, None, None
        self.lid = lid

    def add_point(self, map_point):
        self.point_list.append(map_point)
