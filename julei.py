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
import parser
import argparse

#os.rename('qinglonghu.txt.pcmap','0904.txt')
#all_data=np.loadtxt('pcmap.txt')
all_data=[]
all_utm=[]
all_utm_time=[]
with open('0904.txt','r') as f:
    for line in f:
        every_line=list(map(float,line.split(',')))
        if np.size(every_line)==1:
            pass
        else:
            all_data.append(every_line)
    all_data=np.array(all_data)
    longi=all_data[:,0]
    lati=all_data[:,1]
    time=all_data[:,5]
    for i in range(len(longi)):
        u=utm.from_latlon(lati[i],longi[i])
        u=list(u)
        all_utm.append(u[0:2])
        u_time=[u[0],u[1],time[i]]
        all_utm_time.append(u_time)
    all_utm=np.array(all_utm)

    #step1 Kmeans Clusting
    n_clusters=len(longi)//20
    kmeans = KMeans(n_clusters, random_state=0).fit_predict(all_utm)
    #np.savetxt('class.txt',kmeans)
    #plt.scatter(all_utm[:,0],all_utm[:,1],c=kmeans)
    #plt.show()

    #step2 sort all points by time order
    all_point = []
    all_origin=[]
    all_utm_time=np.array(all_utm_time)
    for i in range(n_clusters):

        class_index=np.array(kmeans)
        same_class_index=np.where(class_index==i)
        same_class=all_utm_time[list(same_class_index[0])]
        origin_point,destination_point=endpoint.find_endpoint(same_class)
        all_point.append([origin_point,destination_point])
        all_origin.append(origin_point)

    all_origin=np.array(all_origin)
    origin=all_origin[0]
    all_point=np.array(all_point)
    #print(all_point)
    arg=np.argsort(all_origin[:,2])
    #print(arg)
    all_point_final=all_point[list(arg)]
    destination=all_point_final[-1][1]
    #print(all_point_final)
    #l=len(all_point)
    #all_point=np.array(all_point)
    #all_point=all_point.resize(l,2)
    #plt.scatter(all_point[0],all_point[1])

    #step3 Concat straight line
    while True:
        slope=endpoint.calculate_slope(all_point_final)
        after_concat,turn_point=endpoint.concat_stright(slope,all_point_final)
        if after_concat==all_point_final:
            break
        else:
            all_point_final=after_concat
    key_jw,X,Y=endpoint.utm2jw(all_point_final)


    #step4 insert points in long stright line
    while True:
        complete_point=endpoint.insert_for_long(all_point_final)
        if all_point_final==complete_point:
            break
        else:
            all_point_final=complete_point
    complete_point=np.array(complete_point)

    jw,no_use_x,no_use_y=endpoint.utm2jw(complete_point)
    new_jw = np.array(jw)
    lati=new_jw[:,0]
    longi=new_jw[:,1]
    #print(jw)
    longi_str = [str(l) for l in longi]
    lati_str = [str(t) for t in lati]

    #step5 display all the key points
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
    py.plot(fig, filename='Multiple Mapbox')

    #step6 write a json file for hmap
    hmap={"debug_info":{"lat_bias":0,"lng_bias":0},"is_coordinate_gps":1,"lane_switch_set":[],"node_set":[],"segment_set":[]}
    #step6-1 node_set
    for i in range(len(lati)):
        node_lat=lati[i]
        node_lng=longi[i]
        node={"gps_weight":1,"id":i,"lat":node_lat,"lng":node_lng,"lslam_carto_weight":0,"name":str(i),"qrcode_weight":0,"radius":0,"type":17,"vslam_weight":0,"z":0}
        hmap["node_set"].append(node)
    #step6-2 segment_set
    for j in range(len(key_jw)-1):
        point0_xy=[X[j],Y[j]]
        point1_xy=[X[j+1],Y[j+1]]
        dis = endpoint.distance(point0_xy,point1_xy)
        if dis < 5:
            max_vel = 8
        else:
            max_vel = 10
        point0=key_jw[j]
        point1=key_jw[j+1]
        index0=jw.index(point0)
        index1=jw.index(point1)
        segment={"id":j,"lane_list":[{"id":0,"lane_width":3.5,"left_line_type":1,"max_vel":max_vel,"name":"Path"+str(j),"node_list":list(range(index0,index1+1)),"right_line_type":1,"seg_id":j}],"name":"seg"+str(j)}
        hmap["segment_set"].append(segment)
    #step6-3 dump json file
    with open('test.hmap', 'w') as f1:
        json.dump(hmap, f1)

    #step7 write json file for rmap
    rmap={"name":"test","roadmap":"data/test.hmap","hmap_routes":[{"is_circle": 0,"name": "first","route_key_nodes": [{"id": 0,"is_stop": 1,"is_stop_enabled": 0},{"id":len(jw)-1,"is_stop": 1,"is_stop_enabled": 0}]},{"is_circle": 0,"name": "second","route_key_nodes": [{"id": len(jw)-1,"is_stop": 1,"is_stop_enabled": 0},{"id":0,"is_stop": 1,"is_stop_enabled": 0}]}]}
    with open('test.rmap', 'w') as f2:
        json.dump(rmap, f2)













