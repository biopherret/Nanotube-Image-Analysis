(*Get the working directory via input
Expect the current directory to have a directory named Images, which contaiens a folder for each image day(which should be inputed), containing a bunch of folders*)
MainDirec = SetDirectory[Directory[] <> "\\Images\\" <> ToString[Input["Input the directory path to folder of images to anylyze from the Images folder: "]]];
ImageTypes = {"green", "blue"}

Print["Loading Files..."]
(*Find folders in the current directory*)
BaseFolders = Flatten[FileNames[All, MainDirec]]
NumFolders = Length[BaseFolders]
Folders = ParallelTable[BaseFolders[[i]] <> "\\RAW", {i, NumFolders}]

(*Make sure images taken under green fluorescence have "green" in their file name,same for blue fluorescence First part of the file name for images to be grouped must be the same so images get paired properly*)
Files = <|
    "green" -> ParallelTable[Flatten[Select[FileNames["*green*", Folders[[i]]], StringMatchQ[#, __ ~~ "tif"] &]], {i, NumFolders}],
    "blue" -> ParallelTable[Flatten[Select[FileNames["*blue*", Folders[[i]]], StringMatchQ[#, __ ~~ "tif"] &]], {i, NumFolders}]
|>
NumImages = ParallelTable[Length[BlueFiles[[i]]], {i, NumFolders}]

Print["Increacing contrast and croping images..."]
(*Increase contrast and crop both blue and green images 
Crop is necessary b/c images in blue and green are offset slightly 
Brightness increase value is different between images b/c blue imaging takes brighter images*)
Images = <|
    "green" -> ParallelTable[ImageCrop[Import[Files[["green", i, j]]]*250, {1354, 1030}, {Left, Bottom}], {i, NumFolders}, {j, NumImages[[i]]}],
    "blue" -> ParallelTable[ImageCrop[Import[Files[["blue", i, j]]]*400, {1354, 1030}, {Right, Top}], {i, NumFolders}, {j, NumImages[[i]]}]
|>

Print["Binarizing images..."]
TubeBinary = (ParallelTable[DeleteBorderComponents[Binarize[#[[i, j]], {0.4, 1}]], {i, NumFolders}, {j, NumImages[[i]]}]) &/@ Images

Print["Finding nanotubes..."]
NTFind = (ParallelTable[ComponentMeasurements[TubeBinary[[i, j]], {"BoundingBox"}, 240 < #Area  < 2000 &], {i, NumFolders}, {j, NumImages[[i]]}]) &/@ TubeBinary

Print["Adding highlights to the original color images..."]
HighlightNT = (ParallelTable[HighlightImage[Images[[i, j]], Rectangle @@@ #[[i, j, All, 1]]], {i, NumFolders}, {j, NumImages[[i]]}]) &/@ NTFind

(*Get the Image file names, without color to use to name final stacked images*)
ImageFileNames = ParallelTable[Flatten[FileNames[All, Folders[[i]]]], {i, NumFolders}]
ImageBaseFileNames = ParallelTable[StringDelete[FileBaseName[ImageFileNames[[i, j]]], " blue"], {i, NumFolders}, {j, 1, NumImages[[i]] * 2, 2}]

Print["Exporting highlighted images as jpgs..."]
ParallelTable[Quiet[CreateDirectory[BaseFolders[[i]] <> "\\Highlited Color Nanotubes"]], {i, NumFolders}]
Table[Export[BaseFolders[[i]] <> "\\Highlited Color Nanotubes\\" <> ImageBaseFileNames[[i, j]] <> " " <> type <> ".jpg", HighlightNT[[type, i, j]]], {type, ImageTypes}, {i, NumFolders}, {j, NumImages[[i]]}]

Print["Exporting nanotube location data in excel"]
Data = <|"green" -> {}, "blue" -> {}|>
Table[Data[[type]] = Append[Data[[type]], {}], {type, ImageTypes}, {i, NumFolders}]
Table[Quiet[Data[[type, i]] = Append[Data[[type, i]], ImageBaseFileNames[[i,j]] -> Prepend[Transpose[{
    NTFind[[type, i, j, All, 1, 1, 1]], (*bottom left x pos*)
    NTFind[[type, i, j, All, 1, 1, 2]], (*bottom left y pos*)
    NTFind[[type, i, j, All, 1, 2, 1]], (*top right x pos*)
    NTFind[[type, i, j, All, 1, 2, 2]] (*top right y pos*)
}], {"bottom left x pos", "bottom left y pos", "top right x pos", "top right y pos"}]]], {type, ImageTypes}, {i, NumFolders}, {j, NumImages[[i]]}]
Table[Export[BaseFolders[[i]] <> "\\Location Data "  <> type <> ".xls", Data[[type, i]]], {type, ImageTypes}, {i, NumFolders}]