import utm
import numpy as np
from sklearn.cluster import *
from scipy.stats import mode
import endpoint
import math
import os
# import plotly.plotly as py
# import plotly
# from plotly.graph_objs import *
import json
import datetime
import matplotlib.pyplot as plt
import parser
import argparse
import re
from mpl_toolkits.mplot3d import axes3d
from matplotlib import cm
import matplotlib.pyplot as plt
from rdp import rdp
from prettytable import PrettyTable
import csv


def seg(pcmap, vslam, gps, autovel, is_local):
    # try:
    if os.path.exists(pcmap) is False:
        print("We can't find the file")
        return False
    else:
        pass
    pcmap_flag = 1
    all_data = []
    all_utm = []
    all_utm_time = []
    all_utm_time_walk = []

    with open(pcmap, 'r') as f:
        for line in f:
            line = line.strip('\n')
            every_line = list(map(float, re.split('[, ]', line)))
            if np.size(every_line) == 1:
                pcmap_flag = every_line[0]
            else:
                all_data.append(every_line)
        # Judge again for pcmap flag
        if pcmap_flag == 0:
            gps = 0
        # Start:Get latitude,longitude,timestamp and height from all kinds of Data
        all_data = np.array(all_data)
        if vslam == 1:
            longi = all_data[:, 1]
            lati = all_data[:, 2]
            time = all_data[:, 0]
            height = all_data[:, 3]
            # elif pcmap_flag == 0:
            # longi = all_data[:, 0]
            # lati = all_data[:, 1]
            # time = list(range(len(longi)))
            # height = all_data[:, 2]
        else:
            longi = all_data[:, 0]
            lati = all_data[:, 1]
            height = all_data[:, 2]
            # time = list(range(len(longi)))
            time = all_data[:, 5]

        if vslam == 1:
            walking_speed = 4 / 66
        else:
            walking_speed = 5

        # step0 process original data

        # step0-0 read original log and delete repetition
        # Local Coordinate or GPS
        all_znum = []
        force = 0
        if gps == 0:
            for i in range(len(longi)):
                u = [longi[i], lati[i]]
                xyz = [u[0], u[1], height[i]]
                if xyz in all_utm:
                    all_utm.remove(xyz)
                else:
                    all_utm.append(xyz)
                    u_time = [u[0], u[1], height[i], time[i]]
                    u_time_walk = [u[0], u[1], height[i], time[i] * walking_speed]
                    # print(u_time_walk)
                    all_utm_time.append(u_time)
                    all_utm_time_walk.append(u_time_walk)
                    # print(all_utm_time_walk)
        else:
            # whether in the same zone
            for h in range(len(longi)):
                unit = utm.from_latlon(lati[h], longi[h])
                zone_number = unit[2]
                all_znum.append(zone_number)
            if all_znum == [all_znum[0]] * len(all_znum):
                force = 0
            else:
                force = mode(all_znum)
            for i in range(len(longi)):
                if force == 0:
                    u = utm.from_latlon(lati[i], longi[i])
                else:
                    u = utm.from_latlon(lati[i], longi[i], force_zone_number=force)
                u = list(u)
                all_utm.append(u[0:2])
                if u in all_utm:
                    all_utm.remove(u)
                else:
                    u_time = [u[0], u[1], height[i], time[i], longi[i], lati[i]]
                    u_time_walk = [u[0], u[1], height[i], time[i] * walking_speed]
                    all_utm_time.append(u_time)
                    all_utm_time_walk.append(u_time_walk)
        all_utm_time0 = np.array(all_utm_time)
        all_utm_time_walk0 = np.array(all_utm_time_walk)
        arg0 = np.argsort(all_utm_time0[:, 3])
        all_utm_time = all_utm_time0[list(arg0)]
        arg1 = np.argsort(all_utm_time_walk0[:, 3])
        all_utm_time_walk = all_utm_time_walk0[list(arg1)]

        # step0-1 calculate the vel of every point
        # With or Without vel
        if autovel == 0:
            new_all_utm_vel = all_utm_time
        else:
            all_point_for_vel = all_utm_time.T
            dif = np.diff(all_point_for_vel)
            all_vel = []
            for s in range(0, len(dif[0])):
                if dif[3][s] < 0.001:
                    vel_of_point = 3
                else:
                    vel_of_point = 3.6 * math.sqrt(
                        math.pow(dif[0][s], 2) + math.pow(dif[1][s], 2) + math.pow(dif[2][s], 2)) / dif[3][s]
                if vel_of_point < 3:
                    vel_of_point = 3
                if vel_of_point > 40:
                    vel_of_point = 40
                all_vel.append(vel_of_point)

            all_vel = list(filter(None, all_vel))
            all_vel = np.array(all_vel)
            N = 20
            weights = np.ones(N) / N
            s = np.convolve(weights, all_vel)[N - 1:-N + 1]

            all_utm_vel = list(all_utm_time)
            new_all_utm_vel = []
            for d in range(len(all_utm_vel)):
                new_d = list(all_utm_vel[d])
                if d >= len(s) - 1:
                    new_d.append(np.max(s))
                elif d == 0:
                    new_d.append(np.max(s))
                else:
                    new_d.append(s[d])
                new_all_utm_vel.append(new_d)

            new_all_utm_vel = np.array(new_all_utm_vel)

        all_pure_utm = all_utm_time[:, :3]
        # step1 extract key point
        # step1-0 few points can be processed directly
        if len(new_all_utm_vel) <= 100:
            mask = rdp(all_pure_utm, epsilon=0.02, algo="iter", return_mask=True)
            all_point_final = new_all_utm_vel[mask]
        else:
            # step1-1 Clusting by distance and time
            point_num = 100
            n_clusters = len(longi) // point_num
            kmeans = MiniBatchKMeans(n_clusters, init_size=n_clusters, random_state=1).fit(all_utm_time_walk)
            labels = kmeans.labels_

            # step2 sort all points by time order
            all_point = []
            for i in range(n_clusters):
                class_index = labels
                same_class_index = np.where(class_index == i)
                # all_utm_time_walk is for cluster and the useful one is new_all_utm_vel
                same_class_utm = all_pure_utm[list(same_class_index[0])]
                same_class = new_all_utm_vel[list(same_class_index[0])]
                mask4class = rdp(same_class_utm, epsilon=0.02, algo="iter", return_mask=True)
                keypoint4class = same_class[mask4class]
                if all_point == []:
                    all_point = keypoint4class
                else:
                    all_point = np.vstack((all_point, keypoint4class))
            arg = np.argsort(all_point[:, 3])
            all_point_final = all_point[list(arg)]

        # step3 delete the latter point in every short segment that length is less than 0.5m
        all_point_final = endpoint.delete_near_point(all_point_final, 0.5)
        all_point_final = np.array(all_point_final)
        all_point_final = endpoint.delete_near_point(all_point_final, 0.5)
        all_point_final = np.array(all_point_final)
        point4all = all_point_final
        # Local cooridinate or GPS With or Without vel(2*2)
        vel_for_point = []
        lati = []
        longi = []
        height = []
        all_x = []
        all_y = []
        jw = []
        if gps == 0 and autovel == 0:
            for i in all_point_final:
                longi.append(i[0])
                lati.append(i[1])
                height.append(i[2])
                all_x.append(i[0])
                all_y.append(i[1])
                jw.append([i[0], i[1]])
        elif gps == 0 and autovel == 1:
            for i in all_point_final:
                longi.append(i[0])
                lati.append(i[1])
                height.append(i[2])
                all_x.append(i[0])
                all_y.append(i[1])
                jw.append([i[0], i[1]])
            vel_for_point = all_point_final[:, -1]
        elif gps == 1 and autovel == 0:
            lati = list(all_point_final[:, -2])
            longi = list(all_point_final[:, -3])
            all_x = all_point_final[:, 0].tolist()
            all_y = all_point_final[:, 1].tolist()
            height = list(all_point_final[:, 2])
            jw = all_point_final[:, -2:].tolist()
        elif gps == 1 and autovel == 1:
            lati = list(all_point_final[:, -2])
            longi = list(all_point_final[:, -3])
            all_x = all_point_final[:, 0].tolist()
            all_y = all_point_final[:, 1].tolist()
            height = list(all_point_final[:, 2])
            vel_for_point = all_point_final[:, -1]
            jw = all_point_final[:, -2:].tolist()
        # step4 Concat straight line
        # num = 0
        while True:
            slope = endpoint.calculate_slope(all_point_final)
            after_concat = endpoint.concat_stright(slope, all_point_final)
            after_concat = list(after_concat)
            all_point_final = list(all_point_final)
            if after_concat == all_point_final or abs(len(after_concat) - len(all_point_final)) == 1:
                break
            else:
                all_point_final = after_concat
        point4key = all_point_final
        # Local Coordinate or GPS
        X = []
        Y = []
        key_jw = []
        if gps == 0 or is_local == 1:
            for i in all_point_final:
                X.append(i[0])
                Y.append(i[1])
                key_jw.append([i[0], i[1]])
        else:
            final_point = np.array(all_point_final)
            key_jw = final_point[:, -2:].tolist()
            X = list(final_point[:, 0])
            Y = list(final_point[:, 1])

        # Count the number of points between key points
        all_point_num = []
        for j in range(0, len(key_jw) - 1):
            point0 = key_jw[j]
            point1 = key_jw[j + 1]
            index0 = jw.index(point0)
            index1 = jw.index(point1)
            point_num = index1 - index0
            all_point_num.append(point_num)
        # Find the stright line which number of points is lager than 2 and distance is larger than 10m
        all_str_id = [k for k in range(len(all_point_num)) if all_point_num[k] > 1]
        real_str_id = []
        for h in range(len(all_str_id)):
            key_id0 = all_str_id[h]
            key_id1 = all_str_id[h] + 1
            if key_id1 > len(jw) - 1:
                break
            else:
                str_dis = endpoint.distance([X[key_id0], Y[key_id0]], [X[key_id1], Y[key_id1]])
                if str_dis >= 5:
                    real_str_id.append(all_str_id[h])
    return force, vel_for_point, lati, longi, height, all_x, all_y, jw, X, Y, key_jw, real_str_id, point4all, point4key
