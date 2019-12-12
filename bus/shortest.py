# -*- coding: utf-8 -*-
# @Time    : 2019/11/14 11:34
# @Author  : yhdu@tongwoo.cn
# @简介    : 
# @File    : shortest.py


from map_info.readMap import MapInfo
import matplotlib.pyplot as plt


def draw_line(line):
    x_list, y_list = [], []
    for pt in line.point_list:
        x, y = pt.x, pt.y
        x_list.append(x)
        y_list.append(y)
    plt.plot(x_list, y_list, color='k')


def main():
    mi = MapInfo('../map_info/hz3.db')
    for line in mi.line_list:
        draw_line(line)
    plt.show()


if __name__ == '__main__':
    main()
