import pandas as pd
import numpy as np
from sqlalchemy.engine import URL
from sqlalchemy import create_engine
import sqlalchemy as sa
import pyodbc
import os

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

date_key = int(input('Input the image date to prep the SQL Server for: '))

os.chdir('{}\Images\{}'.format(os.getcwd(), str(date_key))) #change the current working directory
cwd = os.getcwd()
base_folders = os.listdir(cwd) #find the folder names

nanotube_sample_df = run_quary('Select * From nanotube_sample').set_index('nanotube_sample_id') #retrieve current nanotube_sample and slide_sample tables
slide_sample_df = run_quary('Select * From slide_sample').set_index('slide_sample_id')
cube_offset_df = run_quary('Select * From cube_offset').set_index('date_id')

if date_key not in cube_offset_df.index.values.tolist(): #if you have not yet added the cube offset data for this imaging day
    if input('Would you like to add cube offset points for this imaging day? (yes/no) ') == 'yes':
        last_imaging_date = max([i for i in cube_offset_df.index.values.tolist() if i < date_key])
        if input(f'Has the offset changed since the list imaging day ({max(cube_offset_df.index.values.tolist())})? (yes/no) ') == 'yes':
            print('Find a the x,y points of an objects which exists in both green and blue images')
            green_x = input('    Green x: ')
            green_y = input('    Green y: ')
            blue_x = input('    Blue x: ')
            blue_y = input('    Blue y: ')
            
        else: 
            green_x = cube_offset_df.loc[last_imaging_date]['green_x']
            green_y = cube_offset_df.loc[last_imaging_date]['green_y']
            blue_x = cube_offset_df.loc[last_imaging_date]['blue_x']
            blue_y = cube_offset_df.loc[last_imaging_date]['blue_y']
        
        edit_database(f'Insert Into nanotube_sample (date_id , green_x, green_y, blue_x, blue_y) Values ({date_key}, {green_x}, {green_y}, {blue_x}, {blue_y})') #add new offset points to the database

unique_key_index = 0 
for folder_name in base_folders:
    slide_sample_id = f'{date_key}{unique_key_index:02}' #slide sample key (unique) is the folder date and a 2 digit number
    unique_key_index += 1
    
    if int(slide_sample_id) in slide_sample_df.index.values.tolist(): #if the slide sample has already been added, skip it
        print(f'{folder_name} has already been added to the SQL Server')
        continue

    print(f'Input data for the following slide: {folder_name}')
    nanotube_sample_id = int(input('    Nanotube Sample Id: '))
    channel_num = int(input('    1-channel or 2-channel?: '))
    is_stack = int(input('    Is this a folder of movies?(1 for yes, 0 for no): '))
    total_slide_uL = float(input('    What is the total volume on the slide(uL)?: '))
    uL_sample = float(input('    How much sample is on the slide(uL)?: '))   

    edit_database(f"Insert Into slide_sample Values ({slide_sample_id}, {nanotube_sample_id}, {channel_num}, {is_stack}, {date_key}, '{folder_name}', {total_slide_uL}, {uL_sample});") #add the slide to the slide_sample table

    if nanotube_sample_id not in nanotube_sample_df.index.values.tolist(): #if the nanotube sample used for this slide has not yet been added
        print('This nanotube sample has not yet been added to the SQL Server')
        print(f'Input data for the following nanotube sample: {nanotube_sample_id}')
        seed_sample_id = int(input('    What is the seed sample ID?(0 if no seed added): '))
        if seed_sample_id == 0: #if no seed was added
            uL_seed_added = 0
            anneal_seed_concentration = 0
        else:
            uL_seed_added = float(input('    How much seed was added to the anneal(uL)?: '))
            anneal_seed_concentration = np.array(run_quary(f'Select molarity_avg From seed_sample Where seed_sample_id = {seed_sample_id}')).flatten()[0] * uL_seed_added / 25

        edit_database(f'Insert Into nanotube_sample Values ({nanotube_sample_id}, {seed_sample_id}, {uL_seed_added}, {anneal_seed_concentration})') #add this nanotube_sample to nanotube_sample table