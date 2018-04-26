import cv2
import sys
import os
import random
import time
import numpy as np
from utilities import getTileInfo, rectangle, CYCLE_LEN


def featureMatch(img1, img2, filedir, tile_width, tile_height,
                 tl_pos_1, tl_pos_2):
    start_t = time.time()
    # get intersect rect
    rect1 = rectangle(tl_pos_1[0], tl_pos_1[1], tile_width, tile_height)
    rect2 = rectangle(tl_pos_2[0], tl_pos_2[1], tile_width, tile_height)
    overlap = rect1.interSect(rect2)
    if not overlap:
        print("img1 does not overlaps with img2")
        return
    img1 = img1[int(overlap._tl_y - rect1._tl_y):
                int(overlap._height + overlap._tl_y - rect1._tl_y),
                int(overlap._tl_x - rect1._tl_x):
                int(overlap._width + overlap._tl_x - rect1._tl_x)]
    img2 = img2[int(overlap._tl_y - rect2._tl_y):
                int(overlap._height + overlap._tl_y - rect2._tl_y),
                int(overlap._tl_x - rect2._tl_x):
                int(overlap._width + overlap._tl_x - rect2._tl_x)]
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
    end_t = time.time()
    img3 = cv2.drawMatches(img1, kp1, img2, kp2, matches[:2], None,
                           matchColor=(0, 255, 0), flags=2)
    cv2.imwrite(filedir+os.path.sep+"matches.bmp", img3)
    print("time elapsed for feature matching %f seconds" % (end_t - start_t))
    pass


def getImageData(filedir='', pair=[], tile_cols=0, tile_rows=0,
                 tile_pos_dict={}, tile_data_dict={}):
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
    first_tl_pos = (tl_pos_x, tl_pos_y)
    cycle_index, byte_pos, byte_size = \
        tile_data_dict[first_pair_x, first_pair_y]
    print("tile[%d, %d] with tile pos[%f, %f] and data info[%d, %d, %d]" %
          (first_pair_x, first_pair_y, tl_pos_x, tl_pos_y,
           cycle_index, byte_pos, byte_size))
    tl_pos_x, tl_pos_y = \
        tile_pos_dict[second_pair_x, second_pair_y]
    second_tl_pos = (tl_pos_x, tl_pos_y)
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
    return img1, img2, first_tl_pos, second_tl_pos
    pass


def single_pair_test(filedir='', pair=[]):
    """TODO: Docstring for single_pair_test.

    :filedir: must not be empty
    :pair: if empty, randomly select a pair
    :returns: None

    """
    # read image files from disk
    tile_width, tile_height, tile_cols, tile_rows, \
        tile_pos_dict, tile_data_dict = \
        getTileInfo(filedir)
    # read image data
    img1, img2, tl_pos_1, tl_pos_2 = getImageData(filedir, pair,
                                                  tile_cols, tile_rows,
                                                  tile_pos_dict,
                                                  tile_data_dict)
    # perform feature matching
    featureMatch(img1, img2, filedir, tile_width, tile_height,
                 tl_pos_1, tl_pos_2)
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
        print("or filedir")
        pass
    pass
