from sqlalchemy.engine import URL
from sqlalchemy import create_engine
import sqlalchemy as sa
import pyodbc
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

conn_str = (
    r'driver={SQL Server};'
    r'server=4C4157STUDIO\SQLEXPRESS;' #server name
    r'database=FygensonLabData;' #database name
    r'trusted_connection=yes;'
    )

#using SQLAlchemy to avoid a UserWarning
connection_url = URL.create("mssql+pyodbc", query={"odbc_connect": conn_str})
engine = create_engine(connection_url) #create SQLAlchemy engine object

cnxn = pyodbc.connect(conn_str) #connect to server using pyodbc
cursor = cnxn.cursor()


def run_quary(quary_str):
    '''Run a quary and return the output as a pandas datafrme

    Args:
        quary_str (str): quary string (not case sensitive, SQL strings need to be enclosed in single quotes)

    Returns:
        dataframe: quary output
    '''
    with engine.begin() as conn:
        return pd.read_sql_query(sa.text(quary_str), conn)

date_key = int(input('Input the name of the image day folder: ')) 

#retrieve the cube offset data for this date from the SQL server (needed to crop the images into alignment)
cube_offset_df = run_quary(f'Select * From cube_offset Where date_id = {date_key}').set_index('date_id')
xdim = cube_offset_df.loc[date_key]['xdim']
ydim = cube_offset_df.loc[date_key]['ydim']
x_green_dim = cube_offset_df.loc[date_key]['x_green_dir']
y_green_dim = cube_offset_df.loc[date_key]['y_green_dir']
max_xdim = 1376 #size of images takeing at our microscope pre crop
max_ydim = 1040

print('Loading folders ...')
#change and get current working directory (cwd)
os.chdir('{}\Images\{}'.format(os.getcwd(), str(date_key)))
cwd = os.getcwd()

base_folders = os.listdir(cwd)

blank_image = np.zeros((ydim, xdim), dtype= np.uint16)

for folder in base_folders:
    image_files = sorted(os.listdir(f'{cwd}\{folder}\RAW')) #get the image file names 
    if ('blue' not in image_files[0]) or ('green' not in image_files[1]):
        #if the first image name does not have blue or the second image name does not have green then this is not a folder of two channel images to be stacked
        continue
    
    new_jpg_folder = f'{cwd}\{folder}\\rgb_stacks_jpg' #create new folders for the stacked images
    new_tif_folder = f'{cwd}\{folder}\\rgb_stacks_tif'
    os.mkdir(new_jpg_folder)
    os.mkdir(new_tif_folder)

    if (x_green_dim != 'left') or (y_green_dim != 'bottom'):
        print('add in the cropping setup for this...')
        continue
    else:
        print('Loading and croping images ...')
        green_images = [plt.imread(f'{cwd}\{folder}\RAW\{image_file}')[:ydim, max_xdim - xdim:] for image_file in image_files[1::2]] #[y-direction, x-direction]
        blue_images = [plt.imread(f'{cwd}\{folder}\RAW\{image_file}')[max_ydim - ydim:, :xdim] for image_file in image_files[::2]]

        print('Creating and saving RGB Stacks')
        num_images = len(green_images)
        for im_set in range(num_images):
            image_file_name = image_files[1::2][im_set][:-10]
            new_image = np.stack((green_images[im_set], blue_images[im_set], blue_images[im_set]), axis = 2) #stack the 2 images together
            ydim = np.shape(new_image)[0] #determine the size of the image to be abel to make the correct size blank figure
            xdim = np.shape(new_image)[1]
            inch_per_pixel = 0.014

            fig = plt.figure(frameon = False) #make a figure object that doesn't have the frame
            fig.set_size_inches(xdim*inch_per_pixel,ydim*inch_per_pixel)
            ax = plt.Axes(fig, [0,0,1,1])
            ax.set_axis_off()
            fig.add_axes(ax) #add an ax that doesn't have the axis elements
            ax.imshow(new_image, aspect = 'auto') #add the image to the figure

            image_jpg_file_name = image_file_name + '.jpg' #export as jpg
            plt.savefig('{}\{}'.format(new_jpg_folder, image_jpg_file_name))

            image_tif_file_name = image_file_name + '.tif' #export as tif
            plt.savefig('{}\{}'.format(new_tif_folder, image_jpg_file_name))
            plt.close()