(*Get the working directory via input
Expect the current directory to have a directory named Images, which contaiens a folder for each image day(which should be inputed), containing a bunch of folders*)
MainDirec = SetDirectory[Directory[] <> "\\Images\\" <> ToString[Input["Input the directory path to folder of images to anylyze from the Images folder: "]]];

Print["Loading Files..."]
(*Find folders in the current directory*)
BaseFolders = Flatten[FileNames[All, MainDirec]]
NumFolders = Length[BaseFolders]
RAWFolders = ParallelTable[BaseFolders[[i]] <> "\\RAW", {i, NumFolders}]
(*Make sure images taken under green fluorescence have "green" in their file name,same for blue fluorescence First part of the file name for images to be grouped must be the same so images get paired properly*)
Files = <|
    "green" -> ParallelTable[Flatten[Select[FileNames["*green*", RAWFolders[[i]]], StringMatchQ[#, __ ~~ "tif"] &]], {i, NumFolders}],
    "blue" -> ParallelTable[Flatten[Select[FileNames["*blue*", RAWFolders[[i]]], StringMatchQ[#, __ ~~ "tif"] &]], {i, NumFolders}]
|>
NumImages = ParallelTable[Length[Files[["green", i]]], {i, NumFolders}] (*there should be an equal number of blue files as green files*)

(*Get the Image file names, without color to use to name final stacked images*)
ImageFileNames = ParallelTable[Flatten[FileNames[All, RAWFolders[[i]]]], {i, NumFolders}]
ImageBaseFileNames = ParallelTable[StringDelete[FileBaseName[ImageFileNames[[i, j]]], " blue"], {i, NumFolders}, {j, 1, NumImages[[i]] * 2, 2}]

Print["Increacing contrast and croping images..."]
(*Increase contrast and crop both blue and green images 
Crop is necessary b/c images in blue and green are offset slightly 
Brightness increase value is different between images b/c blue imaging takes brighter images*)
(*250, 400*)
UnModImages = <|
    "green" -> ParallelTable[Import[Files[["green", i, j]]], {i, NumFolders}, {j, NumImages[[i]]}],
    "blue" -> ParallelTable[Import[Files[["blue", i, j]]], {i, NumFolders}, {j, NumImages[[i]]}]
|>
MedianPixelValues = (ParallelTable[ImageMeasurements[#[[i]], "Median"], {i, NumFolders}]) &/@ UnModImages

(*0.4/Median brightness adjust sets the background image brighness to 0.4 for both images*)
Images = <|
    "green" -> ParallelTable[ImageCrop[UnModImages[["green", i, j]]*(0.4/MedianPixelValues[["green", i, j]]), {1354, 1030}, {Left, Bottom}], {i, NumFolders}, {j, NumImages[[i]]}],
    "blue" -> ParallelTable[ImageCrop[UnModImages[["blue", i, j]]*(0.4/MedianPixelValues[["blue", i, j]]), {1354, 1030}, {Right, Top}], {i, NumFolders}, {j, NumImages[[i]]}]
|>

Print["Creating composit images..."]
(*RBG stack green and blue fluorescence images 
green image in the red channel, blue image in the green and blue channel
increase contrast after combining the images*)
ColorImages = ParallelTable[ImageAdjust[ColorCombine[{Images[["green", i, j]], Images[["blue", i, j]], Images[["blue", i, j]]}, "RGB"], 1.8], {i, NumFolders}, {j, NumImages[[i]]}]

Print["Exporting color images as tifs and jpgs..."]
(*Export color images to the RGB Stacks Folders as tif and jpg*)
ParallelTable[Quiet[CreateDirectory[BaseFolders[[i]] <> "\\RGB Stacks tif"]], {i, NumFolders}]
ParallelTable[Quiet[CreateDirectory[BaseFolders[[i]] <> "\\RGB Stacks jpg"]], {i, NumFolders}]
ParallelTable[Export[BaseFolders[[i]] <> "\\RGB Stacks tif\\" <> ImageBaseFileNames[[i, j]] <> ".tif", ColorImages[[i, j]]], {i, NumFolders}, {j, NumImages[[i]]}]
ParallelTable[Export[BaseFolders[[i]] <> "\\RGB Stacks jpg\\" <> ImageBaseFileNames[[i, j]] <> ".jpg", ColorImages[[i, j]]], {i, NumFolders}, {j, NumImages[[i]]}]