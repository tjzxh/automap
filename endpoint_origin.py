import numpy as np
import math
import utm

def distance(a,b):
    return math.sqrt(math.pow((a[0]-b[0]),2)+math.pow((a[1]-b[1]),2))

def find_endpoint(same_class):
    same_class=np.array(same_class)
    time=same_class[:,2]
    time=list(map(float, time))
    max_time_id=time.index(np.max(time))
    min_time_id=time.index(np.min(time))
    origin_point=same_class[min_time_id,:]
    destination_point=same_class[max_time_id,:]
    return list(origin_point),list(destination_point)


def find_endpoint_for_head_tail(same_class):
    same_class=np.array(same_class)
    point=list(same_class[:,0:2])
    max_dis=0
    for i in range(len(point)):
        for j in range(i+1,len(point)):
            dis=distance(point[i],point[j])
            if dis>max_dis:
                max_dis=dis
                origin_point = same_class[i, :]
                destination_point = same_class[j, :]
    return list(origin_point),list(destination_point)

def concat_stright(slope,all_point):
    key_point=[]
    for k in range(0,len(slope)-1,2):
        origin_of_class = all_point[k]
        destination_of_class = all_point[k + 1]
        if abs(slope[k+1]-slope[k])<math.tan(6*math.pi/180) or distance(list(origin_of_class[0]),list(origin_of_class[1]))+distance(list(destination_of_class[0]),list(destination_of_class[1]))<2:
            key_point.append([origin_of_class[0],destination_of_class[1]])

        else:
            key_point.append(list(all_point[k]))
            key_point.append(list(all_point[k+1]))

    if len(slope) % 2 == 1:
        key_point.append(list(all_point[len(slope)-1]))
    return key_point


def calculate_slope(all_point):
    slope=[]
    for j in all_point:
        point0_x=float(j[0][0])
        point0_y=float(j[0][1])
        point1_x=float(j[1][0])
        point1_y=float(j[1][1])
        if point0_x==point1_x:
            print(point0_x,point1_x)
        else:
            class_slope = (point1_y - point0_y) / (point1_x - point0_x)
            slope.append(class_slope)
    return slope


def insert_for_long(after_concat):
    all_point=[]
    for i in after_concat:
        point0=i[0]
        point1=i[1]
        dis=distance(point0,point1)
        if dis >= 10:
            insert=[(point0[0]+point1[0])/2,(point0[1]+point1[1])/2,point0[2]]
            all_point.append([point0,insert])
            all_point.append([insert,point1])

        else:
            all_point.append([point0,point1])
    return all_point


def utm2jw(all_point,zone_number,zone_letter):
    X = []
    Y = []
    jw = []
    origin_of_class=[]
    for i in all_point:
        X.append(i[0][0])
        X.append(i[1][0])
        Y.append(i[0][1])
        Y.append(i[1][1])
        jw.append(utm.to_latlon(i[0][0], i[0][1], zone_number, zone_letter))
        jw.append(utm.to_latlon(i[1][0], i[1][1], zone_number, zone_letter))
    # print(all_point)
    new_jw = list(set(jw))
    new_jw.sort(key=jw.index)
    return new_jw,X,Y
