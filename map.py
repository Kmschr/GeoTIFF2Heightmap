import argparse
import rasterio
import numpy as np
from argparse import RawTextHelpFormatter
from progress.bar import IncrementalBar
from pyproj import CRS, Transformer
from struct import *
from PIL import Image

# Sanitize input using custom type
def downsample_type(x):
    x = int(x)
    if x < 1:
        raise argparse.ArgumentTypeError('Minimum downsampling option is 1')
    return x

# CLI SETUP
desc = 'Convert GeoTIFF raster data to rgba encoded PNG heightmaps'
parser = argparse.ArgumentParser(description=desc, formatter_class=RawTextHelpFormatter)
parser.add_argument('filepath', metavar='FILE', type=str,
                    help='file path for GeoTIFF (.tif) data')
parser.add_argument('-o', metavar='OUTFILE', type=str, default='heightmap.png',
                    help='specify output file/path (default: heightmap.png)')
parser.add_argument('-d', metavar='DOWNSAMPLE', default=1, type=downsample_type,
                    help='skip over every n-1 data points for smaller image output (default: 1)')
parser.add_argument('-v', metavar='VERTICAL SCALE', type=int, default=100,
                    help='height multiplier - controls vertical resolution (default=100)')
parser.add_argument('-n', '--normalize', action='store_true',
                    help='subtract min height from height values')
parser.add_argument('-p', '--project', action='store_true',
                    help='print detailed info about bounds in mercator projection')

# parse args
args = parser.parse_args()
scale = args.d
normalize = args.normalize
vertical_scale = args.v
project = args.project

# Inward offset for each edge
start_x = 0
start_y = 0
end_x = 0
end_y = 0

# Open and read dataset
dataset = rasterio.open(args.filepath)
width = dataset.width
height = dataset.height

topleft = dataset.transform * (0, 0)
botright = dataset.transform * (width, height)

width_in_meters = dataset.bounds.right - dataset.bounds.left
height_in_meters = dataset.bounds.top - dataset.bounds.bottom

image_width = (width - start_x - end_x) // scale
image_height = (height - start_y - end_y) // scale

print('Reading from', dataset.name, '\n')

print('Bounds:')
print('  ', dataset.crs)
print('  ', topleft)
print('  ', botright, '\n')

# Get mercator coordinates of bounds
if project:
    epsg = str(dataset.crs).split(':',1)[1]
    crs = CRS.from_epsg(int(epsg))

    proj = Transformer.from_crs(crs, crs.geodetic_crs)

    topleft_proj = proj.transform(topleft[0], topleft[1])
    botright_proj = proj.transform(botright[0], botright[1])
        
    print('   Mercator')
    print('  ', topleft_proj)
    print('  ', botright_proj, '\n')

print('Input Size:')
print('  Width: ', width, 'px (', width_in_meters, 'm)', sep='')
print('  Height: ', height, 'px (', height_in_meters, 'm)\n', sep='')

print('Output Size:')
print('  Width: ', image_width, 'px', sep='')
print('  Height: ', image_height, 'px\n', sep='')

# Extract elevation data
print('Rasterizing...')
band1 = dataset.read(1)
print('Done rasterizing\n')

# Get range of heights
minheight = float('inf')
maxheight = float('-inf')

# Scaled bounds of image sampling
min_sample_x = start_x // scale
max_sample_x = (width - end_x) // scale
min_sample_y = start_y // scale
max_sample_y = (height - end_y) // scale

# Track progress for large datasets
total_stripes = max_sample_x - min_sample_x

if normalize:
    bar = IncrementalBar('Calculating height extremes', max=total_stripes, suffix='%(percent)d%%')
    for x in range(min_sample_x, max_sample_x):
        for y in range(min_sample_y, max_sample_y):
            # Point to sample from raster data
            sample_x = x * scale
            sample_y = y * scale

            val = band1[sample_y][sample_x]
            if val < 0:
                continue

            if val < minheight:
                minheight = val
            elif val > maxheight:
                maxheight = val
        bar.next()
    bar.finish()
    print('Min height:', minheight, 'meters')
    print('Max height:', maxheight, 'meters\n')

# Drawing heightmap
heightmap = Image.new('RGBA', (image_width, image_height))

bar = IncrementalBar('Drawing heightmap', max=total_stripes, suffix='%(percent)d%%')
for x in range(min_sample_x, max_sample_x):
    for y in range(min_sample_y, max_sample_y):
        # Point to sample from raster data
        sample_x = x * scale
        sample_y = y * scale

        val = band1[sample_y][sample_x]

        if normalize:
            val -= minheight

        # Filter out missing data points
        if val < 0:
            val = 0
        
        val = int(val * vertical_scale)
        
        # Split 32-bit height value into tuple of four 8-bit values (rgba)
        rgba_bytes = pack('>I', val)
        rgba_vals = unpack('BBBB', rgba_bytes)
        heightmap.putpixel((x - min_sample_x, y - min_sample_y), rgba_vals)
    bar.next()
bar.finish()


print('Saving image...')
heightmap.save(args.o)

print('Done!')