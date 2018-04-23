import cv2
import sys
import os
import random
import numpy as np


CYCLE_LEN = (1 << 30)


def getTileSize(scan_info_lines):
    tile_num_index = 0
    for i in range(len(scan_info_lines)):
        if '[tile_size]' == scan_info_lines[i]:
            tile_num_index = i + 1
            break
        pass
    if tile_num_index == 0:
        print("failed to find [tile_size]")
        return
    str_tile_width, str_tile_height = \
        scan_info_lines[tile_num_index].split(',')
    int_tile_width = int(str_tile_width)
    int_tile_height = int(str_tile_height)
    print("tile width %d height %d" % (int_tile_width, int_tile_height))
    return int_tile_width, int_tile_height


def getTileNum(scan_info_lines):
    tile_num_index = 0
    for i in range(len(scan_info_lines)):
        if '[tile_num]' == scan_info_lines[i]:
            tile_num_index = i + 1
            break
        pass
    if tile_num_index == 0:
        print("failed to find [tile_num]")
        return
    str_tile_cols, str_tile_rows = \
        scan_info_lines[tile_num_index].split(',')
    int_tile_cols = int(str_tile_cols)
    int_tile_rows = int(str_tile_rows)
    print("tile cols %d rows %d" % (int_tile_cols, int_tile_rows))
    return int_tile_cols, int_tile_rows


def getTilePos(scan_info_lines, tile_num):
    tile_num_index = 0
    for i in range(len(scan_info_lines)):
        if '[tile_pos_scene_topleft]' == scan_info_lines[i]:
            tile_num_index = i + 1
            break
        pass
    if tile_num_index == 0:
        print("failed to find [tile_pos_scene_topleft]")
        return
    tile_pos_dict = {}
    for i in range(tile_num_index,
                   tile_num_index+tile_num):
        str_tile_index_x, str_tile_index_y, str_tile_pos_x, str_tile_pos_y = \
            scan_info_lines[i].split(',')
        tile_pos_dict[int(str_tile_index_x), int(str_tile_index_y)] = \
            (float(str_tile_pos_x), float(str_tile_pos_y))
        pass
    return tile_pos_dict


def getDataInfo(align_info_lines):
    tile_num_index = 0
    for i in range(len(align_info_lines)):
        if '[tile_data_size]' == align_info_lines[i]:
            tile_num_index = i + 1
            break
        pass
    if tile_num_index == 0:
        print("failed to find [tile_data_size]")
        return
    tile_data_dict = {}
    while True:
        if ('[' in align_info_lines[tile_num_index]) or \
                (not align_info_lines[tile_num_index]):
            break
        str_tile_index_x, str_tile_index_y, str_pyramid_level, \
            str_cycle_index, str_byte_pos, str_byte_size = \
            align_info_lines[tile_num_index].split(',')
        if int(str_pyramid_level) == 1:
            tile_data_dict[int(str_tile_index_x), int(str_tile_index_y)] = \
                (int(str_cycle_index), int(str_byte_pos), int(str_byte_size))
            pass
        tile_num_index += 1
        pass
    return tile_data_dict


def featureMatch(img1, img2, filedir):
    # detect keypoints
    # extract descriptor
    orb = cv2.ORB_create()
    kp1, des1 = orb.detectAndCompute(img1, None)
    kp2, des2 = orb.detectAndCompute(img2, None)
    # feature match
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des1, des2)
    matches = sorted(matches, key=lambda x: x.distance)
    # draw matches
    img3 = cv2.drawMatches(img1, kp1, img2, kp2, matches[:3], None, flags=2)
    cv2.imwrite(filedir+os.path.sep+"matches.bmp", img3)
    pass


def single_pair_test(filedir='', pair=[]):
    """TODO: Docstring for single_pair_test.

    :filedir: must not be empty
    :pair: if empty, randomly select a pair
    :returns: None

    """
    # read image files from disk
    try:
        scan_info_file = open(filedir+os.path.sep+'scan_info_0.txt', 'r')
        pass
    except IOError as e:
        raise e
    scan_info_lines = scan_info_file.read().splitlines()
    scan_info_file.close()
    tile_width, tile_height = getTileSize(scan_info_lines)
    tile_cols, tile_rows = getTileNum(scan_info_lines)
    tile_pos_dict = getTilePos(scan_info_lines, tile_cols*tile_rows)
    try:
        align_info_file = open(filedir+os.path.sep+'alignment_info_0.txt', 'r')
    except IOError as e:
        raise e
    align_info_lines = align_info_file.read().splitlines()
    align_info_file.close()
    tile_data_dict = getDataInfo(align_info_lines)

    if pair:
        first_pair_x = pair[0][0]
        first_pair_y = pair[0][1]
        second_pair_x = pair[1][0]
        second_pair_y = pair[1][1]
        pass
    else:
        first_pair_x = random.randint(1, tile_cols-1)
        first_pair_y = random.randint(1, tile_rows-1)
        if random.randint(0, 1):
            second_pair_x = first_pair_x
            second_pair_y = first_pair_y + 1
            pass
        else:
            second_pair_x = first_pair_x + 1
            second_pair_y = first_pair_y
            pass
        pass
    tl_pos_x, tl_pos_y = \
        tile_pos_dict[first_pair_x, first_pair_y]
    cycle_index, byte_pos, byte_size = \
        tile_data_dict[first_pair_x, first_pair_y]
    print("tile[%d, %d] with tile pos[%f, %f] and data info[%d, %d, %d]" %
          (first_pair_x, first_pair_y, tl_pos_x, tl_pos_y,
           cycle_index, byte_pos, byte_size))
    tl_pos_x, tl_pos_y = \
        tile_pos_dict[second_pair_x, second_pair_y]
    cycle_index, byte_pos, byte_size = \
        tile_data_dict[second_pair_x, second_pair_y]
    print("tile[%d, %d] with tile pos[%f, %f] and data info[%d, %d, %d]" %
          (second_pair_x, second_pair_y, tl_pos_x, tl_pos_y,
           cycle_index, byte_pos, byte_size))

    image_bin = open(filedir+os.path.sep+"alignment_data_0.bin", "rb")
    cycle_index, byte_pos, byte_size = \
        tile_data_dict[first_pair_x, first_pair_y]
    image_bin.seek(cycle_index*CYCLE_LEN+byte_pos)
    jpeg_data = image_bin.read(byte_size)
    img1 = cv2.imdecode(np.fromstring(jpeg_data, dtype=np.uint8),
                        cv2.IMREAD_UNCHANGED)

    cycle_index, byte_pos, byte_size = \
        tile_data_dict[second_pair_x, second_pair_y]
    image_bin.seek(cycle_index*CYCLE_LEN+byte_pos)
    jpeg_data = image_bin.read(byte_size)
    img2 = cv2.imdecode(np.fromstring(jpeg_data, dtype=np.uint8),
                        cv2.IMREAD_UNCHANGED)
    image_bin.close()
    # perform feature matching
    featureMatch(img1, img2, filedir)
    pass


if __name__ == '__main__':
    if(len(sys.argv) == 6):
        filedir = sys.argv[1]
        first_pair_x = int(sys.argv[2])
        first_pair_y = int(sys.argv[3])
        second_pair_x = int(sys.argv[4])
        second_pair_y = int(sys.argv[5])
        pair = [(first_pair_x, first_pair_y), (second_pair_x, second_pair_y)]
        single_pair_test(filedir, pair)
        pass
    elif (len(sys.argv) == 2):
        filedir = sys.argv[1]
        pair = []
        single_pair_test(filedir, pair)
        pass
    else:
        print("input format should be filedir, first_pair_x, first_pair_y" +
              ", second_pair_x, second_pair_y")
        pass
    pass
