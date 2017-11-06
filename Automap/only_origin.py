import utm
import numpy as np
from sklearn.cluster import *
import endpoint
import math
import os
import plotly.plotly as py
import plotly
from plotly.graph_objs import *
import json
import datetime
import matplotlib.pyplot as plt
import parser
import argparse
import re

def make_map(pcmap, is_circle, width, max_vel_str, max_vel_cur, visible, name, vslam):
    if os.path.exists(pcmap) is False:
        print("We can't find the file")
        return False
    else:
        pass
    #elif pcmap[-1] == 't' and pcmap[-2] == 'x' and pcmap[-3] == 't':
        #pass
    #elif pcmap[-1] == 'p' and pcmap[-2] == 'a' and pcmap[-3] == 'm' and pcmap[-4] == 'c' and pcmap[-5] == 'p':
        #pass
    #else:
        #os.rename(pcmap, pcmap+'.txt')
    # all_data=np.loadtxt('pcmap.txt')
    all_data = []
    all_utm = []
    all_utm_time = []
    all_utm_time_walk = []

    with open(pcmap, 'r') as f:
        for line in f:
            line = line.strip('\n')
            every_line = list(map(float, re.split('[, ]',line)))
            if np.size(every_line) == 1:
                pass
            else:
                all_data.append(every_line)
        all_data = np.array(all_data)
        if vslam == 1:
            longi = all_data[:, 1]
            lati = all_data[:, 2]
            time = all_data[:, 0]
        else:
            longi = all_data[:, 0]
            lati = all_data[:, 1]
            time = all_data[:, 5]

        if vslam == 1:
            walking_speed = 4/66
        else:
            walking_speed = 5

        # step0-0 read original log and delete repetition
        if vslam == 1:
            for i in range(len(longi)):
                u = [lati[i], longi[i]]

                if u in all_utm:
                    all_utm.remove(u)
                else:
                    all_utm.append(u)
                    u_time = [u[0], u[1], time[i]]
                    u_time_walk = [u[0], u[1], time[i] * walking_speed]
                    #print(u_time_walk)
                    all_utm_time.append(u_time)
                    all_utm_time_walk.append(u_time_walk)
            #print(all_utm_time_walk)
        else:
            for i in range(len(longi)):
                u = utm.from_latlon(lati[i], longi[i])
                u = list(u)
                zone_number = u[2]
                zone_letter = u[3]
                all_utm.append(u[0:2])
                if u in all_utm:
                    all_utm.remove(u)
                else:
                    u_time = [u[0], u[1], time[i]]
                    u_time_walk = [u[0], u[1], time[i] * walking_speed]
                    all_utm_time.append(u_time)
                    all_utm_time_walk.append(u_time_walk)
        all_utm_time = np.array(all_utm_time)
        all_utm_time_walk = np.array(all_utm_time_walk)

        # step0-1 calculate the vel of every point
        if vslam == 1:
            new_all_utm_vel = all_utm_time
        else:
            all_point_for_vel = all_utm_time.T
            dif = np.diff(all_point_for_vel)
            all_vel = []
            for s in range(0, len(dif[0])):
                if dif[2][s] < 0.001:
                    vel_of_point = 3
                else:
                    vel_of_point = 3.6 * math.sqrt(math.pow(dif[0][s], 2) + math.pow(dif[1][s], 2)) / dif[2][s]
                if vel_of_point < 3:
                    vel_of_point = 3
                all_vel.append(vel_of_point)
                # print(np.max(all_vel),np.mean(all_vel),np.median(all_vel))

                # plt.plot(range(len(all_vel)),all_vel)
                # plt.show()
            all_vel = list(filter(None, all_vel))
            all_vel = np.array(all_vel)
            N = 20
            weights = np.ones(N) / N
            s = np.convolve(weights, all_vel)[N - 1:-N + 1]
            # t = np.arange(N - 1, len(all_vel))
            # plt.plot(t, all_vel[N - 1:], lw=1)
            # plt.plot(t, s, lw=2)
            # plt.show()
            # print(np.max(s),len(s))

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

        # step1 Clusting by distance and time
        if vslam == 1:
            point_num = 10
        else:
            point_num = 20
        n_clusters = len(longi) // point_num
        kmeans = MiniBatchKMeans(n_clusters, init_size=n_clusters).fit(all_utm_time_walk)
        labels = kmeans.labels_
        # np.savetxt('class.txt',kmeans)
        #plt.scatter(lati,longi,c=labels)


        # step2 sort all points by time order
        all_point = []
        all_origin = []
        all_des = []
        # all_utm_time=np.array(all_utm_time)
        for i in range(n_clusters):
            class_index = labels
            same_class_index = np.where(class_index == i)
            same_class = new_all_utm_vel[list(same_class_index[0])]
            if i == 0 or i == n_clusters - 1:
                origin_point, destination_point = endpoint.find_endpoint_for_head_tail(same_class)
            else:
                origin_point, destination_point = endpoint.find_endpoint(same_class)
            # all_point.append([origin_point, destination_point])
            if origin_point != [] and destination_point != []:
                all_origin.append(origin_point)
                all_des.append(destination_point)

        des_point = all_des[-1]
        all_origin.append(des_point)
        all_point = all_origin
        all_point = np.array(all_point)
        all_origin = np.array(all_origin)
        # print(all_point)
        arg = np.argsort(all_origin[:, 2])
        # print(arg)
        all_point_final = all_point[list(arg)]

        # print(all_point_final)
        # l=len(all_point)
        # all_point=np.array(all_point)
        # all_point=all_point.resize(l,2)
        # plt.scatter(all_point[0],all_point[1])


        # step3 delete the latter point in every short segment that length is less than 0.5m
        all_point_final = endpoint.delete_near_point(all_point_final, 0.5)
        all_point_final = np.array(all_point_final)
        all_point_final = endpoint.delete_near_point(all_point_final, 0.5)
        all_point_final = np.array(all_point_final)

        if vslam == 1:
            lati = []
            longi = []
            all_x = []
            all_y = []
            jw = []
            for i in all_point_final:
                lati.append(i[0])
                longi.append(i[1])
                all_x.append(i[0])
                all_y.append(i[1])
                jw.append([i[0], i[1]])
        else:
            jw, all_x, all_y = endpoint.utm2jw(all_point_final, zone_number, zone_letter)
            new_jw = np.array(jw)
            lati = new_jw[:, 0]
            longi = new_jw[:, 1]
            vel_for_point = all_point_final[:, 3]
        # step4 Concat straight line
        while True:
            slope = endpoint.calculate_slope(all_point_final)
            after_concat = endpoint.concat_stright(slope, all_point_final)
            after_concat = list(after_concat)
            all_point_final = list(all_point_final)
            if after_concat == all_point_final:
                break
            else:
                all_point_final = after_concat

        if vslam == 1:
            X = []
            Y = []
            key_jw = []
            for i in all_point_final:
                X.append(i[0])
                Y.append(i[1])
                key_jw.append([i[0], i[1]])
        else:
            key_jw, X, Y = endpoint.utm2jw(all_point_final, zone_number, zone_letter)

        # print(jw)
        longi_str = [str(l) for l in longi]
        lati_str = [str(t) for t in lati]

        # step5 display all the key points in map
        #if vslam == 1:
        
        if visible == 1:
            mapbox_access_token = 'pk.eyJ1IjoidGp6eGgiLCJhIjoiY2o2cTUxN2hlMDZ6eTMycWpmNGJ6bTVrcSJ9.7nt0siqLHX2uaHsOVNF-fA'
            plotly.tools.set_credentials_file(username='tjzxh', api_key='jXpff779zQJ6PKzFkamR')

            data = Data([
                Scattermapbox(
                    lat=lati_str,
                    lon=longi_str,
                    mode='markers',
                    marker=Marker(
                        size=9
                    ),
                    text=[],
                )
            ])
            layout = Layout(
                autosize=True,
                hovermode='closest',
                mapbox=dict(
                    accesstoken=mapbox_access_token,
                    bearing=0,
                    center=dict(
                        lat=lati_str[len(lati) // 2],
                        lon=longi_str[len(lati) // 2]
                    ),
                    pitch=0,
                    zoom=50
                ),
            )

            fig = dict(data=data, layout=layout)
            py.plot(fig, filename='Multiple Mapbox' + str(datetime.datetime.now()))

        # step6 write a json file for hmap
        if vslam == 1:
            is_coordinate_gps = 0
        else:
            is_coordinate_gps = 1
        hmap = {"debug_info": {"lat_bias": 0, "lng_bias": 0}, "is_coordinate_gps": is_coordinate_gps,
                "lane_switch_set": [],
                "node_set": [], "segment_set": []}
        # step6-1 node_set
        if vslam == 1:
            for i in range(len(lati)):
                node_lat = lati[i]
                node_lng = longi[i]
                node = {"gps_weight": 0, "id": i, "lat": node_lat, "lng": node_lng, "lslam_carto_weight": 0,
                        "name": str(i),
                        "qrcode_weight": 0, "radius": 0, "type": 17, "vslam_weight": 1, "z": 0}
                hmap["node_set"].append(node)
        else:
            for i in range(len(lati)):
                node_lat = lati[i]
                node_lng = longi[i]
                node_vel = vel_for_point[i]
                node = {"gps_weight": 1, "id": i, "lat": node_lat, "lng": node_lng, "max_vel": node_vel,
                        "lslam_carto_weight": 0, "name": str(i),
                        "qrcode_weight": 0, "radius": 0, "type": 17, "vslam_weight": 0, "z": 0}
                hmap["node_set"].append(node)
        # step6-2 segment_set
        id = 0
        for j in range(0, len(key_jw) - 1):
            point0_xy = [X[j], Y[j]]
            point1_xy = [X[j + 1], Y[j + 1]]
            dis = endpoint.distance(point0_xy, point1_xy)
            if dis < 5:
                vel = max_vel_cur
            else:
                vel = max_vel_str
            point0 = key_jw[j]
            point1 = key_jw[j + 1]
            index0 = jw.index(point0)
            index1 = jw.index(point1)
            segment = {"id": id, "lane_list": [
                {"id": 0, "lane_width": width, "left_line_type": 1, "max_vel": vel, "name": "Path" + str(id),
                 "node_list": list(range(index0, index1 + 1)), "right_line_type": 1, "seg_id": id}],
                       "name": "seg" + str(id)}
            id += 1
            hmap["segment_set"].append(segment)

        # step6-3 if the route is a circle,add a new segment

        if is_circle == 1:
            op = [X[0], Y[0]]
            # 1 find the point that is the most nearest one from the origin
            min_dis = 100
            all_x.reverse()
            all_y.reverse()
            for k in range((len(jw) - 1) // 2):
                all_other_point = [all_x[k], all_y[k]]
                all_dis = endpoint.distance(op, all_other_point)
                if all_dis < min_dis and all_dis != 0:
                    min_dis = all_dis
                    basic = len(jw) - 1 - (k + 1)
            # 2 find the point that is the most nearest one from the step1
            for s in range(basic,0,-1):
                if jw[s] in key_jw:
                    near_index_segment = s
                    break
            rm_key = key_jw.index(jw[near_index_segment])
            for h in range(len(key_jw) - 2, rm_key - 1, -1):
                hmap["segment_set"].remove(hmap["segment_set"][h])
            # 3 if the basic and the near_index_segment are the same
            if basic == near_index_segment:
                last_segment = {"id": rm_key, "lane_list": [
                    {"id": 0, "lane_width": width, "left_line_type": 1, "max_vel": max_vel_cur,
                     "name": "Path" + str(rm_key),
                     "node_list": [basic, 0], "right_line_type": 1, "seg_id": rm_key}],
                                "name": "seg" + str(rm_key)}
            else:
                if endpoint.distance([all_x[near_index_segment],all_y[near_index_segment]],[all_x[basic],all_y[basic]]) < 5:
                    vel_sls = max_vel_cur
                else:
                    vel_sls = max_vel_str         
                second_last_segment = {"id": rm_key, "lane_list": [
                {"id": 0, "lane_width": width, "left_line_type": 1, "max_vel": vel_sls,
                 "name": "Path" + str(rm_key),
                 "node_list": list(range(near_index_segment, basic + 1)), "right_line_type": 1,
                 "seg_id": rm_key}],
                                   "name": "seg" + str(rm_key)}

                hmap["segment_set"].append(second_last_segment)

                last_segment = {"id": rm_key + 1, "lane_list": [
                    {"id": 0, "lane_width": width, "left_line_type": 1, "max_vel": max_vel_cur,
                     "name": "Path" + str(rm_key + 1),
                     "node_list": [basic, 0], "right_line_type": 1, "seg_id": rm_key + 1}],
                                "name": "seg" + str(rm_key + 1)}
             
            hmap["segment_set"].append(last_segment)

        # step6-4 dump json file
        with open(name + '.hmap', 'w') as f1:
            json.dump(hmap, f1, indent=4)

        # step7 write json file for rmap
        if is_circle == 1:
            rmap = {"name": "test", "roadmap": "data/" + name + ".hmap", "hmap_routes": [
                {"is_circle": 1, "name": "first",
                 "route_key_nodes": [{"id": 0, "is_stop": 1, "is_stop_enabled": 0},
                                     {"id": basic, "is_stop": 1, "is_stop_enabled": 0}]}]}
        else:

            rmap = {"name": "test", "roadmap": "data/" + name + ".hmap",
                    "hmap_routes": [{"is_circle": 0, "name": "first",
                                     "route_key_nodes": [
                                         {"id": 0, "is_stop": 1,
                                          "is_stop_enabled": 0},
                                         {"id": len(jw) - 1,
                                          "is_stop": 1,
                                          "is_stop_enabled": 0}]}]}
        with open(name + '.rmap', 'w') as f2:
            json.dump(rmap, f2, indent=4)

        # step8 display the road only
        plt.plot(lati,longi)
        plt.show()
