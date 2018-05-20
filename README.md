README

This is an example of python simulator that sequentially takes in misaligned image tiles(2048x2048)
obtained by whole slide imager(WSI) and generate the new alignment position for each tile in real-time
during tissue scanning. What we mean 'misaligned' here is that although camera is triggered by stage positioning to
acquire image tiles there could be up to 50 pixels(0.45um per pixel) position misalignment due to a
variety of reasons including mechanical disturbance, latencies in camera capturing, camera calibration
errors, etc.

To begin, the simulator will read the original tile info(positions, tile size, etc.) from assigned directory
and parse these data into data structures. The tile info are stored in txt files format.

To align each image tile, we will compute the keypoints(for example, corners) and extract feature descriptors in areas where
this tile overlaps with neighboring tiles that have already been aligned. Then we will match features
between current tile and its neighroing tiles with a measure called 'distance', the smaller the distance,
the better chance for this pair of features being identical. One intuitive way is to find the match with
the shortest distance
and adjust the current position accordingly, but algorithms may lie to you, especially for features located
at the blank area of a slide. What we adopted here is to use the two pairs with least distances and check
if the two new alignment positions proposed separately by the top two agree with each other. If so, we have good
confidence in the new tile position.

One more important thing to take care is that it is possible the
top two matched features in current tile could be 'geographically' close to each other. In this way, the two pair test
may result in wrong alignment as the two features may indicate the same location in current tile. So one more
criterion for the two pair test is that the two features must be 32 pixels away from each other. Note that
32 pixels is the dimension of feature patches used in feature extraction.

This simulator will calculate the 'offset' from current position to new alignment position. It will also
check if the 'resize' tile(about 1441x1441, we only want the image in the center of a tile for better quality)
remains within the current tile with new position. If not, the simulator will raise an error and terminate, as
this means there is too much error in the original positioning.

After the simulator finishes alignment, it will generate the alignment info and store it in txt file format.

To run the tile aligner, you will need python3, numpy, and opencv3.4 for python.

How to run the code:

	python turbo_tile_aligner.py <tile_data_directory> <simulate in zigzag?> <use aligner?>

typical example:

	python turbo_tile_aligner.py ./data 1 1

A copy of unaligned image data could be downloaded [Here](https://drive.google.com/drive/folders/1u7hxsuSNjXtwzQVCzkR68zRcWwTgIKi0?usp=sharing)
