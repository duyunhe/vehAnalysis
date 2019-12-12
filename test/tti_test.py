# -*- coding: utf-8 -*-
# @Time    : 2019/10/24 10:14
# @Author  : yhdu@tongwoo.cn
# @简介    : 
# @File    : tti_test.py


import numpy as np
import matplotlib.pyplot as plt


def main():
    y = np.array([0, 2, 4, 6, 8, 10])
    x = np.array([1, 1.3, 1.6, 2.1, 2.7, 3.6])
    f1 = np.polyfit(x, y, 3)
    p1 = np.poly1d(f1)
    x0 = np.arange(1, 4, 0.01)
    print p1
    yvals = np.polyval(f1, x0)
    plot1 = plt.plot(x, y, 's', label='original values')
    plot2 = plt.plot(x0, yvals, 'r', label='polyfit values')
    plt.xlabel('x')
    plt.ylabel('y')
    plt.show()


if __name__ == '__main__':
    main()
