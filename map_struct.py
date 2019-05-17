# -*- coding: utf-8 -*-
# @Time    : 2018/9/10 10:55
# @Author  : 
# @简介    : 道路数据结构
# @File    : map_struct.py

import math


def segment2point(seg_list):
    """
    :param seg_list: list of Segment
    :return: 
    """
    point_list = [seg_list[0].begin_point]
    for seg in seg_list:
        point_list.append(seg.end_point)
    return point_list


class Vector:
    """
    向量
    """
    def __init__(self, px, py):
        self.px, self.py = px, py

    def __neg__(self):
        return Vector(-self.px, -self.py)


class Point:
    """
    点，px py 
    """
    def __init__(self, px, py):
        self.px, self.py = px, py
        self.cross = 0      # 是否为交点   1 进路口 2 出路口
        self.cross_name = ""
        self.cross_seg = -1             # 相交时本线段的序号
        self.cross_other_seg = -1       # 对面相交线段的序号

    def __eq__(self, other):
        return math.fabs(self.px - other.px) < 1e-5 and math.fabs(self.py - other.py) < 1e-5


class Segment:
    """
    道路中的线段，
    有方向，SegmentID，begin_point, end_point, road_name
    """
    def __init__(self, begin_point=None, end_point=None, name='', sid=0):
        self.begin_point, self.end_point = begin_point, end_point
        self.name, self.sid = name, sid
        self.entrance, self.exit = None, None

    def set_invert(self):
        self.begin_point, self.end_point = self.end_point, self.begin_point

    def set_sid(self, sid):
        self.sid = sid

    def set_name(self, name):
        self.name = name

    def add_entrance(self, point):
        """
        添加一个路口的进路口点
        :param point: Point
        :return: 
        """
        self.entrance = point

    def add_exit(self, point):
        self.exit = point


class Road:
    """
    道路
    字段：道路名，等级，道路中线段list
    """
    def __init__(self, name, level, rid):
        self.name, self.level = name, level
        self.seg_list = []              # list of Segment
        self.point_list = []            # list of Point
        self.rid = rid
        self.cross_list = []
        self.es, self.bs = 0, 0         # end connected to other, begin connected to other
        self.mark = 0
        self.grid_set = None

    def set_rid(self, rid):
        self.rid = rid

    def set_grid_set(self, gs):
        self.grid_set = gs

    def set_mark(self, mark):
        self.mark = mark

    def add_point(self, point):
        self.point_list.append(point)

    def set_point_list(self, point_list):
        self.point_list = point_list

    def gene_segment(self):
        self.seg_list = []
        last_point = None
        sid = 0
        for point in self.point_list:
            if last_point is not None:
                seg = Segment(last_point, point, self.name, sid)
                self.seg_list.append(seg)
                sid += 1
            last_point = point

    def set_cross_list(self, cross_list):
        """
        该路段已经有的交点，用于cross函数中判断是否会有不同路段去匹配到同一条道路上
        :param cross_list: 
        :return: 
        """
        self.cross_list = cross_list

    def add_segment(self, segment):
        """
        添加线段
        :param segment: Segment
        :return: 
        """
        self.seg_list.append(segment)

    def get_entrance(self):
        e_list = []
        for seg in self.seg_list:
            if seg.entrance is not None:
                e_list.append(seg.entrance)
        return e_list

    def get_exit(self):
        e_list = []
        for seg in self.seg_list:
            if seg.exit is not None:
                e_list.append(seg.exit)
        return e_list

    def get_name(self):
        return self.name

    def get_path(self):
        return segment2point(self.seg_list)

    def get_path_without_crossing(self):
        """
        对外接口
        路口线段隐藏，得到新的list
        由于整条完整的道路被路口分开，因此存在多个list，每个list代表一条被隔开的道路list
        :return: path_list
        """
        path_list, temp_seg_list = [], []
        # path_list : list of path
        # path: list of Point
        # temp_seg_list: temp segment list
        cross = False
        for seg in self.seg_list:
            if seg.entrance is None and seg.exit is not None:
                cross = True
                break
            if seg.entrance is not None and seg.exit is None:
                break

        for i, seg in enumerate(self.seg_list):
            if seg.entrance is None and seg.exit is None:
                if not cross:
                    temp_seg_list.append(seg)
            elif seg.entrance is not None and seg.exit is not None:
                # 在正常情况下不会出现，因为道路的交叉点会将segment分开
                # 不会出现同一条segment里面既有路口一侧又有路口另一侧的情况
                # 测试各种情况用
                if not cross:
                    s0 = Segment(seg.begin_point, seg.entrance)
                    temp_seg_list.append(s0)
                    s1 = Segment(seg.exit, seg.end_point)
                    path_list.append(segment2point(temp_seg_list))
                    temp_seg_list = [s1]
                else:
                    s0 = Segment(seg.exit, seg.entrance)
                    temp_seg_list = [s0]
                    path_list.append(segment2point(temp_seg_list))
                    temp_seg_list = []
            elif seg.entrance is not None and seg.exit is None:
                s0 = Segment(seg.begin_point, seg.entrance)
                temp_seg_list.append(s0)
                path_list.append(segment2point(temp_seg_list))
                temp_seg_list = []
                cross = True
            elif seg.entrance is None and seg.exit is not None:
                s1 = Segment(seg.exit, seg.end_point)
                temp_seg_list.append(s1)
                cross = False
        if len(temp_seg_list) != 0:
            path_list.append(segment2point(temp_seg_list))
        return path_list

