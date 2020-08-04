# GeoTIFF2Heightmap
Convert GeoTIFF raster data to rgba encoded PNG heightmaps

![Example output](https://i.imgur.com/hmDpMVL.png)
![Example output](https://i.imgur.com/JWjINQc.png)

### Getting data
There are a lot of good sources for getting high resolution elevation data, though it is not available for all areas and the data is not always complete or free of noise. Here are some sources I used while making this program.

[OpenTopography](https://opentopography.org/) - 
1 meter resolution Lidar scans with option to supress noise/trees and generate shaded relief maps, limited to specific areas within the US. Some data is restricted to users with .edu email address

[USGS TNM](https://viewer.nationalmap.gov/basic/) - 
Covers a larger area than OpenTopography and has multiple resolutions available but has less options for pulling data from specific bounds

### Usage

`python3 map.py -h` for usage instructions:

    usage: map.py [-h] [-o OUTFILE] [-d DOWNSAMPLE] [-v VERTICAL SCALE] [-n] FILE

    Convert GeoTIFF raster data to rgba encoded PNG heightmaps

    positional arguments:
    FILE               file path for GeoTIFF (.tif) data

    optional arguments:
    -h, --help         show this help message and exit
    -o OUTFILE         specify output file/path (default: heightmap.png)
    -d DOWNSAMPLE      skip over every n-1 data points for smaller image output (default: 1)
    -v VERTICAL SCALE  height multiplier - controls vertical resolution (default=100)
    -n, --normalize    subtract min height from height values