import os

CYCLE_LEN = (1 << 30)


def getTileSize(scan_info_lines):
    tile_num_index = 0
    for i in range(len(scan_info_lines)):
        if '[tile_size]' == scan_info_lines[i]:
            tile_num_index = i + 1
            break
        pass
    if tile_num_index == 0:
        raise NameError("failed to find [tile_size]")
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
        raise NameError("failed to find [tile_num]")
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
        raise NameError("failed to find [tile_pos_scene_topleft]")
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
        raise NameError("failed to find [tile_data_size]")
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


def getTileInfo(filedir=''):
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
    return tile_width, tile_height, tile_cols, tile_rows, tile_pos_dict, \
        tile_data_dict


class rectangle(object):

    """Docstring for rectangle. """

    def __init__(self, tl_x, tl_y, width, height):
        """TODO: to be defined1.

        :tl_x: TODO
        :tl_y: TODO
        :width: TODO
        :height: TODO

        """
        self._tl_x = tl_x
        self._tl_y = tl_y
        self._width = width
        self._height = height

    def interSect(self, other):
        assert isinstance(other, rectangle)
        if((self._tl_x < other._tl_x+other._width) or
           (other._tl_x < self._tl_x+self._width)) and \
                ((self._tl_y < other._tl_y+other._height) or
                 (other._tl_y < self._tl_y+self._height)):
            new_tl_x = max(self._tl_x, other._tl_x)
            new_tl_y = max(self._tl_y, other._tl_y)
            new_br_x = min(self._tl_x+self._width, other._tl_x+other._width)
            new_br_y = min(self._tl_y+self._height, other._tl_y+other._height)
            return rectangle(new_tl_x, new_tl_y,
                             new_br_x - new_tl_x,
                             new_br_y - new_tl_y)
        return None

    def contains(self, other):
        assert isinstance(other, rectangle)
        if (self._tl_x <= other._tl_x) and \
                (self._tl_y <= other._tl_y) and \
                (self._tl_x+self._width >=
                 other._tl_x+other._width) and \
                (self._tl_y+self._height >=
                 other._tl_y+other._height):
            return True
        return False


class featureObj(object):

    """Docstring for featureObj. """

    def __init__(self, keypoints, descriptors, tl_x, tl_y):
        """TODO: to be defined1.

        :keypoints: TODO
        :descriptors: TODO
        :tl_x: TODO
        :tl_y: TODO

        """
        self._keypoints = keypoints
        self._descriptors = descriptors
        self._tl_x = tl_x
        self._tl_y = tl_y
        pass
