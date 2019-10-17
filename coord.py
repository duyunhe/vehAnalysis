# -*- coding: utf-8 -*-
# @Time    : 2019/6/28 10:28
# @Author  : yhdu@tongwoo.cn
# @简介    : 
# @File    : coord.py


from math import sin, cos, sqrt, pi, atan, fabs, tan


class BLH:
    def __init__(self, b=.0, l=.0, h=.0):
        self.b, self.l, self.h = b, l, h


class XYZ:
    def __init__(self, x=.0, y=.0, z=0.0):
        self.x, self.y, self.z = x, y, z


class xyH:
    def __init__(self, x=.0, y=.0, h = .0):
        self.x, self.y, self.h = x, y, h


class Ellipsoid:
    def __init__(self, name="", a=0.0, r=0.0):
        self.name, self.a, self.r = name, a, r


class Param7:
    def __init__(self):
        self.dx, self.dy, self.dz, self.rx, self.ry, self.rz, self.k = 0, 0, 0, 0, 0, 0, 0


class Param4:
    def __init__(self, dx=.0, dy=.0, r=.0, k=.0):
        self.dx, self.dy, self.r, self.k = dx, dy, r, k


WGS84 = Ellipsoid("WGS84", 6378137, 1.0 / 298.257223563)
BJ54 = Ellipsoid("北京54", 6378245, 1.0 / 298.3)
LIMIT = tan(0.0001 * pi / (3600 * 180))
MAX_ITER = 100000


def BLH2XYZ(src, dest, ellipsoid):
    """
    :param src: BLH 
    :param dest: XYZ to calc
    :param ellipsoid: Ellipsoid 
    :return: 
    """
    e = 2.0 * ellipsoid.r - ellipsoid.r ** 2
    n = ellipsoid.a / sqrt(1.0 - e * pow(sin(src.b * pi / 180.0), 2))
    dest.x = (n + src.h) * cos(src.b * pi / 180.0)
    dest.y = dest.x * sin(src.l * pi / 180.0)
    dest.x *= cos(src.l * pi / 180.0)
    dest.z = (n * (1 - e) + src.h) * sin(src.b * pi / 180.0)


def XYZ2BLH(src, dest, ellipsoid):
    """
    :param src: XYZ 
    :param dest: BLH
    :param ellipsoid: Ellipsoid 
    :return: 
    """
    e = 2.0 * ellipsoid.r - 1.0 * ellipsoid.r ** 2
    n = ellipsoid.a / sqrt(1 - e * sin(src.x) ** 2)
    m = sqrt(src.x ** 2 + src.y ** 2)
    dest.l = atan(src.y / src.x)
    if dest.l < 0:
        dest.l += pi
    _e = e / (1 - e)
    ce = ellipsoid.a * sqrt(1 + _e) * e
    k = 1 + _e
    front = src.z / m
    temp = front
    count = 0

    while True:
        front = temp
        temp = src.z / m + ce * front / (m * sqrt(k + front ** 2))
        count += 1
        if fabs(temp - front) <= LIMIT or count >= MAX_ITER:
            break

    dest.b = atan(temp)
    if dest.b < 0:
        dest.b += pi
    n = ellipsoid.a / sqrt(1 - e * (sin(dest.b) ** 2))
    dest.h = m / cos(dest.b) - n
    dest.b = dest.b * 180.0 / pi
    dest.l = dest.l * 180.0 / pi


def xyHTrans(src, dest, param):
    """
    :param src: xyH 
    :param dest: xyH
    :param param: Param4
    :return: dest
    """
    dest.x = param.dx + param.k * (cos(param.r) * src.x - sin(param.r) * src.y)
    dest.y = param.dy + param.k * (sin(param.r) * src.x + cos(param.r) * src.y)
    dest.h = src.h


def BLH2xyH(src, dest, ellipsoid, zone_wide, center_longti):
    """
    :param src: BLH
    :param dest: xyH
    :param ellipsoid: Ellipsoid
    :param zone_wide: int
    :param center_longti: float 
    :return: dest
    """
    ipi = pi / 180.0
    proj_no = int(src.l / zone_wide)
    longitude1 = float(proj_no * zone_wide)
    if zone_wide == 6:
        longitude1 += zone_wide / 2
    if center_longti != 0.0:
        longitude0 = center_longti
    else:
        longitude0 = 120.0
    longitude0, latitude0 = longitude0 * ipi, 0
    longitude1, latitude1 = src.l * ipi, src.b * ipi
    e2 = 2 * ellipsoid.r - ellipsoid.r ** 2
    ee = e2 * (1.0 - e2)
    NN = ellipsoid.a / sqrt(1.0 - e2 * sin(latitude1) * sin(latitude1))
    T = tan(latitude1) ** 2
    C = ee * (cos(latitude1) ** 2)
    A = (longitude1 - longitude0) * cos(latitude1)
    M = ellipsoid.a * ((1-e2/4-3*e2*e2/64-5*e2*e2*e2/256)*latitude1-(3*e2/8+3*e2*e2/32+45*e2*e2*e2/1024)
                       * sin(2*latitude1)+(15*e2*e2/256+45*e2*e2*e2/1024)*sin(4*latitude1)-(35*e2*e2*e2/3072)
                       * sin(6*latitude1))
    yval = NN*(A+(1-T+C)*A*A*A/6+(5-18*T+T*T+72*C-58*ee)*A*A*A*A*A/120)
    xval = M+NN*tan(latitude1)*(A*A/2+(5-T+9*C+4*C*C)*A*A*A*A/24+(61-58*T+T*T+600*C-330*ee)*A*A*A*A*A*A/720)
    x0, y0 = 0, 500000
    xval += x0
    yval += y0
    dest.x, dest.y, dest.h = xval, yval, src.h


def xyH2BLH(src, dest, ellipsoid, zone_wide, center_longti):
    Y, X = src.x, src.y
    ipi = pi / 180.0
    proj_no = int(X / 1000000)
    longitude0 = (proj_no - 1) * zone_wide
    if zone_wide == 6:
        longitude0 += zone_wide / 2
    if center_longti != 0.0:
        longitude0 = center_longti
    longitude0 *= ipi

    x0, y0 = 500000, 0
    xval, yval = X - x0, Y - y0
    e2 = 2 * ellipsoid.r - ellipsoid.r ** 2
    e1 = (1.0 - sqrt(1 - e2)) / (1.0 + sqrt(1 - e2))
    ee = e2 / (1 - e2)
    M = yval
    u = M / (ellipsoid.a * (1 - e2 / 4 - 3 * e2 * e2 / 64 - 5 * e2 * e2 * e2 / 256))
    fai = u + (3 * e1 / 2 - 27 * e1 * e1 * e1 / 32) * sin(2 * u) + (21 * e1 * e1 / 16 - 55 * e1 * e1 * e1 * e1 / 32)\
          * sin(4 * u)+(151 * e1 * e1 * e1 / 96) * sin(6 * u) + (1097 * e1 * e1 * e1 * e1 / 512) * sin(8 * u)
    C = ee * cos(fai) * cos(fai)
    T = tan(fai) * tan(fai)
    NN = ellipsoid.a / sqrt(1.0 - e2 * sin(fai) * sin(fai))
    R = ellipsoid.a * (1 - e2) / sqrt((1 - e2 * sin(fai) * sin(fai)) * (1 - e2 * sin(fai) * sin(fai))
                                      * (1 - e2 * sin(fai) * sin(fai)))
    D = xval / NN
    longitude1 = longitude0 + (D - (1 + 2 * T + C) * D * D * D / 6 + (
                    5 - 2 * C + 28 * T - 3 * C * C + 8 * ee + 24 * T * T) * D * D * D * D * D / 120) / cos(fai)
    latitude1 = fai - (NN * tan(fai) / R) * (
                    D * D / 2 - (5 + 3 * T + 10 * C - 4 * C * C - 9 * ee) * D * D * D * D / 24 + (
                        61 + 90 * T + 298 * C + 45 * T * T - 256 * ee - 3 * C * C) * D * D * D * D * D * D / 720)

    dest.l, dest.b, dest.h = longitude1 / ipi, latitude1 / ipi, src.h


def WGS84_BLH_2_HZ_xyH(src, dest):
    """
    :param src: BLH 
    :param dest: xyH
    :return: 
    """
    wgsXYZ = XYZ()
    bjBLH = BLH()
    bjxyH = xyH()
    p4 = Param4(-3267260.681433, -439368.775424, 0.0011552983, 1.000127233286)

    BLH2XYZ(src, wgsXYZ, WGS84)
    XYZ2BLH(wgsXYZ, bjBLH, BJ54)
    BLH2xyH(bjBLH, bjxyH, BJ54, 3, 120.0)
    xyHTrans(bjxyH, dest, p4)


def HZ_xyH_2_WGS84_BLH(src, dest):
    wgsXYZ = XYZ()
    bjBLH = BLH()
    bjxyH = xyH()
    p4 = Param4(3267350.405956, 435538.425307, -0.0011552983, 0.999872559078)

    xyHTrans(src, bjxyH, p4)
    xyH2BLH(bjxyH, bjBLH, BJ54, 3, 120.0)
    BLH2XYZ(bjBLH, wgsXYZ, BJ54)
    XYZ2BLH(wgsXYZ, dest, WGS84)


def bl2xy(b, l):
    blh, xyh = BLH(b, l), xyH()
    WGS84_BLH_2_HZ_xyH(blh, xyh)
    return xyh.y, xyh.x


def xy2bl(x, y):
    blh, xyh = BLH(), xyH(y, x)
    HZ_xyH_2_WGS84_BLH(xyh, blh)
    return blh.b, blh.l
