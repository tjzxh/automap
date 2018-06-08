import segment
from scipy.spatial import cKDTree

pcmap = 'shahe.gps.1.log.pcmap'
vslam = 0
gps = 1
autovel = 0
is_local = 0
_, _, _, _, _, _, _, jw, _, _, key_jw, real_str_id, point4all, point4key = segment.seg(pcmap, vslam, gps, autovel,
                                                                                       is_local)
roads_way_pointlist = []
is_str_list = []
roadnum = len(key_jw) - 1
if len(real_str_id) == 0:
    roads_way_pointlist = point4all.tolist()
    is_str_list.append(False)
else:
    # Distinguish the stright and curve
    for p in range(len(real_str_id) - 1):
        first_id = jw.index(key_jw[real_str_id[p]])
        second_id = jw.index(key_jw[real_str_id[p] + 1])
        third_id = jw.index(key_jw[real_str_id[p + 1]])
        # Generate the stright segment
        str_segment = point4all[first_id:second_id + 1].tolist()
        roads_way_pointlist.append(str_segment)
        is_str_list.append(True)
        # Generate the curve segment if second id is not the same as third id
        if second_id == third_id:
            pass
        else:
            cur_segment = point4all[second_id:third_id + 1].tolist()
            roads_way_pointlist.append(cur_segment)
            is_str_list.append(False)

    # Append the first segment
    f_id = jw.index(key_jw[real_str_id[0]])
    if f_id == 0:
        pass
    else:
        # Generate the first curve segment
        first_cur_segment = point4all[:f_id + 1].tolist()
        roads_way_pointlist.insert(0, first_cur_segment)
        is_str_list.append(False)
    # Append the last segment
    last_id = jw.index(key_jw[real_str_id[- 1]])
    if last_id == len(jw) - 1:
        pass
    else:
        # Generate the last curve segment
        last_cur_segment = point4all[last_id:].tolist()
        roads_way_pointlist.append(last_cur_segment)
        is_str_list.append(False)
