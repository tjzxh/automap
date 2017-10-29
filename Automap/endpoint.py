import numpy as np
import math
import utm
from scipy.spatial.distance import squareform,pdist
from sklearn.metrics.pairwise import pairwise_distances

def distance(a,b):
    return math.sqrt(math.pow((a[0]-b[0]),2)+math.pow((a[1]-b[1]),2))

def find_endpoint(same_class):
    same_class=np.array(same_class)
    time = same_class[:, 2]
    time = list(map(float, time))
    if time==[]:
        return [],[]
    else:
        max_time_id=time.index(np.max(time))
        min_time_id=time.index(np.min(time))
        origin_point=same_class[min_time_id,:]
        destination_point=same_class[max_time_id,:]
        return list(origin_point),list(destination_point)


def find_endpoint_for_head_tail(same_class):
    same_class=np.array(same_class)
    point=list(same_class[:,0:2])
    dis=pairwise_distances(np.array(point), metric='euclidean')
    max_index=np.where(dis==np.max(dis))
    row_id=max_index[0][0]
    col_id=max_index[1][0]
    if same_class[row_id,2] < same_class[col_id,2]:
        ori_id=row_id
        des_id=col_id
    else:
        ori_id=col_id
        des_id=row_id
    origin_point = same_class[ori_id, :]
    destination_point = same_class[des_id, :]
    return list(origin_point),list(destination_point)


def delete_near_point(all_point,min_dis):
    point = list(all_point[:, 0:2])
    all_point_list=list(all_point[:, 0:4])
    delete_id=[]
    dele=[]
    dis = squareform(pdist(np.array(point), 'euclidean'))
    a=np.where(dis<min_dis)
    for i in range(len(a[0])):
        b=[a[0][i],a[1][i]]
        c=[a[1][i],a[0][i]]
        if b in delete_id or c in delete_id or b==c or a[1][i]-a[0][i]!=1:
            pass
        else:
            delete_id.append(b)
            dele.append(list(all_point_list[b[1]]))
    all_point_list=list(map(list,all_point_list))
    for j in dele:
        all_point_list.remove(j)
    return all_point_list


def concat_stright(slope,all_point):
    key_point=[]
    origin_point=all_point[0]
    key_point.append(list(origin_point))
    for k in range(0,len(slope)//2):
        origin_of_class = all_point[2*k]
        middle_of_class = all_point[2*k + 1]
        destination_of_class=all_point[2*k+2]
        vector1=np.mat([1,slope[2*k]])
        vector2=np.mat([1,slope[2*k+1]])
        simi_cos = np.dot(vector1, vector2.T) / (np.linalg.norm(vector1) * np.linalg.norm(vector2))
        if simi_cos > math.cos(5*math.pi/180):
            key_point.append(list(destination_of_class))
        else:
            key_point.append(list(middle_of_class))
            key_point.append(list(destination_of_class))

    if len(slope) % 2 == 1:
        if list(all_point[len(slope)-1]) not in key_point:
            key_point.append(list(all_point[len(slope)-1]))
        if list(all_point[len(slope)]) not in key_point:
            key_point.append(list(all_point[len(slope)]))
    return key_point


def calculate_slope(all_point):
    slope=[]
    for j in range(len(all_point)-1):
        point0=all_point[j]
        point1=all_point[j+1]
        point0_x=float(point0[0])
        point0_y=float(point0[1])
        point1_x=float(point1[0])
        point1_y=float(point1[1])
        if point0_x==point1_x:
            class_slope=10000
        else:
            class_slope = (point1_y - point0_y) / (point1_x - point0_x)
        slope.append(class_slope)
    return slope


def insert_for_long(after_concat):
    all_point=[]
    for i in range(len(after_concat)-1):
        point0=after_concat[i]
        point1=after_concat[i+1]
        all_point.append(list(point0))
        dis=distance(point0,point1)
        if dis >= 10:
            insert=[(point0[0]+point1[0])/2,(point0[1]+point1[1])/2,point0[2]]
            all_point.append(list(insert))
        if i==len(after_concat)-2:
            all_point.append(point1)
    return all_point


def utm2jw(all_point,zone_number,zone_letter):
    X = []
    Y = []
    jw = []
    origin_of_class=[]
    for i in all_point:
        X.append(i[0])
        Y.append(i[1])
        jw.append(utm.to_latlon(i[0], i[1], zone_number, zone_letter))

    new_jw = list(set(jw))
    new_jw.sort(key=jw.index)
    return new_jw,X,Y
