import os
import requests
from tqdm import tqdm
from decouple import config
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed


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
        gogoanime = config("gogoanime")
        auth = config("auth")
        User_Agent = config("User-Agent")
        self.headers = requests.utils.default_headers()
        self.headers.update(
            {
                'Cookie': f'gogoanime={gogoanime}; auth=f{auth}',
                'User-Agent': f'{User_Agent}',
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

        # get main download url
        url = response.headers.get('location')
        return url, quality
    
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

    def start(self, gogoanimeUrl, fileName=None, quality='1080'):
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
        try:
            self.download(url, fileName)
        except requests.exceptions.MissingSchema as e:
            print(f"Error: Please check your url: {gogoanimeUrl}")


if __name__ == '__main__':
    downloader = Gogoanime()
    url = input("Anime url: ")
    quality = input('Video Quality(360, 480, 720, 1080): ')
    url_dict = {
        'web_site': "/".join(url.split("/")[:3]),
        "anime_name": url.split("/")[-1]
    }
    if "episode" in url_dict['anime_name']:
        url_dict['anime_name'] = url_dict['anime_name'].split("-episode")[0]

    print(f"""
    Download Type:
    1. Single Episode/ Video
    2. Multiple Episodes/ Videos 
    """)
    download_type = int(input("Download Type: "))
    if download_type == 1:
        if "episode" not in url:
            print(f"{url} not found")
            exit()
        downloader.start(url, quality=quality)
    else:
        ep_from = int(input('Episode from : '))
        ep_to = int(input('Episode to : ')) + 1
        for episode in range(ep_from, ep_to):
            url = f"{url_dict['web_site']}/{url_dict['anime_name']}-episode-{episode}"
            downloader.start(url, quality=quality)
    