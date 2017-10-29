# -*- coding:UTF-8 -*-
# Version 2.0
# Version 3.0: Add flag every line to judge roadmap types in pcmap
# Version 3.1: Add function to convert solid line to dotted line

import os
import sys
import argparse
import only_origin


# Commands for input files

def parser_options():
    parser = argparse.ArgumentParser()
    parser.add_argument("-vlog", required=True, action='append', nargs='*', dest='file_list')
    #parser.add_argument("--level", type=int, action='store', dest='lev', default=[4521])
    parser.add_argument("-circle",type=int,action='store',dest='is_circle',default=0)
    parser.add_argument("-width",type=float,action='store',dest='width',default=3.5)
    parser.add_argument("-name",type=str,action='store',dest='name',default='test')
    parser.add_argument("-velofstr",type=float,action='store',dest='max_vel_straight',default=10)
    parser.add_argument("-velofcur",type=float,action='store',dest='max_vel_curve',default=5)
    parser.add_argument("-visible",type=int,action='store',dest='visible',default=0)
    parser.add_argument("-vslam",type=int,action='store',dest='vslam',default=0)
    global argus
    argus = parser.parse_args()


# Check the validity of input files
def check_file():
    if len(argus.file_list[0]) < 1:
        return False
    for vlog_file in argus.file_list[0]:
        if vlog_file is None or os.path.exists(vlog_file) is False:
            return False
    return True


# Convert vlog files to pcmap files
def cvt_vlog(vlog_file, level):
    if "vlog_solid_line" in vlog_file:
        roadmap_type = 1
    elif "vlog_dotted_line" in vlog_file:
        roadmap_type = 2
    elif "vlog_deceleration_zone" in vlog_file:
        roadmap_type = 3
    elif "vlog_parking_line" in vlog_file:
        roadmap_type = 4
    elif "vlog_other_type" in vlog_file:
        roadmap_type = 5
    else:
        roadmap_type = 0

    with open(vlog_file, 'r') as f_log:
        coordinate_tmp = []
        coordinate = []
        line = f_log.readline()
        while line:
            if 'GGA' in line:
                list_split = line.split(',')
                if (level == 4):
                    if (list_split[6] == '4'):
                        coordinate_tmp.append(
                            [list_split[4], list_split[2], list_split[9], list_split[6], list_split[1]])
                elif (level == 5):
                    if (list_split[6] == '5'):
                        coordinate_tmp.append(
                            [list_split[4], list_split[2], list_split[9], list_split[6], list_split[1]])
                elif (level == 2):
                    if (list_split[6] == '2'):
                        coordinate_tmp.append(
                            [list_split[4], list_split[2], list_split[9], list_split[6], list_split[1]])
                elif (level == 1):
                    if (list_split[6] == '1'):
                        coordinate_tmp.append(
                            [list_split[4], list_split[2], list_split[9], list_split[6], list_split[1]])
                elif ((level == 45) or (level == 54)):
                    if (list_split[6] == '4') or (list_split[6] == '5'):
                        coordinate_tmp.append(
                            [list_split[4], list_split[2], list_split[9], list_split[6], list_split[1]])
                elif ((level == 452) or (level == 425) or (level == 542) or (level == 524) or (level == 245) or (
                    level == 254)):
                    if (list_split[6] == '4') or (list_split[6] == '5') or (list_split[6] == '2'):
                        coordinate_tmp.append(
                            [list_split[4], list_split[2], list_split[9], list_split[6], list_split[1]])
                elif (level >= 1000):
                    if (list_split[6] == '4') or (list_split[6] == '5') or (list_split[6] == '2') or (
                        list_split[6] == '1'):
                        coordinate_tmp.append(
                            [list_split[4], list_split[2], list_split[9], list_split[6], list_split[1]])
            line = f_log.readline()
        for line_tmp in coordinate_tmp:
            lng = float(line_tmp[0])
            lat = float(line_tmp[1])
            #height = float(line_tmp[2])
            height = 0.0
            level = int(line_tmp[3])
            time_stamp = line_tmp[4]
            lng = lng % 100 / 60 + int(lng) // 100
            lat = lat % 100 / 60 + int(lat) // 100
            coordinate.append([lng, lat, height, level, time_stamp])

    coordinate_dotted = []
    count = 0
    if "vlog_dotted_line" in vlog_file:
        for line_dotted in coordinate:
            if (count < 100):
                coordinate_dotted.append(
                    [line_dotted[0], line_dotted[1], line_dotted[2], line_dotted[3], line_dotted[4]])
                count = count + 1
            elif (count >= 200):
                count = 0
            else:
                count = count + 1

    with open(vlog_file + '.pcmap', 'w') as f_pcmap:
        #f_pcmap.write("1\n")
        if "vlog_dotted_line" in vlog_file:
            for line_coordinate in coordinate_dotted:
                #print("%.13f,%.13f,%.3f,%d,%s" % (
                #line_coordinate[0], line_coordinate[1], line_coordinate[2], line_coordinate[3], line_coordinate[4]))
                f_pcmap.write("%.13f,%.13f,%.3f,%d,%d,%s\n" % (
                line_coordinate[0], line_coordinate[1], line_coordinate[2], line_coordinate[3], roadmap_type,
                line_coordinate[4]))
        else:
            for line_coordinate in coordinate:
                #print("%.13f,%.13f,%.3f,%d,%s" % (
                #line_coordinate[0], line_coordinate[1], line_coordinate[2], line_coordinate[3], line_coordinate[4]))
                f_pcmap.write("%.13f,%.13f,%.3f,%d,%d,%s\n" % (
                line_coordinate[0], line_coordinate[1], line_coordinate[2], line_coordinate[3], roadmap_type,
                line_coordinate[4]))


if __name__ == "__main__":
    parser_options()
    ret = check_file()
    if ret is True:
        for vlog_file in argus.file_list[0]:
            if argus.vslam == 0:
                cvt_vlog(vlog_file, 4)
                print("vlog file is converted NOW!")
            #generate hmap and rmap automatically
            if argus.name == 'test':
                name = vlog_file[:-4]
            else:
                name = argus.name
            if argus.vslam == 0:
                only_origin.make_map(vlog_file + '.pcmap',argus.is_circle,argus.width,argus.max_vel_straight,argus.max_vel_curve,argus.visible,name,argus.vslam)
            else:
                only_origin.make_map(vlog_file,argus.is_circle,argus.width,argus.max_vel_straight,argus.max_vel_curve,argus.visible,name,argus.vslam)
            if os.path.exists(vlog_file + '.pcmap'):
                os.remove(vlog_file + '.pcmap')
            print("You have generated hmap and rmap NOW!")            
