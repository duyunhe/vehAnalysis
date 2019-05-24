# vehAnalysis
路况分析

参考ACM GIS09 Hidden Markov Map Matching Through Noise and Sparseness一文。
HMM使用两个参数，代码和论文中计算选择略有不同

mapMatching.match_trace

参数trace, map_info，得到MatchRecord列表，记录下每个GPS点在道路路网上的匹配点（有多个），在模型下得到的最佳匹配点，以及前一个点到后一个点的路径


