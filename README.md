# Gogoanime Downloader

## Features
* Single episode download
* Multiple episode download
* Resumeable

## Setup
Install python3 any version.[website](https://www.python.org/)
### Create environment
```
python -m venv env
```
activate environment `Linux`
```
source env/bin/activate
```
activate environment `Windows`
```
env/Scripts/activate.bat
```
### Install dependencies
```
pip install -r requirements.txt
```

## Directories
<pre>
│  
├─gogoanime.py
│
├─.env
|
</pre>

## Setup .env file
gogoanime, auth get from browser cookie.
<p>
<img src='pic/gogoanime.png' width="600" height="350"/>
<p>
After geting the environment variable then you can use the following steps to set the environment.
Go to the .env file and configure the environment
```
gogoanime=gogoanime
auth=HSAkash
```

# Run the command
```
python gogoanime.py
```
details:
Anime url: anime url from gogoanime site.
Video Quality: 360, 480, 720, 1080
Download Type:
    1. Single Episode/ Video
    2. Multiple Episodes/ Videos 

Episode from : Starting from
Episode to : Ending Episode