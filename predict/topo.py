# -*- coding: utf-8 -*-
# @Time    : 2019/10/29 17:06
# @Author  : yhdu@tongwoo.cn
# @简介    : 
# @File    : topo.py


from map_info.readMap import MapInfo


def main():
    mi = MapInfo("../map_info/hz3.db")
    ln_list, pt_list = mi.line_list, mi.point_list
    rmap = mi.reverse_map
    a = rmap[2708]
    pass


if __name__ == "__main__":
    main()
