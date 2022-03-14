SetOptions[$Output, FormatType -> OutputForm]
SetSharedFunction[Print]
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

Print["Separating images into 3 main colors and binarizing..."] (*Threholding happens at 50% gray level*)
TubeBinary = <|
    "full" -> ParallelTable[Binarize[ImageData /@ ColorDistance[ColorImages[[i, j]], RGBColor[0.22, 0.22, 0.22]], {0.5, 1}], {i, NumFolders}, {j, NumImages[[i]]}],
    "green" -> ParallelTable[Binarize[ColorNegate[ImageData /@ ColorDistance[ColorImages[[i, j]], RGBColor[1, 0.22, 0.22]]], {0.5, 1}], {i, NumFolders}, {j, NumImages[[i]]}],
    "blue" -> ParallelTable[Binarize[ColorNegate[ImageData /@ ColorDistance[ColorImages[[i, j]], RGBColor[1, 1, 1]]], {0.5, 1}], {i, NumFolders}, {j, NumImages[[i]]}]
|>

Print["Finding nanotubes in each binarized image..."]
NTFind = (ParallelTable[Values[ComponentMeasurements[#[[i, j]], {"BoundingBox", "Count"}, 200 < #Area  < 2000 &]], {i, NumFolders}, {j, NumImages[[i]]}]) &/@ TubeBinary

Print["Adding highlights to the original color images..."]
HighlightNT = (ParallelTable[HighlightImage[ColorImages[[i, j]], Rectangle @@@ #[[i, j, All, 1]]], {i, NumFolders}, {j, NumImages[[i]]}]) &/@ NTFind

(*Get the Image file names, without color to use to name final images*)
ImageFileNames = ParallelTable[Flatten[FileNames[All, StacksFolders[[i]]]], {i, NumFolders}]
ImageBaseFileNames = ParallelTable[FileBaseName[ImageFileNames[[i, j]]], {i, NumFolders}, {j, NumImages[[i]]}]

Print["Exporting highlighted images as jpgs..."]
ParallelTable[Quiet[CreateDirectory[BaseFolders[[i]] <> "\\Highlited Color Nanotubes"]], {i, NumFolders}]
TotalImages = Sum[NumImages[[i]], {i, NumFolders}] * 3
Progress[x_] = N[x/TotalImages, 2]*100
counter = 0
SetSharedVariable[counter]
Table[Export[BaseFolders[[i]] <> "\\Highlited Color Nanotubes\\" <> ImageBaseFileNames[[i, j]] <> " " <> type <> ".jpg", HighlightNT[[type, i, j]]]; counter += 1; If[Mod[counter, 10] == 0, Print[ToString[Progress[counter]] <> "% of images exported"]], {type, ImageTypes}, {i, NumFolders}, {j, NumImages[[i]]}]

Print["Exporting nanotube location data in excel..."]
ParallelTable[Quiet[CreateDirectory[BaseFolders[[i]] <> "\\Location Data"]], {i, NumFolders}]
Data = <|"full" -> {}, "green" -> {}, "blue" -> {}|>
Table[Data[[type]] = Append[Data[[type]], {}], {type, ImageTypes}, {i, NumFolders}]
Table[Quiet[Data[[type, i]] = Append[Data[[type, i]], ImageBaseFileNames[[i,j]] -> Prepend[Transpose[{
    NTFind[[type, i, j, All, 1, 1, 1]], (*bottom left x pos*)
    NTFind[[type, i, j, All, 1, 1, 2]], (*bottom left y pos*)
    NTFind[[type, i, j, All, 1, 2, 1]], (*top right x pos*)
    NTFind[[type, i, j, All, 1, 2, 2]], (*top right y pos*)
    NTFind[[type, i, j, All, 2]] (*pixel count*)
}], {"bottom left x pos", "bottom left y pos", "top right x pos", "top right y pos", "pixel count"}]]], {type, ImageTypes}, {i, NumFolders}, {j, NumImages[[i]]}]
Table[Export[BaseFolders[[i]] <> "\\Location Data\\Location Data "  <> type <> ".xls", Data[[type, i]]], {type, ImageTypes}, {i, NumFolders}]