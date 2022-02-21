(*Input the name of the folder containing Images*)
CurrentDirecName = Directory[]

(*Get the working directory via input
Expect the current directory to have a directory named Images, which contaiens a folder for each image day(which should be inputed), containing a bunch of folders*)
MainDirec = SetDirectory[Directory[] <> "\\Images\\" <> ToString[Input["Input the directory path to folder of images to anylyze from the Images folder: "]]];

(*Find folders in the current directory*)
Folders = Flatten[FileNames[All, MainDirec]]
NumFolders = Length[Folders]

(*Make sure images taken under green fluorescence have "green" in their file name,same for blue fluorescence First part of the file name for images to be grouped must be the same so images get paired properly*)
BlueFiles = ParallelTable[Flatten[Select[FileNames["*blue*", Folders[[i]]], StringMatchQ[#, __ ~~ "tif"] &]], {i, NumFolders}]
GreenFiles = ParallelTable[Flatten[Select[FileNames["*green*", Folders[[i]]], StringMatchQ[#, __ ~~ "tif"] &]], {i, NumFolders}]
NumImages = ParallelTable[Length[BlueFiles[[i]]], {i, NumFolders}]

(*Get the Image file names, without color to use to name final stacked images*)
ImageFileNames = ParallelTable[Flatten[FileNames[All, Folders[[i]]]], {i, NumFolders}]
ImageBaseFileNames = ParallelTable[StringDelete[FileBaseName[ImageFileNames[[i, j]]], " blue"], {i, NumFolders}, {j, 1, NumImages[[i]] * 2, 2}]

(*Increase contrast and crop both blue and green images 
Crop is necessary b/c images in blue and green are offset slightly 
Brightness increase value is different between images b/c blue imaging takes brighter images*)
BlueNanotubeImages = ParallelTable[ImageCrop[Import[BlueFiles[[i, j]]]*400, {1354, 1030}, {Right, Top}], {i, NumFolders}, {j, NumImages[[i]]}]
GreenNanotubeImages = ParallelTable[ImageCrop[Import[GreenFiles[[i, j]]]*250, {1354, 1030}, {Left, Bottom}], {i, NumFolders}, {j, NumImages[[i]]}]

(*RBG stack green and blue fluorescence images*)
ColorNanotubeImages = ParallelTable[ImageAdjust[ColorCombine[{GreenNanotubeImages[[i, j]], BlueNanotubeImages[[i, j]], BlueNanotubeImages[[i, j]] }, "RGB"], 1.8], {i, NumFolders}, {j, NumImages[[i]]}]

(*Move RAW images to new RAW folder*)
ParallelTable[CreateDirectory[Folders[[i]] <> "\\RAW"], {i, NumFolders}]
ParallelTable[CopyFile[BlueFiles[[i, j]], Folders[[i]] <> "\\RAW\\" <> ImageBaseFileNames[[i, j]] <> " blue.tif"], {i, NumFolders}, {j, NumImages[[i]]}]
ParallelTable[CopyFile[GreenFiles[[i, j]], Folders[[i]] <> "\\RAW\\" <> ImageBaseFileNames[[i, j]] <> " green.tif"], {i, NumFolders}, {j, NumImages[[i]]}]
ParallelTable[DeleteFile[Folders[[i]] <> "\\" <> ImageBaseFileNames[[i, j]] <> " blue.tif"], {i, NumFolders}, {j, NumImages[[i]]}]
ParallelTable[DeleteFile[Folders[[i]] <> "\\" <> ImageBaseFileNames[[i, j]] <> " green.tif"], {i, NumFolders}, {j, NumImages[[i]]}]

(*Export color images to the RGB Stacks Folders as tif and jpg*)
ParallelTable[CreateDirectory[Folders[[i]] <> "\\RGB Stacks tif"], {i, NumFolders}]
ParallelTable[CreateDirectory[Folders[[i]] <> "\\RGB Stacks jpg"], {i, NumFolders}]
ParallelTable[Export[Folders[[i]] <> "\\RGB Stacks tif\\" <> ImageBaseFileNames[[i, j]] <> ".tif", ColorNanotubeImages[[i, j]]], {i, NumFolders}, {j, NumImages[[i]]}]
ParallelTable[Export[Folders[[i]] <> "\\RGB Stacks jpg\\" <> ImageBaseFileNames[[i, j]] <> ".jpg", ColorNanotubeImages[[i, j]]], {i, NumFolders}, {j, NumImages[[i]]}]