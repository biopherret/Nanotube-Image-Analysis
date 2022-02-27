import os

#assumes the following path format
#\Nanotube Image Analysis
#   this file.py
#   \Images
#       \Date1
#       \Date2
#           \images folder
#           \another images folder
#               \RGB Stacks jpg
#                   image 1
#                   image 2

#change and get current working directory (cwd)
os.chdir('{}\Images\{}'.format(os.getcwd(), input('Input the name of the image day folder: ')))
cwd = os.getcwd()

base_folders = os.listdir(cwd)

for folder in base_folders:
    #get list of image file names
    image_files = (os.listdir('{}\{}'.format(cwd, folder)))
    #make a new directory
    os.mkdir('{}\{}\RAW'.format(cwd, folder))
    for image_file_name in image_files:
        os.rename('{}\{}\{}'.format(cwd, folder, image_file_name), '{}\{}\RAW\{}'.format(cwd, folder, image_file_name))