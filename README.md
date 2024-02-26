## obs3dian
Easy image controller for obsidian. Change internal file links to external S3 links.
Obs3dian converts local image file path to external url by uploading file in S3.

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
Image Folder Path [your image path]:

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

You can get more info by --help option

<div class="termy">

```console
$ obs3dian --help
```

</div>

## Info
* Obs3dian converts all *.md files contain input path.
  * If given path is dir then dir/*.md, dir/subdir/*.md is all converted.
* Created Bucket is public read.
* run command automatically executes apply before run

