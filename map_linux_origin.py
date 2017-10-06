import utm
import numpy as np
from sklearn.cluster import KMeans
import endpoint
import math
import os
import plotly.plotly as py
import plotly
from plotly.graph_objs import *
import json
import datetime
import parser
import argparse


def make_map(pcmap,is_circle,width,max_vel_str,max_vel_cur,visible):
    if os.path.exists('test.txt') is False:
        os.rename(pcmap, 'test.txt')
    # all_data=np.loadtxt('pcmap.txt')
    all_data = []
    all_utm = []
    all_utm_time = []
    all_utm_time_walk = []

    with open('test.txt', 'r') as f:
        for line in f:
            every_line = list(map(float, line.split(',')))
            if np.size(every_line) == 1:
                pass
            else:
                all_data.append(every_line)
        all_data = np.array(all_data)
        longi = all_data[:, 0]
        lati = all_data[:, 1]
        time = all_data[:, 5]
        walking_speed = 6
        # step0 read original log and delete repetition
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
                u_time_walk = [u[0] * walking_speed, u[1] * walking_speed, time[i]]
                all_utm_time.append(u_time)
                all_utm_time_walk.append(u_time_walk)
        all_utm_time = np.array(all_utm_time)
        all_utm_time_walk = np.array(all_utm_time_walk)
        # step1 Clusting by distance and time
        n_clusters = len(longi) // 20
        kmeans = KMeans(n_clusters, random_state=0).fit_predict(all_utm_time_walk)
        # np.savetxt('class.txt',kmeans)
        # plt.scatter(all_utm[:,0],all_utm[:,1],c=kmeans)
        # plt.show()

        # step2 sort all points by time order
        all_point = []
        all_origin = []
        # all_utm_time=np.array(all_utm_time)
        for i in range(n_clusters):
            class_index = np.array(kmeans)
            same_class_index = np.where(class_index == i)
            same_class = all_utm_time[list(same_class_index[0])]
            if i == 0 or i == n_clusters - 1:
                origin_point, destination_point = endpoint.find_endpoint_for_head_tail(same_class)
            else:
                origin_point, destination_point = endpoint.find_endpoint(same_class)
            all_point.append([origin_point, destination_point])
            all_origin.append(origin_point)

        all_origin = np.array(all_origin)
        origin = all_origin[0]
        all_point = np.array(all_point)
        # print(all_point)
        arg = np.argsort(all_origin[:, 2])
        # print(arg)
        all_point_final = all_point[list(arg)]
        destination = all_point_final[-1][1]
        # print(all_point_final)
        # l=len(all_point)
        # all_point=np.array(all_point)
        # all_point=all_point.resize(l,2)
        # plt.scatter(all_point[0],all_point[1])

        # step3 Concat straight line and short segment that length is less than 0.5m
        while True:
            slope = endpoint.calculate_slope(all_point_final)
            after_concat = endpoint.concat_stright(slope, all_point_final)
            if after_concat == all_point_final:
                break
            else:
                all_point_final = after_concat
        key_jw, X, Y = endpoint.utm2jw(all_point_final, zone_number, zone_letter)

        # step4 insert points in long stright line
        while True:
            complete_point = endpoint.insert_for_long(all_point_final)
            if all_point_final == complete_point:
                break
            else:
                all_point_final = complete_point
        complete_point = np.array(complete_point)

        jw, no_use_x, no_use_y = endpoint.utm2jw(complete_point, zone_number, zone_letter)
        new_jw = np.array(jw)
        lati = new_jw[:, 0]
        longi = new_jw[:, 1]
        # print(jw)
        longi_str = [str(l) for l in longi]
        lati_str = [str(t) for t in lati]

        # step5 display all the key points
        if visible==1:
            mapbox_access_token = 'pk.eyJ1IjoidGp6eGgiLCJhIjoiY2o2cTUxN2hlMDZ6eTMycWpmNGJ6bTVrcSJ9.7nt0siqLHX2uaHsOVNF-fA'
            plotly.tools.set_credentials_file(username='tjzxh', api_key='Faxs8vPpdsiAqtoMO2Zt')

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
        hmap = {"debug_info": {"lat_bias": 0, "lng_bias": 0}, "is_coordinate_gps": 1, "lane_switch_set": [],
                "node_set": [], "segment_set": []}
        # step6-1 node_set
        for i in range(len(lati)):
            node_lat = lati[i]
            node_lng = longi[i]
            node = {"gps_weight": 1, "id": i, "lat": node_lat, "lng": node_lng, "lslam_carto_weight": 0, "name": str(i),
                    "qrcode_weight": 0, "radius": 0, "type": 17, "vslam_weight": 0, "z": 0}
            hmap["node_set"].append(node)
        # step6-2 segment_set
        id = 0
        for j in range(0, len(key_jw) - 2, 2):
            point0_xy = [X[j], Y[j]]
            point1_xy = [X[j + 2], Y[j + 2]]
            dis = endpoint.distance(point0_xy, point1_xy)
            if dis < 5:
                vel = max_vel_cur
            else:
                vel = max_vel_str
            point0 = key_jw[j]
            point1 = key_jw[j + 2]
            index0 = jw.index(point0)
            index1 = jw.index(point1)
            segment = {"id": id, "lane_list": [
                {"id": 0, "lane_width": width, "left_line_type": 1, "max_vel": vel, "name": "Path" + str(id),
                 "node_list": [index0, index1], "right_line_type": 1, "seg_id": id}],
                       "name": "seg" + str(id)}
            id += 1
            hmap["segment_set"].append(segment)

        last_two_point = key_jw[-2]
        last_two_id = jw.index(last_two_point)
        odd_segment = {"id": (len(key_jw) - 1) // 2, "lane_list": [
            {"id": 0, "lane_width": width, "left_line_type": 1, "max_vel": max_vel_str,
             "name": "Path" + str((len(key_jw) - 1) // 2), "node_list": [last_two_id, len(jw)-1],
             "right_line_type": 1, "seg_id": (len(key_jw) - 1) // 2}], "name": "seg" + str((len(key_jw) - 1) // 2)}
        hmap["segment_set"].append(odd_segment)
        # step6-5 if the route is a circle,add a new segment
        min_index = 0
        if is_circle == 1:
            op = [X[0], Y[0]]
            min_dis = 100
            min_point = []
            for j in range(len(key_jw) - 1):
                X.reverse()
                Y.reverse()
                other_point = [X[j], Y[j]]
                dis = endpoint.distance(op, other_point)
                if dis < min_dis:
                    min_dis = dis
                    min_point = key_jw[j + 1]
                min_index = jw.index(min_point)
            last_segment = {"id": len(jw) - 1, "lane_list": [
                {"id": 0, "lane_width": width, "left_line_type": 1, "max_vel": 8, "name": "Path" + str(len(jw) - 1),
                 "node_list": [len(jw) - (min_index + 1), 0], "right_line_type": 1, "seg_id": len(jw) - 1}],
                            "name": "seg" + str(len(jw) - 1)}
            hmap["segment_set"].append(last_segment)
        # step6-4 dump json file
        with open('test.hmap', 'w') as f1:
            json.dump(hmap, f1)
        # step7 write json file for rmap
        if is_circle == 1:
            rmap = {"name": "test", "roadmap": "data/test.hmap", "hmap_routes": [
                {"is_circle": is_circle, "name": "first",
                 "route_key_nodes": [{"id": 0, "is_stop": 1, "is_stop_enabled": 0},
                                     {"id": len(jw) - (min_index + 1), "is_stop": 1, "is_stop_enabled": 0}]}]}
        else:

            rmap = {"name": "test", "roadmap": "data/test.hmap",
                    "hmap_routes": [{"is_circle": is_circle, "name": "first",
                                     "route_key_nodes": [
                                         {"id": 0, "is_stop": 1,
                                          "is_stop_enabled": 0},
                                         {"id": len(jw) - 1,
                                          "is_stop": 1,
                                          "is_stop_enabled": 0}]}]}
        with open('test.rmap', 'w') as f2:
            json.dump(rmap, f2)













