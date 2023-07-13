import os
import sys
import time
import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from tkinter import messagebox
import argparse

from urllib.parse import urlparse
import threading
# Termination condition
terminate = threading.Event()



def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False
    
def is_valid_anime_url(url):
    response = requests.get(url)
    bs4_object = BeautifulSoup(response.content, 'html.parser')
    result = bs4_object.find_all('h1', class_='entry-title')
    if result:
        return result[0].text != 'Error 404'
    return True

def get_last_episode(url):
    response = requests.get(url)
    bs4_object = BeautifulSoup(response.content, 'html.parser')
    last_episode = bs4_object.find_all('ul', id='episode_page')[0].find_all('a')[-1].text.strip().split('-')[-1]
    return last_episode

def get_next_episode(url):
    response = requests.get(url)
    bs4_object = BeautifulSoup(response.content, 'html.parser')
    next_episode = bs4_object.find_all('div', class_='anime_video_body_episodes_r')[0].find_all('a')
    if bs4_object:
        return next_episode[0].attrs['href']
    return
    





class Gogoanime:
    def __init__(self, max_workers=6):
        self.header_setup()
        self.max_workers = max_workers

    def header_setup(self):
        """
        Geting download url user must have gogoanime cookie and auth cookie.
        Which is stored in .env file.
        gogoanime, auth get from browser cookie.
        """
        gogoanime="bbm4c1ohjm90oc"
        auth="rtqbS1Vd%2FNRVlFpRP0N5ZoobhgSFViluOY1SVnGPJjU%3D%3D"
        User_Agent = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/112.0"
        Accept = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
        self.headers = requests.utils.default_headers()
        self.headers.update(
            {
                'Cookie': f'gogoanime={gogoanime}; auth={auth}',
                'User-Agent': User_Agent,
                'Accept': Accept,
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate'
            }
        )

    def get_download_link_dict(self, response):
        """
        Get all download links quality wise.
        """
        link_dict = {}
        bs4_object = BeautifulSoup(response.content, 'html.parser')
        links = bs4_object.find_all('div', class_='list_dowload')[0].find_all('a')
        for link in links:
            key = link.text.strip().split('x')[-1]
            link_dict[key] = link['href']
        return link_dict
    
    def get_download_url(self, link_dict, quality='1080'):
        if quality not in link_dict:
            """
            if quality not found, then get the last quality
            means the highest quality.
            """
            keys = link_dict.keys()
            if keys:
                quality = list(keys)[-1]
            else:
                raise Exception(f'Quality {quality} not found.')
        link = link_dict[quality]
        response = requests.head(link)
        if response.headers.get('Location'):
            return response.headers.get('Location') , quality

    
    def download(self, url, fileName):

        chunk_size = 1024 * 1024  # 1MB chunks

        # Get the total file size
        response = requests.head(url)
        total_size = int(response.headers.get('Content-Length', 0))

        # Check if the file was partially downloaded
        file_size = 0
        if os.path.exists(fileName):
            file_size = os.path.getsize(fileName)
        if file_size > 0:
            headers = {'Range': f'bytes={file_size}-'}
            response = requests.get(url, headers=headers, stream=True)
            mode = 'ab'
        else:
            response = requests.get(url, stream=True)
            mode = 'wb'

        # Download the file with progress bar and simultaneous requests
        print(f"{fileName}")
        with open(fileName, mode) as file, \
                tqdm(total=total_size, unit='iB', unit_scale=True, unit_divisor=1024, initial=file_size) as progress_bar, \
                ThreadPoolExecutor(max_workers=self.max_workers) as executor:

            # Initialize the futures list
            self.futures = []

            # Create a function to download chunks
            def download_chunk(start, end):
                headers = {'Range': f'bytes={start}-{end}'}
                response = requests.get(url, headers=headers, stream=True)
                chunk_list = []
                for chunk in response.iter_content(chunk_size=chunk_size):
                    chunk_list.append(chunk)
                file.seek(start)
                for chunk in chunk_list:
                    file.write(chunk)
                    progress_bar.update(len(chunk))

            # Divide the remaining bytes into chunks
            remaining_bytes = total_size - file_size
            chunk_count = remaining_bytes // chunk_size
            for i in range(chunk_count):
                start = file_size + i * chunk_size
                end = start + chunk_size - 1
                self.futures.append(executor.submit(download_chunk, start, end))

            # Download the last chunk, if any
            last_chunk_start = file_size + chunk_count * chunk_size
            if last_chunk_start < total_size:
                last_chunk_end = total_size - 1
                self.futures.append(executor.submit(download_chunk, last_chunk_start, last_chunk_end))

            # Wait for all futures to complete
            for future in as_completed(self.futures):
                future.result()

    def start(self, gogoanimeUrl, fileName=None, quality='1080', anime_name=None):
        # authenicate user send request to gogoanime and get all download links
        response = requests.get(gogoanimeUrl, headers=self.headers)
        # get download link dict
        link_dict = self.get_download_link_dict(response)
        # get download url
        url, quality = self.get_download_url(link_dict, quality)
        if fileName is None:
            fileName = gogoanimeUrl.split("/")[-1]
            file_extension = url.split('.')[-1]
            fileName = f"{fileName}-{quality}.{file_extension}"
        if anime_name:
            fileName = f"{anime_name}/{fileName}"
        try:
            self.download(url, fileName)
        except requests.exceptions.MissingSchema as e:
            print(f"Error: Please check your url: {gogoanimeUrl}")


def download(downloader, url, fileName=None, quality='1080', anime_name=None):
    i = 0
    while True:
        try:
            downloader.start(url, fileName=fileName, quality=quality, anime_name=anime_name)
            return
        except Exception as e:
            i += 1
            print(f"Error retrying {i}. Going to sleep for 10 seconds")
            if i > 5:
                messagebox.showerror(title="Error", message=f"{e}")
                exit()
            time.sleep(10)




def main():
    # Create an argument parser
    parser = argparse.ArgumentParser(description='Description of program')

    # Add arguments to the parser
    parser.add_argument('-s', '--start', type=str, help='start episode')
    parser.add_argument('-e', '--end', type=str, help='end episode')
    parser.add_argument('-q', '--quality', type=str, help='video quality')
    parser.add_argument('-d', '--destination', type=str, help='destination folder')
    parser.add_argument('--yes-playlist', action='store_true', help='For playlist download')
    parser.add_argument('url', help='Url of the anime')
    

    # Parse the command-line arguments
    args = parser.parse_args()

    # Access the values of the arguments
    url = args.url
    start_episode = args.start
    end_episode = args.end
    quality = args.quality
    destination = args.destination
    yes_playlist = args.yes_playlist

    if not is_valid_url(url) or not is_valid_anime_url(url):
        messagebox.showerror(title="Invalid link", message=f"{url}")
        return
    
    if not yes_playlist and 'episode' not in url:
        messagebox.showwarning(title="Warning", message=f"Not category url:{url}\n Give episode url or type --yes-playlist for downloading playlist")
        return
    
    web_site = "/".join(url.split("/")[:3])
    anime_name = url.split("/")[-1].split("-episode")[0]
    if not quality:
        quality = '1080'
    if not destination:
            destination = anime_name
    os.makedirs(destination, exist_ok=True)

    downloader = Gogoanime()

    if not yes_playlist:
        download(downloader, url, quality=quality, anime_name=destination)
        messagebox.showinfo(title="Success", message="Download Complete")
        return
        
    
    if not start_episode:
        start_episode = 1
    if not end_episode:
        end_episode = get_last_episode(f"{web_site}/category/{anime_name}")

    start_episode = f"/{anime_name}-episode-{start_episode}"
    end_episode = f"/{anime_name}-episode-{end_episode}"


    # if signle_episode:
    #     url = f"{web_site}/{destination}-episode-{signle_episode}"
    #     download(downloader, url, quality=quality, anime_name=destination)
    current_episode = start_episode
    while current_episode:
        url = f"{web_site}{current_episode}"
        print(url)
        download(downloader, url, quality=quality, anime_name=destination)
        next_episode = get_next_episode(url)
        if not next_episode:
            break
        if current_episode == end_episode:
            break
        current_episode = next_episode


    messagebox.showinfo(title="Success", message="Download Complete")


if __name__ == '__main__':
    main()
