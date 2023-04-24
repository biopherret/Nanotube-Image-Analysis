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

for day in cube_offset_df.index.values.tolist():
    green_x = cube_offset_df.loc[day]['green_x']
    green_y = cube_offset_df.loc[day]['green_y']
    blue_x = cube_offset_df.loc[day]['blue_x']
    blue_y = cube_offset_df.loc[day]['blue_y']

    if green_x >= blue_x: #determine if the right or left side of the green image should be cropped (opposite side of blue is cropped)
        x_green_dir = 'left'
    else:
        x_green_dir = 'right'

    if green_y <= blue_y: #determine if the bottom or top side of the green image should be cropped (opposite side of blue is cropped)
        y_green_dir = 'bottom'
    else:
        y_green_dir = 'top'
    
    ydim = int(1040 - np.abs(green_y - blue_y)) #determine how much to crop in each dimension
    xdim = int(1376 - np.abs(green_x - blue_x))

    edit_database(f"Update cube_offset Set ydim = {ydim}, xdim = {xdim}, x_green_dir = '{x_green_dir}', y_green_dir = '{y_green_dir}' Where date_id = {day};") #update the SQL database