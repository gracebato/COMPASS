import os
import numpy as np
from osgeo import gdal

def gen_ramp(burst, path_slc_vrt, path_slc_ramp, az_carrier_poly2d):
    '''
    Generating ramp on the input burst

    Parameters:
    -----------
    burst: Sentinel1BurstSlc
        Input burst
    path_slc_vrt: str
        Path to the burst SLC to be corrected
    path_slc_ramp: str:
        Path to the burst SLC after ramping
    az_carrier_poly2d: Namespace
        Azimuth carrier phase of the SLC data, in radians, as a function of azimuth and range

    '''
    # Load the burst SLC to correct
    slc_in = gdal.Open(path_slc_vrt, gdal.GA_ReadOnly)
    arr_slc_in = slc_in.ReadAsArray()

    # Apply the correction
    arr_slc_ramp = arr_slc_in.copy()
    radar_grid = burst.as_isce3_radargrid()
    
    i = np.arange(burst.length)
    j = np.arange(burst.width)
    i_az = i+burst.first_valid_line
    az = radar_grid.sensing_start + i_az/radar_grid.prf
    j_rg = j+burst.first_valid_sample
    rg = radar_grid.starting_range +  j_rg*radar_grid.range_pixel_spacing
    az_, rg_ = np.meshgrid(az,rg,indexing='ij')
    carrierPhase = az_carrier_poly2d.eval(az_,rg_)
    #arr_slc_ramp = arr_slc_in*np.exp(-1j*carrierPhase)
    arr_slc_ramp = np.exp(1j*carrierPhase)
 
    # Write out the ramp SLC
    dtype = slc_in.GetRasterBand(1).DataType
    drvout = gdal.GetDriverByName('ENVI')
    raster_out = drvout.Create(path_slc_ramp, burst.shape[1],
                               burst.shape[0], 1, dtype)
    band_out = raster_out.GetRasterBand(1)
    band_out.WriteArray(arr_slc_ramp)
    band_out.FlushCache()
    del band_out

    command = 'gdal_translate ' + path_slc_ramp + ' ' + path_slc_ramp + '.vrt'
    os.system(command)

