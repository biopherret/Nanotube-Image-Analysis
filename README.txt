All scripts in this repo are expecting the following folder structure:

add_scale_bap.py
move_images_to_raw.py
nanotube_finder_SEs_only.py
nanotube_finder.py
RGB_stacker.m
sarah_plt_style.mplstyle
Images (folder)
----> date1
----> date2
--------> folder with images 1
--------> folder with images 2

For RGB stacker and nanotube_finder, the scripts expect each folder with images to have a RAW folder containing the raw images. Use move_images_to_raw.py to setup this structure.
(Run move_images_to_raw.py and enter the date of the folder). After the folder structure will look like this:

Images (folder)
----> date1
----> date2
--------> folder 1
------------> RAW
--------> folder 2
------------> RAW

Then when you run RGB stacker or nanotube finder more directories will be added like this

Images (folder)
----> date1
----> date2
--------> folder 1
------------> RAW
------------> RGB Stackts tif
------------> RGB Stackts jpg
------------> Nanotube Finder Results
--------> folder 2
------------> RAW
------------> RGB Stackts tif
------------> RGB Stackts jpg
------------> Nanotube Finder Results

For add_scale_bar.py you need to give the entire path name to the folder you want to add scale bars too (this allows you to add scale bars to any image folder, not just the RAW folder)

For all python files, start the script as you normally would. (you will need either python or anaconda installed)

For RGB_stacker.m run this command in your terminal after navigating to the working directory: wolframscript -file '.\RGB_stacker.m' (I *think* you need mathmatica installed for this to work)