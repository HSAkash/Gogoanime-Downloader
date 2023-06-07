import os
import time
import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import tkinter as tk
import argparse

from urllib.parse import urlparse

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False
    





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
        gogoanime="gogoanime"
        auth="HSAkash"
        User_Agent = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/112.0"
        Accept = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
        self.headers = requests.utils.default_headers()
        self.headers.update(
            {
                'Host': 'gogoanime.cl',
                'Cookie': f'gogoanime={gogoanime}; auth={auth}',
                'User-Agent': User_Agent,
                'Accept': Accept,
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Referer': 'https://gogoanime.cl/'
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
            if i > 5:
                tk.messagebox.showerror(title="Error", message=f"{e}")
                exit()
            time.sleep(30)
            i += 1




def main():
    # Create an argument parser
    parser = argparse.ArgumentParser(description='Description of program')

    # Add arguments to the parser
    parser.add_argument('-U', '--url', type=str, help='url of the anime')
    parser.add_argument('-s', '--start', type=int, help='start episode')
    parser.add_argument('-n', '--episode', type=int, help='single episode number')
    parser.add_argument('-e', '--end', type=int, help='end episode')
    parser.add_argument('-q', '--quality', type=str, help='video quality')
    parser.add_argument('-d', '--destination', type=str, help='destination folder')

    # Parse the command-line arguments
    args = parser.parse_args()

    # Access the values of the arguments
    url = args.url
    start_episode = args.start
    end_episode = args.end
    quality = args.quality
    destination = args.destination
    signle_episode = args.episode

    
    if is_valid_url(url):
        downloader = Gogoanime()
        web_site = "/".join(url.split("/")[:3])
        anime_name = url.split("/")[-1].split("-episode")[0]

        if not quality:
            quality = '1080'
        if not destination:
                destination = anime_name
        os.makedirs(destination, exist_ok=True)


        if signle_episode:
            url = f"{web_site}/{destination}-episode-{signle_episode}"
            download(downloader, url, quality=quality, anime_name=destination)

        elif not start_episode and not end_episode and 'episode' in url:
            download(downloader, url, quality=quality, anime_name=destination)
        else:
            if not start_episode:
                start_episode = 1
            if not end_episode:
                end_episode = start_episode + 12
            for episode in range(start_episode, end_episode+1):
                url = f"{web_site}/{destination}-episode-{episode}"
                download(downloader, url, quality=quality, anime_name=destination)
            


if __name__ == '__main__':
    main()
    tk.messagebox.showinfo(title="Success", message="Download Complete")