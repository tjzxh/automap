import numpy as np
import endpoint
# import plotly.plotly as py
# import plotly
# from plotly.graph_objs import *
import json
import datetime
import matplotlib.pyplot as plt
from prettytable import PrettyTable
import csv
import segment


def make_map(pcmap, is_circle, width, max_vel_str, max_vel_cur, visible, name, vslam, gps, autovel, weight, is_local,
             path):
    # Export the trajectory to a csv file (including all points and key points)
    force, vel_for_point, lati, longi, height, all_x, all_y, jw, X, Y, key_jw, real_str_id, point4all, point4key = segment.seg(
        pcmap, vslam, gps, autovel, is_local)
    if path == 1:
        zero_mat = [0] * len(lati)
        half_mat = [0.5] * len(lati)
        one_mat = [1] * len(lati)
        width_list = [width] * len(lati)
        # convert jw to uos utm
        uos_x, uos_y = endpoint.jw2uos(lati, longi)
        x_array = np.array([uos_x])
        y_array = np.array([uos_y])
        height_array = np.array([height])
        zero_array = np.array([zero_mat])
        half_array = np.array([half_mat])
        one_array = np.array([one_mat])
        vel_array = np.array([vel_for_point])
        width_array = np.array([width_list])
        array4csv = np.concatenate((x_array, y_array, height_array, zero_array, zero_array, zero_array, one_array,
                                    one_array, half_array, half_array, zero_array, zero_array, vel_array,
                                    width_array,
                                    zero_array, zero_array), axis=0)
        array4csv = array4csv.T
        np.savetxt('test.csv', array4csv, delimiter=',')
    # step5 Judge the back off
    possible_backid = []
    possible_backvec = []
    for p in range(len(jw) - 2):
        vector1 = [all_x[p + 1] - all_x[p], all_y[p + 1] - all_y[p]]
        vector2 = [all_x[p + 2] - all_x[p + 1], all_y[p + 2] - all_y[p + 1]]
        back_cos = endpoint.vector_cos(vector1, vector2)
        if back_cos < 0:
            possible_backid.append(p + 1)
            possible_backvec.append([vector1, vector2])
    # Check the back off id
    for b in range(len(possible_backvec) - 2):
        if endpoint.vector_cos(possible_backvec[b][1], possible_backvec[b + 1][0]) > 0:
            pass
        else:
            possible_backid.remove(possible_backid[b + 1])
            possible_backid.remove(possible_backid[b])

    longi_str = [str(l) for l in longi]
    lati_str = [str(t) for t in lati]

    # step6 display all the key points in map
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

    # step7 Generate a json file for hmap
    if gps == 0 or is_local == 1:
        is_coordinate_gps = 0
    else:
        is_coordinate_gps = 1
    hmap = {"debug_info": {"lat_bias": 0, "lng_bias": 0}, "is_coordinate_gps": is_coordinate_gps,
            "lane_switch_set": [],
            "node_set": [], "segment_set": []}
    # step7-1 node_set
    # With or Without vel
    if autovel == 0:
        for i in range(len(lati)):
            node_lat = lati[i]
            node_lng = longi[i]
            node_hei = height[i]
            node = {"gps_weight": weight[0], "id": i, "lat": node_lat, "lng": node_lng,
                    "lslam_carto_weight": weight[3],
                    "name": str(i),
                    "qrcode_weight": weight[1], "radius": 0, "type": 17, "vslam_weight": weight[2],
                    "z": node_hei}
            hmap["node_set"].append(node)
    else:
        for i in range(len(lati)):
            node_lat = lati[i]
            node_lng = longi[i]
            node_hei = height[i]
            node_vel = vel_for_point[i]
            node = {"gps_weight": weight[0], "id": i, "lat": node_lat, "lng": node_lng, "max_vel": node_vel,
                    "lslam_carto_weight": weight[3], "name": str(i),
                    "qrcode_weight": weight[1], "radius": 0, "type": 17, "vslam_weight": weight[2],
                    "z": node_hei}
            hmap["node_set"].append(node)
    # step7-2 segment_set
    id = 0

    all_segment_id = []
    # With or Without vel
    if autovel == 0:
        vel_str = max_vel_str
        vel_cur = max_vel_cur
    else:
        vel_str = 40
        vel_cur = 40
    # Judge whether this a pure curve
    if len(real_str_id) == 0:
        all_segment_id.append(key_jw[0])
        all_segment_id.append(key_jw[-1])
        only_cur_segment = {"id": id, "lane_list": [
            {"id": 0, "lane_width": width, "left_line_type": 1, "max_vel": vel_cur,
             "name": "Path" + str(id),
             "node_list": list(range(0, len(jw))), "right_line_type": 1, "seg_id": id}],
                            "name": "seg" + str(id)}
        id += 1
        hmap["segment_set"].append(only_cur_segment)
    else:
        # Distinguish the stright and curve
        for p in range(len(real_str_id) - 1):
            first_id = jw.index(key_jw[real_str_id[p]])
            second_id = jw.index(key_jw[real_str_id[p] + 1])
            third_id = jw.index(key_jw[real_str_id[p + 1]])
            all_segment_id.append(first_id)
            if second_id == third_id:
                pass
            else:
                all_segment_id.append(second_id)
            # Generate the stright segment
            str_segment = {"id": id, "lane_list": [
                {"id": 0, "lane_width": width, "left_line_type": 1, "max_vel": vel_str, "name": "Path" + str(id),
                 "node_list": list(range(first_id, second_id + 1)), "right_line_type": 1, "seg_id": id}],
                           "name": "seg" + str(id)}
            id += 1
            hmap["segment_set"].append(str_segment)
            # Generate the curve segment if second id is not the same as third id
            if second_id == third_id:
                pass
            else:
                cur_segment = {"id": id, "lane_list": [
                    {"id": 0, "lane_width": width, "left_line_type": 1, "max_vel": vel_cur,
                     "name": "Path" + str(id),
                     "node_list": list(range(second_id, third_id + 1)), "right_line_type": 1, "seg_id": id}],
                               "name": "seg" + str(id)}
                id += 1
                hmap["segment_set"].append(cur_segment)

        # Append the first segment
        f_id = jw.index(key_jw[real_str_id[0]])
        if f_id == 0:
            pass
        else:
            # Generate the first curve segment
            first_cur_segment = {"id": id, "lane_list": [
                {"id": 0, "lane_width": width, "left_line_type": 1, "max_vel": vel_cur, "name": "Path" + str(id),
                 "node_list": list(range(0, f_id + 1)), "right_line_type": 1, "seg_id": id}],
                                 "name": "seg" + str(id)}
            id += 1
            hmap["segment_set"].insert(0, first_cur_segment)
            all_segment_id.insert(0, 0)
        # Append the last segment
        last_id = jw.index(key_jw[real_str_id[- 1]])
        all_segment_id.append(last_id)
        if last_id == len(jw) - 1:
            pass
        else:
            # Generate the last curve segment
            last_cur_segment = {"id": id, "lane_list": [
                {"id": 0, "lane_width": width, "left_line_type": 1, "max_vel": vel_cur, "name": "Path" + str(id),
                 "node_list": list(range(last_id, len(jw))), "right_line_type": 1, "seg_id": id}],
                                "name": "seg" + str(id)}
            id += 1
            hmap["segment_set"].append(last_cur_segment)
            all_segment_id.append(len(jw) - 1)

    # step7-3 if the route is a circle,add a new segment

    if is_circle == 1:
        op = [X[0], Y[0]]
        # 1 find the point that is the most nearest one from the origin
        min_dis = 100
        basic = len(jw) - 1
        all_x.reverse()
        all_y.reverse()
        for k in range((len(jw) - 1) - 25):
            all_other_point = [all_x[k], all_y[k]]
            all_dis = endpoint.distance(op, all_other_point)
            if all_dis < min_dis and all_dis != 0:
                min_dis = all_dis
                basic = len(jw) - 1 - k
            else:
                basic = len(jw) - 1
                break
        all_x.reverse()
        all_y.reverse()
        vector1 = [all_x[1] - all_x[0], all_y[1] - all_y[0]]
        vector2 = [all_x[0] - all_x[basic], all_y[0] - all_y[basic]]
        circle_cos = endpoint.vector_cos(vector1, vector2)
        while circle_cos < 0:
            basic = basic - 1
            vector = [all_x[0] - all_x[basic], all_y[0] - all_y[basic]]
            circle_cos = np.dot(vector1, vector) / (np.linalg.norm(vector1) * np.linalg.norm(vector))
        # if len(real_str_id) == 0:
        # while endpoint.distance([all_x[0], all_y[0]], [all_x[basic], all_y[basic]]) < 1:
        # basic = basic - 1
        # 2 find the point that is the most nearest one from the step1
        # Except for one curve segment
        if len(real_str_id) == 0:
            near_seg_id = 0
            hmap["segment_set"].remove(hmap["segment_set"][0])
        else:
            for s in range(basic - 1, 0, -1):
                if s in all_segment_id:
                    near_seg_id = s
                    break
            if all_segment_id.index(near_seg_id) == len(all_segment_id) - 2:
                hmap["segment_set"].remove(hmap["segment_set"][-1])
            else:
                for h in range(len(all_segment_id) - 2, all_segment_id.index(near_seg_id) - 1, -1):
                    hmap["segment_set"].remove(hmap["segment_set"][h])
        # 3 Append the added segment
        if near_seg_id - basic <= 2 or len(real_str_id) == 0:
            vel_sls = max_vel_cur
        else:
            vel_sls = max_vel_str
        second_last_segment = {"id": id, "lane_list": [
            {"id": 0, "lane_width": width, "left_line_type": 1, "max_vel": vel_sls,
             "name": "Path" + str(id),
             "node_list": list(range(near_seg_id, basic + 1)), "right_line_type": 1,
             "seg_id": id}], "name": "seg" + str(id)}
        id += 1
        hmap["segment_set"].append(second_last_segment)
        last_segment = {"id": id, "lane_list": [
            {"id": 0, "lane_width": width, "left_line_type": 1, "max_vel": vel_sls,
             "name": "Path" + str(id),
             "node_list": [basic, 0], "right_line_type": 1,
             "seg_id": id}], "name": "seg" + str(id)}
        id += 1
        hmap["segment_set"].append(last_segment)

    # step7-4 Add the back off segment
    rm_id = []
    previous_id = 0
    behind_id = 0
    for a in range(len(possible_backid)):
        if a % 2 == 0:
            for pre in range(possible_backid[a] - 1, 0, -1):
                if pre in all_segment_id:
                    previous_id = all_segment_id.index(pre)
                    break
            rm_id.append(previous_id)
        else:
            for back in range(possible_backid[a] + 1, len(jw)):
                if back in all_segment_id:
                    behind_id = all_segment_id.index(back)
                    break
            rm_id.append(behind_id)
    for b in range(len(rm_id) // 2):
        if rm_id[b + 1] - rm_id[b] == 1:
            hmap["segment_set"].remove(hmap["segment_set"][rm_id[b]])
        else:
            for c in range(rm_id[b + 1] - 1, rm_id[b] - 1, -1):
                hmap["segment_set"].remove(hmap["segment_set"][c])
        back_segment0 = {"id": id, "lane_list": [
            {"id": 0, "lane_width": width, "left_line_type": 1, "max_vel": max_vel_cur,
             "name": "Path" + str(id),
             "node_list": list(range(all_segment_id[rm_id[b]], possible_backid[b] + 1)), "right_line_type": 1,
             "seg_id": id}], "name": "seg" + str(id)}
        id += 1
        hmap["segment_set"].append(back_segment0)
        back_segment1 = {"id": id, "lane_list": [
            {"id": 0, "lane_width": width, "left_line_type": 1, "max_vel": max_vel_cur,
             "name": "Path" + str(id),
             "node_list": list(range(possible_backid[b], possible_backid[b + 1] + 1)), "right_line_type": 1,
             "seg_id": id}], "name": "seg" + str(id)}
        id += 1
        hmap["segment_set"].append(back_segment1)
        back_segment2 = {"id": id, "lane_list": [
            {"id": 0, "lane_width": width, "left_line_type": 1, "max_vel": max_vel_cur,
             "name": "Path" + str(id),
             "node_list": list(range(possible_backid[b + 1], all_segment_id[rm_id[b + 1]] + 1)),
             "right_line_type": 1,
             "seg_id": id}], "name": "seg" + str(id)}
        id += 1
        hmap["segment_set"].append(back_segment2)
    # step7-5 dump json file
    with open(name + '.hmap', 'w') as f1:
        json.dump(hmap, f1, indent=4)

    # step8 write json file for rmap
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
    print(name + '.hmap and ' + name + '.rmap are generated in the folder!')
    x = PrettyTable(
        ["Hmap&Rmap name", "Nodes Num", "Seg Num", "Width", "Vel of Str", "Vel of Cur", "Is Circle", "Has Backoff",
         "Same Zone"])
    x.align["Hmap&Rmap name"] = "l"
    x.padding_width = 1  # One space between column edges and contents (default)
    if autovel == 1:
        vel_of_str = "auto"
        vel_of_cur = "auto"
    else:
        vel_of_str = max_vel_str
        vel_of_cur = max_vel_cur
    if force == 0:
        same_zone = "Yes"
    else:
        same_zone = "No"
    x.add_row([name, len(hmap["node_set"]), len(hmap["segment_set"]), width, vel_of_str, vel_of_cur, is_circle,
               len(rm_id) // 2, same_zone])
    print(x)
    # step9 display the road only
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    # plt.plot(longi, lati)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_zlabel("z")

    figure = ax.plot(longi, lati, height, label='3D View')
    ax.plot(longi, lati, zdir='z', c='r', label='Top View')

    plt.legend()
    plt.show()
