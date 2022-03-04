(*Get the working directory via input
Expect the current directory to have a directory named Images, which contaiens a folder for each image day(which should be inputed), containing a bunch of folders*)
MainDirec = SetDirectory[Directory[] <> "\\Images\\" <> ToString[Input["Input the directory path to folder of images to anylyze from the Images folder: "]]];
ImageTypes = {"full", "green", "blue"}

Print["Loading Files..."]
(*Find folders in the current directory*)
BaseFolders = Flatten[FileNames[All, MainDirec]]
NumFolders = Length[BaseFolders]
StacksFolders = ParallelTable[BaseFolders[[i]] <> "\\RGB Stacks tif", {i, NumFolders}]

ColorFiles = ParallelTable[Flatten[Select[FileNames[All, StacksFolders[[i]]], StringMatchQ[#, __ ~~ "tif"] &]], {i, NumFolders}]
NumImages = ParallelTable[Length[ColorFiles[[i]]], {i, NumFolders}]

ColorImages = ParallelTable[Import[ColorFiles[[i, j]]], {i, NumFolders}, {j, NumImages[[i]]}];

Print["Separating images into 3 main colors and binarizing..."] (*Threholding happens at 40% gray level*)
TubeBinary = <|
    "full" -> ParallelTable[Binarize[ImageData /@ ColorDistance[ColorImages[[i, j]], RGBColor[0.3, 0.3, 0.3]], {0.4, 1}], {i, NumFolders}, {j, NumImages[[i]]}],
    "green" -> ParallelTable[Binarize[ColorNegate[ImageData /@ ColorDistance[ColorImages[[i, j]], RGBColor[1, 0.3, 0.3]]], {0.4, 1}], {i, NumFolders}, {j, NumImages[[i]]}],
    "blue" -> ParallelTable[Binarize[ColorNegate[ImageData /@ ColorDistance[ColorImages[[i, j]], RGBColor[1, 1, 1]]], {0.4, 1}], {i, NumFolders}, {j, NumImages[[i]]}]
|>

Print["Finding nanotubes in each binarized image..."]
NTFind = (ParallelTable[Values[ComponentMeasurements[#[[i, j]], {"BoundingBox"}, 240 < #Area  < 2000 &]], {i, NumFolders}, {j, NumImages[[i]]}]) &/@ TubeBinary
(*NTFind objcts: {{{lower left x pos, lower left y pos},{upper right x pos, upper left y pos}},{center x pos, center y, pos}}*)

Print["Adding highlights to the original color images..."]
HighlightNT = (ParallelTable[HighlightImage[ColorImages[[i, j]], Rectangle @@@ #[[i, j, All, 1]]], {i, NumFolders}, {j, NumImages[[i]]}]) &/@ NTFind

(*Get the Image file names, without color to use to name final images*)
ImageFileNames = ParallelTable[Flatten[FileNames[All, StacksFolders[[i]]]], {i, NumFolders}]
ImageBaseFileNames = ParallelTable[FileBaseName[ImageFileNames[[i, j]]], {i, NumFolders}, {j, NumImages[[i]]}]

Print["Exporting highlighted images as jpgs..."]
ParallelTable[Quiet[CreateDirectory[BaseFolders[[i]] <> "\\Highlited Color Nanotubes"]], {i, NumFolders}]
Table[Export[BaseFolders[[i]] <> "\\Highlited Color Nanotubes\\" <> ImageBaseFileNames[[i, j]] <> " " <> type <> ".jpg", HighlightNT[[type, i, j]]], {type, ImageTypes}, {i, NumFolders}, {j, NumImages[[i]]}]

Print["Exporting nanotube location data in excel"]
Data = <|"full" -> {}, "green" -> {}, "blue" -> {}|>
Table[Data[[type]] = Append[Data[[type]], {}], {type, ImageTypes}, {i, NumFolders}]
Table[Quiet[Data[[type, i]] = Append[Data[[type, i]], ImageBaseFileNames[[i,j]] -> Prepend[Transpose[{
    NTFind[[type, i, j, All, 1, 1, 1]], (*bottom left x pos*)
    NTFind[[type, i, j, All, 1, 1, 2]], (*bottom left y pos*)
    NTFind[[type, i, j, All, 1, 2, 1]], (*top right x pos*)
    NTFind[[type, i, j, All, 1, 2, 2]] (*top right y pos*)
}], {"bottom left x pos", "bottom left y pos", "top right x pos", "top right y pos"}]]], {type, ImageTypes}, {i, NumFolders}, {j, NumImages[[i]]}]
Table[Export[BaseFolders[[i]] <> "\\Location Data "  <> type <> ".xls", Data[[type, i]]], {type, ImageTypes}, {i, NumFolders}]
