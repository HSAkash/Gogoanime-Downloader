# Gogoanime Downloader

## Features
* Single episode download
* Multiple episode download
* check already downloaded

## Setup
Install python3 any version.[website](https://www.python.org/)
### Clone repository
```
git clone git@github.com:HSAkash/Gogoanime-Downloader.git
```
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
|
</pre>

## Setup .env file
gogoanime, auth get from browser cookie.
<p>
<img src='pic/gogoanime.png'/>
<p>
After geting the session variable then you can use the following steps to set the session.
Go to the Gogoanime class and header_setup function and configure the session.

```
gogoanime=gogoanime #your gogoanime session 
auth=HSAkash #your gogoanime session 
```

# Run the command
```
python gogoanime.py -h
```
```
usage: test.py [-h] [-s START] [-e END] [-q QUALITY] [-d DESTINATION] [--yes-playlist] url

Description of program

positional arguments:
  url                   Url of the anime

options:
  -h, --help            show this help message and exit
  -s START, --start START
                        start episode
  -e END, --end END     end episode
  -q QUALITY, --quality QUALITY
                        video quality
  -d DESTINATION, --destination DESTINATION
                        destination folder
  -w WORKERS, --workers WORKERS
                        Number of workers
  --yes-playlist        For playlist download
```
