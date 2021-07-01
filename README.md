# WADs Out For [The] Ladies
Simple Python / ImageMagick script to package images into WAD3s for use as GoldSrc textures. 

Development mostly focused on Linux, where a native WAD file creator is MIA. 

# Usage
`wofl input1 [input2 ...] output`
* `input1 [input2 ...]` are the input images
* `output` is the output WAD filename
## Example
```
$ ./wofl.py pictures/file.jpg my_wad.wad
$ echo $?
0 # success
```

# Requirements
* ImageMagick (its executables have to be in the system `PATH`)

<p align="center">
  <img width="500px" src="assets/wofl.jpg">
</p>
