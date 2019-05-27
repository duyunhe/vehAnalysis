# coding=utf-8
import math

import numpy as np
from map_struct import Point


x_pi = 3.14159265358979324 * 3000.0 / 180.0
pi = 3.1415926535897932384626  # π
earth_a = 6378245.0  # 长半轴
ee = 0.00669342162296594323  # 扁率


def calc_point_dist(pt0, pt1):
    """
    :param pt0: Point
    :param pt1: 
    :return: 
    """
    v0 = np.array([pt0.x, pt0.y])
    v1 = np.array([pt1.x, pt1.y])
    dist = np.linalg.norm(v0 - v1)
    return dist


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
    v0 = np.array([seg0.end_point.x - seg0.begin_point.x, seg0.end_point.y - seg0.begin_point.y])
    v1 = np.array([seg1.end_point.x - seg1.begin_point.x, seg1.end_point.y - seg1.begin_point.y])
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
    pt = [point.px, point.py]
    p0 = [segment.begin_point.px, segment.begin_point.py]
    p1 = [segment.end_point.px, segment.end_point.py]
    pt, _, _ = point_project(pt, p0, p1)
    return Point(pt[0], pt[1])


def point_project(point, p0, p1):
    """
    :param point: point to be matched
    :param p0: Segment point0
    :param p1: Segment point1
    :return: projected point, state
            state 为2 在s0s1的延长线上  
            state 为1 在s1s0的延长线上
    """
    x, y = point[0:2]
    x0, y0 = p0[0:2]
    x1, y1 = p1[0:2]
    ap, ab = np.array([x - x0, y - y0]), np.array([x1 - x0, y1 - y0])
    if np.dot(ap, ab) < 0:
        proj_pt = [x0, y0]
        px, py, state, dist = x0, y0, 1, calc_dist(point, proj_pt)
    else:
        bp, ba = np.array([x - x1, y - y1]), np.array([x0 - x1, y0 - y1])
        if np.dot(bp, ba) < 0:
            proj_pt = [x1, y1]
            px, py, state, dist = x1, y1, 2, calc_dist(point, proj_pt)
        else:
            ac = np.dot(ap, ab) / (np.dot(ab, ab)) * ab
            proj_pt = [ac[0] + x0, ac[1] + y0]
            px, py, state, dist = ac[0] + x0, ac[1] + y0, 0, calc_dist(point, proj_pt)

    return [px, py], state, dist


def point2segment(point, segment_point0, segment_point1):
    """
    :param point: Point
    :param segment_point0: 
    :param segment_point1: 
    :return: dist from point to segment
    """
    x, y = point.x, point.y
    x0, y0 = segment_point0.x, segment_point0.y
    x1, y1 = segment_point1.x, segment_point1.y
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


def point_segment_prob(point, segment):
    """
    calculate emit probability of single matching 
    :param point: Point
    :param segment: Segment
    :return: probability, dist from matching point to fact point, matching state, matching point on road
    """
    pt = [point.x, point.y]
    p0 = [segment.begin_point.x, segment.begin_point.y]
    p1 = [segment.end_point.x, segment.end_point.y]
    proj, state, dist = point_project(pt, p0, p1)
    dev = 5
    omg = -0.5 * math.pow(dist / dev, 2)
    p = -math.log(math.sqrt(2 * math.pi) * dev) + omg
    return p, dist, state, proj


def route_trans_prob(euclid_dist, route_dist):
    """
    calculate trans probability
    :param euclid_dist: 
    :param route_dist: 
    :return: 
    """
    beta = 0.5
    p = math.fabs(euclid_dist - route_dist) * -beta
    return p


def path_forward(src_pt, dst_pt, line, seq):
    dist0 = calc_point_dist(src_pt, line.point_list[seq])
    dist1 = calc_point_dist(dst_pt, line.point_list[seq])
    return dist0 < dist1


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
    if in_hz(lng, lat):  # 判断是否在国内
        return lng, lat
    dlat = transformlat(lng - 105.0, lat - 35.0)
    dlng = transformlng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * pi
    magic = math.sin(radlat)
    magic = 1 - ee * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((earth_a * (1 - ee)) / (magic * sqrtmagic) * pi)
    dlng = (dlng * 180.0) / (earth_a / sqrtmagic * math.cos(radlat) * pi)
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
    dlat = (dlat * 180.0) / ((earth_a * (1 - ee)) / (magic * sqrtmagic) * pi)
    dlng = (dlng * 180.0) / (earth_a / sqrtmagic * math.cos(radlat) * pi)
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
