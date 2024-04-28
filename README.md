## obs3dian
Easy image controller for obsidian. Change internal file links to external S3 links.
Obs3dian converts local image file path to external url by uploading file in S3.

obs3dian converts image link text to external link.

`![](./test.png)`

will change to

`![](https://YOUR_BUCKET.s3.YOUR_REGION.amazonaws.com/test.png)`

obs3dian allows alt option or size options like

`![[test.jpeg|500]]`

`![this is caption](test.gif)`

and it also can converts image links used in obsidain

`![[test.jpg|500]]`


## Installation

<div class="termy">

```console
$ pip install obs3dian
```
</div>

## Requirements
* python > 3.10
* AWS accounts with permissions to
  * create bucket
  * put image
  * set bucket public

### Commands

<div class="termy">

```console
$ obs3dian config

Config file is not founded... Input your configuration

AWS Profile Name [your aws profile]: 
S3 bucket Name [your bucket name]: 
Output Path [your ouput path]: 
Image Folder Path [your local image folder path]:

```
</div>

<div class="termy">

```console
$ obs3dian apply

Connected to AWS S3
Bucket obs3dian is created
Create Output Folder in ./ouput
```

</div>

<div class="termy">

```console
$ obs3dian run [your mark down path (file or directory)]

Processing  [############################--------]   78%
Finished    [README.md]

Processing  [#############################-------]   82%
Finished    [CONTRIBUTING.md]

Processing  [###############################-----]   86%
Finished    [LINKS.md] 

Processing  [################################----]   91%
Finished    [SUPPORTED_PLATFORMS.md]

Processing  [##################################--]   95%
Finished    [ISSUE_TEMPLATE.md]

Processing  [####################################]  100%

Total converts: 23 obs3dian is successfully finished
```

</div>

`run` command got options 

* `--overwrite` will overwrites all markdown files and not create output files under output folder.
* `--usekey` forces obs3dian to use access key when connects to S3. In default obs3dian using CLI profile in connection.


You can get more info by --help option

<div class="termy">

```console
$ obs3dian --help
$ obs3dian run --help
$ obs3dian apply --help
```

</div>

## How it works
*  `obs3dian` reads config data to set enviroment
   *  It creates S3 public read bucket by your aws account info
   *  It creates output folder
* `obs3dian` reads markdown files in given path
    * It also reads all .md files under subdir
* `obs3dian` extracts all image names used in markdown and finds matching paths with names from given image folder
* upload mathced images
* Replace local image links to S3 external links


## Info
* `obs3dian` converts all *.md files under input path.
  * If given path is dir then dir/*.md, dir/subdir/*.md is all converted.
* Created Bucket is public read.
* `run` command automatically executes apply before run
* `obs3dian` uses AWS CLI profile first. If you want to use access key pleas give `--usekey` when run.
* obs3dian only supports `.png, .jpg, .jpeg, .gif` type images.
