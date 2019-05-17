# coding=utf-8
import math
from ctypes import *
import numpy as np
from map_struct import Point, Segment, Vector

dll = WinDLL("E:/job/amap2local/dll/CoordTransDLL.dll")


class BLH(Structure):
    _fields_ = [("b", c_double),
                ("l", c_double),
                ("h", c_double)]


class XYZ(Structure):
    _fields_ = [("x", c_double),
                ("y", c_double),
                ("z", c_double)]


def bl2xy(b, l):
    """
    :param b: latitude
    :param l: longitude
    :return: x, y
    """
    blh = BLH()
    blh.b = float(b)
    blh.l = float(l)
    blh.h = 0
    xyz = XYZ()
    global dll
    dll.WGS84_BLH_2_HZ_xyH(blh, byref(xyz))
    y, x = xyz.x, xyz.y
    return x, y


def xy2bl(x, y):
    xyz = XYZ()
    blh = BLH()
    xyz.x, xyz.y, xyz.z = y, x, 0
    global dll
    dll.HZ_xyH_2_WGS84_BLH(xyz, byref(blh))
    return blh.b, blh.l


def calc_dist(pt0, pt1):
    """
    计算两点距离
    :param pt0: [x0, y0]
    :param pt1: [x1, y1]
    :return: 
    """
    v0 = np.array(pt0)
    v1 = np.array(pt1)
    dist = np.linalg.norm(v0 - v1)
    return dist


def calc_bl_dist(pt0, pt1):
    """
    计算经纬度距离
    :param pt0: [lng, lat]
    :param pt1: [lng, lat]
    :return: 
    """
    x0, y0 = bl2xy(pt0[1], pt0[0])
    x1, y1 = bl2xy(pt1[1], pt1[0])
    dist = calc_dist([x0, y0], [x1, y1])
    return dist


def calc_include_angle2(seg0, seg1):
    """
    :param seg0: Segment
    :param seg1: 
    :return: cos a
    """
    v0 = np.array([seg0.end_point.px - seg0.begin_point.px, seg0.end_point.py - seg0.begin_point.py])
    v1 = np.array([seg1.end_point.px - seg1.begin_point.px, seg1.end_point.py - seg1.begin_point.py])
    dt = np.sqrt(np.dot(v0, v0)) * np.sqrt(np.dot(v1, v1))
    if dt == 0:
        return 0
    return math.fabs(np.dot(v0, v1) / dt)


def calc_include_angle3(seg0, seg1):
    """
    :param seg0: Segment
    :param seg1: 
    :return: cos a
    """
    v0 = np.array([seg0.end_point.px - seg0.begin_point.px, seg0.end_point.py - seg0.begin_point.py])
    v1 = np.array([seg1.end_point.px - seg1.begin_point.px, seg1.end_point.py - seg1.begin_point.py])
    dt = np.sqrt(np.dot(v0, v0)) * np.sqrt(np.dot(v1, v1))
    if dt == 0:
        return 0
    return np.dot(v0, v1) / dt


def moid(x):
    ZERO = 1e-3
    if x < -ZERO:
        return -1
    elif x > ZERO:
        return 1
    else:
        return 0


def calc_included_angle(s0p0, s0p1, s1p0, s1p1):
    """
    计算夹角
    :param s0p0: 线段0点0 其中点用[x,y]表示
    :param s0p1: 线段0点1 
    :param s1p0: 线段1点0
    :param s1p1: 线段1点1
    :return: 
    """
    v0 = np.array([s0p1[0] - s0p0[0], s0p1[1] - s0p0[1]])
    v1 = np.array([s1p1[0] - s1p0[0], s1p1[1] - s1p0[1]])
    dt = np.sqrt(np.dot(v0, v0)) * np.sqrt(np.dot(v1, v1))
    if dt == 0:
        return 0
    return np.dot(v0, v1) / dt


def is_near_segment(pt0, pt1, pt2, pt3):
    v0 = np.array([pt1[0] - pt0[0], pt1[1] - pt0[1]])
    v1 = np.array([pt3[0] - pt2[0], pt3[1] - pt2[1]])
    dt = np.sqrt(np.dot(v0, v0)) * np.sqrt(np.dot(v1, v1))
    if dt == 0:
        return False
    ret = np.dot(v0, v1) / dt > math.cos(np.pi / 1.5)
    return ret


def get_eps(x0, y0, x1, y1):
    # calculate arctan(dy / dx)
    dx, dy = x1 - x0, y1 - y0
    # angle = angle * 180 / np.pi
    if np.fabs(dx) < 1e-10:
        if y1 > y0:
            return 90
        else:
            return -90
    angle = math.atan2(dy, dx)
    angle2 = angle * 180 / np.pi
    return angle2


def get_diff(e0, e1):
    # 计算夹角，取pi/2到-pi/2区间的绝对值
    de = e1 - e0
    if de >= 180:
        de -= 360
    elif de < -180:
        de += 360
    return math.fabs(de)


def point_project_edge(point, edge):
    n0, n1 = edge.node0, edge.node1
    sp0, sp1 = n0.point, n1.point
    return point_project(point, sp0, sp1)


def point_project_segment(point, segment):
    """
    :param point: Point
    :param segment: Segment
    :return: Point
    """
    x, y = point.px, point.py
    x0, y0 = segment.begin_point.px, segment.begin_point.py
    x1, y1 = segment.end_point.px, segment.end_point.py
    pt, _, _ = point_project([x, y], [x0, y0], [x1, y1])
    return Point(pt[0], pt[1])


def point_project(point, segment_point0, segment_point1):
    """
    :param point: point to be matched
    :param segment_point0: segment
    :param segment_point1: 
    :return: projected point, state
            state 为1 在s0s1的延长线上  
            state 为-1 在s1s0的延长线上
    """
    x, y = point[0:2]
    x0, y0 = segment_point0[0:2]
    x1, y1 = segment_point1[0:2]
    ap, ab = np.array([x - x0, y - y0]), np.array([x1 - x0, y1 - y0])
    ac = np.dot(ap, ab) / (np.dot(ab, ab)) * ab
    dx, dy = ac[0] + x0, ac[1] + y0
    state = 0
    if np.dot(ap, ab) < 0:
        state = -1
    bp, ba = np.array([x - x1, y - y1]), np.array([x0 - x1, y0 - y1])
    if np.dot(bp, ba) < 0:
        state = 1
    return [dx, dy], ac, state


def point2segment2(point, segment):
    """
    计算点到线段距离(Point 版) 
    :param point: Point
    :param segment: Segment
    :return: dist
    """
    return point2segment([point.px, point.py], [segment.begin_point.px, segment.begin_point.py],
                         [segment.end_point.px, segment.end_point.py])


def point2segment(point, segment_point0, segment_point1):
    """
    :param point: point to be matched, [px(double), py(double)] 
    :param segment_point0: segment [px, py]
    :param segment_point1: [px, py]
    :return: dist from point to segment
    """
    x, y = point[0:2]
    x0, y0 = segment_point0[0:2]
    x1, y1 = segment_point1[0:2]
    cr = (x1 - x0) * (x - x0) + (y1 - y0) * (y - y0)
    if cr <= 0:
        return math.sqrt((x - x0) * (x - x0) + (y - y0) * (y - y0))
    d2 = (x1 - x0) * (x1 - x0) + (y1 - y0) * (y1 - y0)
    if cr >= d2:
        return math.sqrt((x - x1) * (x - x1) + (y - y1) * (y - y1))
    r = cr / d2
    px = x0 + (x1 - x0) * r
    py = y0 + (y1 - y0) * r
    return math.sqrt((x - px) * (x - px) + (y - py) * (y - py))


def draw_raw(traj, ax):
    xlist, ylist = [], []
    for point in traj:
        xlist.append(point.px)
        ylist.append(point.py)
    ax.plot(xlist, ylist, marker='o', linestyle='--', color='k', lw=1)


def line2grid(segment_point0, segment_point1):
    x0, y0 = segment_point0[0:2]
    x1, y1 = segment_point1[0:2]

    dx, dy = x1 - x0, y1 - y0
    # 是否用x步进
    if dx == 0:
        x_step = False
    else:
        k = dy / dx
        x_step = math.fabs(k) < 1
    grid = []
    if x_step:
        if x0 > x1:
            x0, y0, x1, y1 = x1, y1, x0, y0
        k = dy / dx
        x, y = int(x0), y0
        while x <= x1:
            grid.append([x, int(y)])
            # grid.append([x, int(y) + 1])
            x, y = x + 1, y + k
    else:
        if y0 > y1:
            x0, y0, x1, y1 = x1, y1, x0, y0
        k = dx / dy
        x, y = x0, int(y0)
        while y <= y1:
            grid.append([int(x), y])
            # grid.append([int(x), y + 1])
            x, y = x + k, y + 1
    return grid


def get_parallel(segment_point0, segment_point1, d):
    """
    获取离线段距离为d的两条平行线段
    :param segment_point0: 线段端点0, Point
    :param segment_point1: 线段端点1, Point
    :param d: 距离d
    :return: segment1(Segment), segment2,
    """
    x0, y0 = segment_point0.px, segment_point0.py
    x1, y1 = segment_point1.px, segment_point1.py
    vec = np.array([x1 - x0, y1 - y0])
    y = np.linalg.norm(vec)
    z = vec / y
    h0 = np.array([z[1], -z[0]])            # 右手边
    h1 = np.array([-z[1], z[0]])            # 左手边
    xh0, yh0 = x0 + h0[0] * d, y0 + h0[1] * d
    xh1, yh1 = x1 + h0[0] * d, y1 + h0[1] * d
    p0, p1 = Point(xh0, yh0), Point(xh1, yh1)
    segment0 = Segment(begin_point=p0, end_point=p1, name='')
    # segment0 = [[xh0, yh0], [xh1, yh1]]
    xh0, yh0 = x0 + h1[0] * d, y0 + h1[1] * d
    xh1, yh1 = x1 + h1[0] * d, y1 + h1[1] * d
    # segment1 = [[xh0, yh0], [xh1, yh1]]
    p0, p1 = Point(xh0, yh0), Point(xh1, yh1)
    segment1 = Segment(begin_point=p0, end_point=p1, name='')
    return segment0, segment1


def get_line_equation(segment_point0, segment_point1):
    """
    Ax + By + C = 0
    :param segment_point0: Point
    :param segment_point1: 
    :return: A, B, C
    """
    x0, y0 = segment_point0.px, segment_point0.py
    x1, y1 = segment_point1.px, segment_point1.py
    a, b, c = y1 - y0, x0 - x1, x1 * y0 - y1 * x0
    d = math.sqrt(a * a + b * b)
    a, b, c = a / d, b / d, c / d
    return a, b, c


def get_cross_point(segment0, segment1):
    """
    获得两线段交点（在延长线上的交点）
    :param segment0: Segment
    :param segment1: 
    :return: d 左手边>0 右手边<0 平行=0    px, py
    """
    sp0, sp1 = segment0.begin_point, segment0.end_point
    a0, b0, c0 = get_line_equation(sp0, sp1)
    sp0, sp1 = segment1.begin_point, segment1.end_point
    a1, b1, c1 = get_line_equation(sp0, sp1)

    d = a0 * b1 - a1 * b0
    if math.fabs(d) < 1e-10:          # 平行
        return d, None, None
    else:
        px = (b0 * c1 - b1 * c0) / d
        py = (c0 * a1 - c1 * a0) / d
        return d, px, py


def vec_cross(vec0, vec1):
    return vec0.px * vec1.py - vec1.px * vec0.py


def is_segment_cross(segment0, segment1):
    """
    计算两线段是否相交
    :param segment0: Segment
    :param segment1:
    :return: bool
    """
    a, b = segment0.begin_point, segment0.end_point
    c, d = segment1.begin_point, segment1.end_point
    ac = Vector(c.px - a.px, c.py - a.py)
    ad = Vector(d.px - a.px, d.py - a.py)
    bc = Vector(c.px - b.px, c.py - b.py)
    bd = Vector(d.px - b.px, d.py - b.py)
    ca, cb, da, db = -ac, -bc, -ad, -bd
    c0, c1 = vec_cross(ac, ad), vec_cross(bc, bd)
    c2, c3 = vec_cross(ca, cb), vec_cross(da, db)
    w0 = moid(c0) * moid(c1)
    w1 = moid(c2) * moid(c3)

    return w0 <= 0 and w1 <= 0


def cut_y(point_list, y):
    """
    截取y以下的线段
    :param point_list: list[Point] 
    :param y: thread y
    :return: new_point_list[Point]
    """
    new_point_list = []
    last_point = None
    for point in point_list:
        if point.py < y:
            new_point_list.append(point)
        else:
            cur_seg = Segment(last_point, point)
            par = Segment(Point(0, y), Point(1, y))
            _, px, py = get_cross_point(cur_seg, par)
            new_point_list.append(Point(px, py))
            break
        last_point = point
    return new_point_list


def cut_x(point_list, x):
    """
    截取x以右的线段
    :param point_list: list[Point] 
    :param x: thread x
    :return: new_point_list[Point]
    """
    new_point_list = []
    last_point = None
    cut = False
    for point in point_list:
        if point.px < x:
            pass
        elif not cut:
            if last_point is None:
                new_point_list.append(point)
                cut = True
            else:
                cur_seg = Segment(last_point, point)
                par = Segment(Point(x, 0), Point(x, 1))
                _, px, py = get_cross_point(cur_seg, par)
                new_point_list.append(Point(px, py))
                cut = True
        else:
            new_point_list.append(point)
        last_point = point
    return new_point_list


def get_dist(point0, point1):
    """
    :param point0: Point
    :param point1: Point
    :return: 
    """
    return calc_dist([point0.px, point0.py], [point1.px, point1.py])


def get_segment_length(segment):
    """
    :param segment: Segment
    :return: 
    """
    return get_dist(segment.begin_point, segment.end_point)


def cut_from_segment(segment, d):
    """
    从segment里面切开距离为d的线段
    :param segment: Segment
    :param d: 
    :return: segment0, segment1
    """
    x0, y0 = segment.begin_point.px, segment.begin_point.py
    x1, y1 = segment.end_point.px, segment.end_point.py
    vec = np.array([x1 - x0, y1 - y0])
    y = np.linalg.norm(vec)
    z0 = vec / y         # 单位向量
    xd, yd = x0 + z0[0] * d, y0 + z0[1] * d
    cr = Point(xd, yd)
    s0 = Segment(segment.begin_point, cr)
    s1 = Segment(cr, segment.end_point)
    return s0, s1


def get_segment_distance(seg0, seg1):
    """
    :param seg0: Segment
    :param seg1: 
    :return: 
    """
    d00, d01 = point2segment2(seg0.begin_point, seg1), point2segment2(seg0.end_point, seg1)
    d10, d11 = point2segment2(seg1.begin_point, seg0), point2segment2(seg1.end_point, seg0)
    return min(min(d00, d01), min(d10, d11))


x_pi = 3.14159265358979324 * 3000.0 / 180.0
pi = 3.1415926535897932384626  # π
a = 6378245.0  # 长半轴
ee = 0.00669342162296594323  # 扁率


def gcj02_to_bd09(lng, lat):
    """
    火星坐标系(GCJ-02)转百度坐标系(BD-09)
    谷歌、高德——>百度
    :param lng:火星坐标经度
    :param lat:火星坐标纬度
    :return:
    """
    z = math.sqrt(lng * lng + lat * lat) + 0.00002 * math.sin(lat * x_pi)
    theta = math.atan2(lat, lng) + 0.000003 * math.cos(lng * x_pi)
    bd_lng = z * math.cos(theta) + 0.0065
    bd_lat = z * math.sin(theta) + 0.006
    return [bd_lng, bd_lat]


def bd09_to_gcj02(bd_lon, bd_lat):
    """
    百度坐标系(BD-09)转火星坐标系(GCJ-02)
    百度——>谷歌、高德
    :param bd_lat:百度坐标纬度
    :param bd_lon:百度坐标经度
    :return:转换后的坐标列表形式
    """
    x = bd_lon - 0.0065
    y = bd_lat - 0.006
    z = math.sqrt(x * x + y * y) - 0.00002 * math.sin(y * x_pi)
    theta = math.atan2(y, x) - 0.000003 * math.cos(x * x_pi)
    gg_lng = z * math.cos(theta)
    gg_lat = z * math.sin(theta)
    return [gg_lng, gg_lat]


def wgs84_to_gcj02(lng, lat):
    """
    WGS84转GCJ02(火星坐标系)
    :param lng: WGS84坐标系的经度
    :param lat: WGS84坐标系的纬度
    :return:
    """
    if out_of_china(lng, lat):  # 判断是否在国内
        return lng, lat
    dlat = transformlat(lng - 105.0, lat - 35.0)
    dlng = transformlng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * pi
    magic = math.sin(radlat)
    magic = 1 - ee * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((a * (1 - ee)) / (magic * sqrtmagic) * pi)
    dlng = (dlng * 180.0) / (a / sqrtmagic * math.cos(radlat) * pi)
    mglat = lat + dlat
    mglng = lng + dlng
    return [mglng, mglat]


def gcj02_to_wgs84(lng, lat):
    """
    GCJ02(火星坐标系)转GPS84
    :param lng:火星坐标系的经度
    :param lat:火星坐标系纬度
    :return:
    """
    if not in_hz(lng, lat):
        return lng, lat
    dlat = transformlat(lng - 105.0, lat - 35.0)
    dlng = transformlng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * pi
    magic = math.sin(radlat)
    magic = 1 - ee * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((a * (1 - ee)) / (magic * sqrtmagic) * pi)
    dlng = (dlng * 180.0) / (a / sqrtmagic * math.cos(radlat) * pi)
    mglat = lat + dlat
    mglng = lng + dlng
    return [lng * 2 - mglng, lat * 2 - mglat]


def transformlat(lng, lat):
    ret = -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat + \
        0.1 * lng * lat + 0.2 * math.sqrt(math.fabs(lng))
    ret += (20.0 * math.sin(6.0 * lng * pi) + 20.0 *
            math.sin(2.0 * lng * pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lat * pi) + 40.0 *
            math.sin(lat / 3.0 * pi)) * 2.0 / 3.0
    ret += (160.0 * math.sin(lat / 12.0 * pi) + 320 *
            math.sin(lat * pi / 30.0)) * 2.0 / 3.0
    return ret


def transformlng(lng, lat):
    ret = 300.0 + lng + 2.0 * lat + 0.1 * lng * lng + \
        0.1 * lng * lat + 0.1 * math.sqrt(math.fabs(lng))
    ret += (20.0 * math.sin(6.0 * lng * pi) + 20.0 *
            math.sin(2.0 * lng * pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lng * pi) + 40.0 *
            math.sin(lng / 3.0 * pi)) * 2.0 / 3.0
    ret += (150.0 * math.sin(lng / 12.0 * pi) + 300.0 *
            math.sin(lng / 30.0 * pi)) * 2.0 / 3.0
    return ret


def in_hz(lat, lng):
    """
    判断是否在国内，不在国内不做偏移
    :param lng:
    :param lat:
    :return:
    """
    return 119 < lng < 121 and 29 < lat < 31
