import cv2
import sys
import os
import time
import numpy as np
from shutil import copy2
from utilities import getTileInfo, rectangle, CYCLE_LEN
from utilities import featureObj


class turbo_tile_aligner(object):

    """Docstring for turbo_tile_aligner. """

    def __init__(self, filedir=''):
        """initialize turbo_tile_aligner

        :filedir: directory to image files

        """
        self._filedir = filedir
        self._time_elapsed = 0.
        self._tile_width = 0
        self._tile_height = 0
        self._tile_cols = 0
        self._tile_rows = 0
        self._tile_pos_dict = {}
        self._tile_data_dict = {}
        pass

    def parseTileInfo(self):
        self._tile_width, self._tile_height, \
            self._tile_cols, self._tile_rows, \
            self._tile_pos_dict, self._tile_data_dict = \
            getTileInfo(self._filedir)
        pass

    def processResizing(self, left, new_left,
                        right, new_right,
                        top, new_top,
                        bottom, new_bottom):
        if(new_left != left) or (new_right != right):
            if new_right == right:
                new_right = right - (new_left - left)
                pass
            elif new_left == left:
                new_left = left + (right - new_right)
                pass
            if(new_top == top) and (new_bottom == bottom):
                temp = self._tile_height * \
                    (new_left-left) / self._tile_width
                new_top = top + temp
                new_bottom = bottom - temp
            pass
        if(new_top != top) or (new_bottom != bottom):
            if new_bottom == bottom:
                new_bottom = bottom - (new_top - top)
                pass
            elif new_top == top:
                new_top = top + (bottom - new_bottom)
                pass
            if(new_left == left) and (new_right == right):
                temp = self._tile_width * \
                    (new_top-top) / self._tile_height
                new_left = left + temp
                new_right = right - temp
            pass
        if new_left != left:
            new_left -= 4.
            new_right += 4.
            new_top -= 4.
            new_bottom += 4.
            pass
        return new_left, new_top, \
            int(new_right-new_left), \
            int(new_bottom-new_top)

    def getResizeTileDict(self):
        resize_tile_dict = {}
        for i, j in self._tile_pos_dict.keys():
            left = self._tile_pos_dict[i, j][0]
            top = self._tile_pos_dict[i, j][1]
            right = left + self._tile_width
            bottom = top + self._tile_height
            new_left = left
            new_right = right
            new_top = top
            new_bottom = bottom
            if (i-1, j) in self._tile_pos_dict:
                temp = self._tile_pos_dict[i-1, j][0] + \
                    self._tile_width
                new_left = (temp + left) / 2
                pass
            if (i+1, j) in self._tile_pos_dict:
                temp = self._tile_pos_dict[i+1, j][0]
                new_right = (temp + right) / 2
                pass
            if (i, j-1) in self._tile_pos_dict:
                temp = self._tile_pos_dict[i, j-1][1] + \
                    self._tile_height
                new_top = (temp + top) / 2
                pass
            if (i, j+1) in self._tile_pos_dict:
                temp = self._tile_pos_dict[i, j+1][1]
                new_bottom = (temp + bottom) / 2
                pass
            tl_x, tl_y, int_width, int_height = \
                self.processResizing(left, new_left,
                                     right, new_right,
                                     top, new_top,
                                     bottom, new_bottom)
            print("resize tile[%d, %d] at(%f, %f) with width %d height %d" %
                  (i, j, tl_x, tl_y,
                   int_width, int_height))
            resize_tile_dict[i, j] = rectangle(tl_x, tl_y,
                                               int_width,
                                               int_height)
            pass
        return resize_tile_dict

    def extractFeatures(self, x_index, y_index, orb):
        assert isinstance(orb, cv2.ORB)
        output = (None, None, None, None)
        tile_list = [(x_index-1, y_index), (x_index, y_index-1),
                     (x_index+1, y_index), (x_index, y_index+1)]
        # get image data and rect
        image_bin = open(self._filedir + os.path.sep +
                         "alignment_data_0.bin", "rb")
        cycle_index, byte_pos, byte_size = \
            self._tile_data_dict[x_index, y_index]
        image_bin.seek(cycle_index*CYCLE_LEN+byte_pos)
        jpeg_data = image_bin.read(byte_size)
        image_bin.close()
        img = cv2.imdecode(np.fromstring(jpeg_data, dtype=np.uint8),
                           cv2.IMREAD_UNCHANGED)
        this_rect = rectangle(self._tile_pos_dict[x_index, y_index][0],
                              self._tile_pos_dict[x_index, y_index][1],
                              self._tile_width, self._tile_height)
        # extract descriptors
        temp_t = time.time()
        for i in range(len(tile_list)):
            if tile_list[i] in self._tile_pos_dict:
                other_rect = rectangle(self._tile_pos_dict[tile_list[i]][0],
                                       self._tile_pos_dict[tile_list[i]][1],
                                       self._tile_width, self._tile_height)
                overlap = this_rect.interSect(other_rect)
                if overlap:
                    crop = img[int(overlap._tl_y - this_rect._tl_y):
                               int(overlap._tl_y + overlap._height -
                                   this_rect._tl_y),
                               int(overlap._tl_x - this_rect._tl_x):
                               int(overlap._tl_x + overlap._width -
                                   this_rect._tl_x)]
                    kp, des = orb.detectAndCompute(crop)
                    offset_x = int(overlap._tl_x - this_rect._tl_x)
                    offset_y = int(overlap._tl_y - this_rect._tl_y)
                    output[i] = featureObj(kp, des, offset_x, offset_y)
                    pass
                pass
            pass
        self._time_elapsed += time.time() - temp_t
        return output

    def featureMatch(self, x_index, y_index, des_list,
                     align_tile_dict, tile_des_dict, bf):
        assert isinstance(bf, cv2.BFMatcher)
        tile_list = [(x_index-1, y_index), (x_index, y_index-1),
                     (x_index+1, y_index), (x_index, y_index+1)]
        temp_t = time.time()
        for i in range(len(tile_list)):
            if tile_list[i] in tile_des_dict:
                other_des = tile_des_dict[tile_list[i]]
                pair_idx = (i+2) % 4
                if des_list[i] and other_des[pair_idx]:
                    matches = bf.match(des_list[i]._descriptors,
                                       other_des[pair_idx]._descriptors)
                    if len(matches) >= 2:
                        matches = sorted(matches, key=lambda x: x.distance)
                        other_tl_x = align_tile_dict[tile_list[i]][0]
                        other_tl_y = align_tile_dict[tile_list[i]][1]
                        new_tls = []
                        for j in [0, 1]:
                            kp1 = des_list[i]._keypoints[
                                matches[j].queryIdx]
                            kp2 = other_des[pair_idx]._keypoints[
                                matches[j].trainIdx]
                            new_tl_x = other_tl_x + kp2.pt.x + \
                                other_des[pair_idx]._tl_x - \
                                (kp1.pt.x + des_list[i]._tl_x)
                            new_tl_y = other_tl_y + kp2.pt.y + \
                                other_des[pair_idx]._tl_y - \
                                (kp1.pt.y + des_list[i]._tl_y)
                            new_tls.append((new_tl_x, new_tl_y))
                            pass
                        if abs(new_tls[0][0] - new_tls[1][0]) < 2. and \
                                abs(new_tls[0][1] - new_tls[1][1]) < 2.:
                            self._time_elapsed += time.time() - temp_t
                            return True, (new_tls[0][0] + new_tls[1][0]) / 2. \
                                (new_tls[0][1] + new_tls[1][1]) / 2.
                        pass
                pass
            pass
        self._time_elapsed += time.time() - temp_t
        return False, 0., 0.

    def performAlignment(self, isZigZag=False, resize_tile_dict={}):
        align_tile_dict = {}
        tile_des_dict = {}
        orb = cv2.ORB_create()
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        for i in range(self._tile_cols):
            x_index = i+1
            for j in range(self._tile_rows):
                y_index = j+1
                if isZigZag and (0 == x_index % 2):
                    y_index = self._tile_rows-j
                    pass
                # detect keypoints and compute descriptors
                des_list = self.extractFeatures(x_index, y_index, orb)
                # match features against neighbors
                isMatch, new_tl_x, new_tl_y = \
                    self.featureMatch(x_index, y_index,
                                      des_list, align_tile_dict,
                                      tile_des_dict, bf)
                # adjust tile position
                tile_des_dict[x_index, y_index] = des_list
                if not isMatch:
                    new_tl_x, new_tl_y = self._tile_pos_dict[x_index, y_index]
                    pass
                align_tile_dict[x_index, y_index] = \
                    rectangle(new_tl_x, new_tl_y,
                              self._tile_width,
                              self._tile_height)
                prev_tl_x, prev_tl_y = self._tile_pos_dict[x_index, y_index]
                print("Is matched? %d" % isMatch +
                      " and alignment offset of tile[%d, %d] is (%f, %f)" %
                      (x_index, y_index, new_tl_x - prev_tl_x,
                       new_tl_y - prev_tl_y))
                # check if resize tile is still contained in align tile
                align_rect = align_tile_dict[x_index, y_index]
                resize_rect = resize_tile_dict[x_index, y_index]
                if not align_rect.contains(resize_rect):
                    print("Error: alignment is out of range at tile[%d, %d]"
                          % (x_index, y_index))
                    return
                pass
            pass
        return align_tile_dict

    def outputInfo(self, resize_tile_dict={}, align_tile_dict={}):
        outdir = self._filedir+os.path.sep+"output"
        if not os.path.exists(outdir):
            os.makedirs(outdir)
            pass
        copy_file_list = ["scan_info_0.txt", "preview.bmp",
                          "out_for_web.txt", "Label.bmp",
                          "alignment_data_0.bin"]
        for file2copy in copy_file_list:
            file_path = self._filedir+os.path.sep+file2copy
            if not os.path.exists(outdir+os.path.sep+file2copy):
                copy2(file_path, outdir)
                pass
            pass
        align_file = open(self._filedir + os.path.sep +
                          "alignment_info_0.txt", 'r')
        align_info_lines = align_file.read().splitlines()
        align_file.close()
        align_file = open(outdir+os.path.sep+"alignment_info_0.txt", 'w')
        for i in range(len(align_info_lines)):
            if align_info_lines[i] == '[align_tile_pos_scene_topleft]':
                break
            align_file.write(align_info_lines[i]+'\n')
            pass
        align_file.write('[align_tile_pos_scene_topleft]'+'\n')
        for j in range(self._tile_rows):
            y_index = j + 1
            for i in range(self._tile_cols):
                x_index = i + 1
                out_array = []
                rect = align_tile_dict[x_index, y_index]
                out_array.append(x_index)
                out_array.append(y_index)
                out_array.append(rect._tl_x)
                out_array.append(rect._tl_y)
                align_file.write(','.join(str(a) for a in out_array) + '\n')
                pass
            pass
        align_file.write('[resize_tile_pos_scene_topleft]'+'\n')
        for j in range(self._tile_rows):
            y_index = j + 1
            for i in range(self._tile_cols):
                x_index = i + 1
                out_array = []
                rect = resize_tile_dict[x_index, y_index]
                out_array.append(x_index)
                out_array.append(y_index)
                out_array.append(rect._tl_x)
                out_array.append(rect._tl_y)
                out_array.append(1)
                out_array.append(self._tile_rows*self._tile_cols)
                out_array.append(rect._width)
                out_array.append(rect._height)
                align_file.write(','.join(str(a) for a in out_array) + '\n')
                pass
            pass
        align_file.close()
        pass

    def run(self, isZigZag=False):
        # reset time elapsed
        self._time_elapsed = 0.
        start_t = time.time()
        # parse tile info
        self.parseTileInfo()
        # pre-alignment resizing
        resize_tile_dict = self.getResizeTileDict()
        # align tiles
        align_tile_dict = self.performAlignment(isZigZag, resize_tile_dict)
        # output alignment info to outdir
        self.outputInfo(resize_tile_dict, align_tile_dict)
        # output total time elapsed
        end_t = time.time()
        print("total time elapsed for aligner is %f sec"
              % (end_t-start_t))
        print("time elapsed for feature extraction and matching is %f sec"
              % (self._time_elapsed))
        pass


if __name__ == '__main__':
    if(len(sys.argv == 2)):
        filedir = sys.argv[1]
        aligner = turbo_tile_aligner(filedir)
        aligner.run()
        pass
    elif(len(sys.argv == 3)):
        filedir = sys.argv[1]
        isZigZag = bool(int(sys.argv[2]))
        aligner = turbo_tile_aligner(filedir)
        aligner.run(isZigZag)
        pass
    else:
        print("input format should be: " +
              "python turbo_tile_aligner.py <filedir>" +
              "or python turbo_tile_aligner.py <filedir> <useZigZag>")
        pass
    pass
