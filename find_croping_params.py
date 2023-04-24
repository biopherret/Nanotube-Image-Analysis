from sqlalchemy.engine import URL
from sqlalchemy import create_engine
import sqlalchemy as sa
import pyodbc
import pandas as pd
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
    
def edit_database(quary_str):
    '''Edit database with quary

    Args:
        quary_str (str): quary string (not case sensitive, SQL strings need to be enclosed in single quotes)
    ''' 
    cursor.execute(quary_str)
    cnxn.commit()

cube_offset_df = run_quary('Select * From cube_offset;').set_index('date_id') #retrieve the cube_offset table from the SQL server
max_xdim = 1376 #size of images takeing at our microscope pre crop
max_ydim = 1040

for day in cube_offset_df.index.values.tolist():
    green_x = cube_offset_df.loc[day]['green_x']
    green_y = cube_offset_df.loc[day]['green_y']
    blue_x = cube_offset_df.loc[day]['blue_x']
    blue_y = cube_offset_df.loc[day]['blue_y']

    ydim = int(max_ydim - np.abs(green_y - blue_y)) #determine the new dimentions
    xdim = int(max_xdim - np.abs(green_x - blue_x))

    edit_database(f'Update cube_offset Set ydim = {ydim}, xdim = {xdim} Where date_id = {day}')

    if green_y < blue_y: #determine if the bottom or top side of the green image should be cropped (opposite side of blue is cropped)
        green_crop_yend = ydim #crop the bottom off the green image
        blue_crop_ystart = max_ydim - ydim #crop the top off the blue image
        edit_database(f'Update cube_offset Set green_crop_yend = {green_crop_yend}, blue_crop_ystart = {blue_crop_ystart} Where date_id = {day}')
    elif green_y > blue_y: 
        green_crop_ystart = max_ydim - ydim #crop the top off the green image
        blue_crop_yend = ydim #crop the bottom off the blue image
        edit_database(f'Update cube_offset Set green_crop_ystart = {green_crop_ystart}, blue_crop_yend = {blue_crop_yend} Where date_id = {day}')

    if green_x > blue_x: #determine if the right or left side of the green image should be cropped (opposite side of blue is cropped)
        green_crop_xstart = max_xdim - xdim #crop the left off the green image
        blue_crop_xend = xdim #crop the right off the blue image
        edit_database(f'Update cube_offset Set green_crop_xstart = {green_crop_xstart}, blue_crop_xend = {blue_crop_xend} Where date_id = {day}')
    elif green_x < blue_x:
        green_crop_xend = xdim #crop the right off the green image
        blue_crop_xstart = max_xdim - xdim #crop the left off the blue image
        edit_database(f'Update cube_offset Set green_crop_xend = {green_crop_xend}, blue_crop_xstart = {blue_crop_xstart} Where date_id = {day}')