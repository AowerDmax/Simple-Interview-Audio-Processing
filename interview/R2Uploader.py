import boto3
from botocore.client import Config as boto3Config
from Config import Config
import hashlib
import os
from datetime import datetime
import requests
from requests.exceptions import RequestException, SSLError
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class R2Uploader:
    def __init__(self):
        self.access_key_id = Config.R2_ACCESS_KEY_ID
        self.secret_access_key = Config.R2_SECRET_ACCESS_KEY
        self.bucket_name = Config.R2_BUCKET_NAME
        self.region = Config.R2_REGION
        self.endpoint_url = Config.R2_ENDPOINT_URL
        self.custom_domain = Config.R2_CUSTOM_DOMAIN

        self.s3_client = boto3.client(
            's3',
            region_name=self.region,
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            config=boto3Config(signature_version='s3v4')
        )

    def _calculate_md5(self, file_path):
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _construct_object_name(self, file_path):
        md5_hash = self._calculate_md5(file_path)
        ext = os.path.splitext(file_path)[1]
        now = datetime.now()
        object_name = f"{now.year}/{now.month}/{md5_hash}{ext}"
        return object_name

    def upload_image(self, file_path):
        try:
            object_name = self._construct_object_name(file_path)
            self.s3_client.upload_file(
                file_path, 
                self.bucket_name, 
                object_name,
                ExtraArgs={'ACL': 'public-read'}
            )
            print(f"File {file_path} uploaded to {object_name} in R2 bucket.")
            return object_name
        except Exception as e:
            print(f"Failed to upload {file_path} to R2 bucket: {e}")
            return None

    def get_file_url(self, object_name):
        if self.custom_domain:
            return f"{self.custom_domain}/{self.bucket_name}/{object_name}"
        else:
            return f"{self.endpoint_url}/{self.bucket_name}/{object_name}"

    def get_markdown_link(self, object_name):
        url = self.get_file_url(object_name)
        return f"![Image]({url})"

    def get_html_link(self, object_name):
        url = self.get_file_url(object_name)
        return f'<img src="{url}" alt="Image"/>'

    def upload_and_get_link(self, file_path, link_type="url"):
        object_name = self.upload_image(file_path)
        if object_name:
            if link_type == "markdown":
                return self.get_markdown_link(object_name)
            elif link_type == "html":
                return self.get_html_link(object_name)
            else:
                return self.get_file_url(object_name)
        else:
            return None
        
    def download_image_from_url(self, img_url):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive"
        }

        retry_strategy = Retry(
            total=5,
            backoff_factor=1, 
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session = requests.Session()
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        try:
            response = session.get(img_url, headers=headers, stream=True, timeout=(10, 30))
            response.raise_for_status()
        except SSLError as e:
            print(f"SSL error occurred, retrying with TLSv1.2: {e}")
            try:
                # Retry with TLSv1.2
                session.mount("https://", adapter)
                response = session.get(img_url, headers=headers, stream=True)
                response.raise_for_status()
            except Exception as e:
                print(f"Failed to download image with TLSv1.2 from {img_url}: {e}")
                return None
        except RequestException as e:
            print(f"Failed to download image from {img_url}: {e}")
            return None

        tmp_dir = "./tmp"
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)

        file_name = os.path.basename(img_url)
        file_path = os.path.join(tmp_dir, file_name)

        try:
            with open(file_path, 'wb') as out_file:
                for chunk in response.iter_content(chunk_size=8192):
                    out_file.write(chunk)
            print(f"Image downloaded successfully from {img_url}")
            return file_path
        except Exception as e:
            print(f"Unexpected error occurred while saving image from {img_url}: {e}")
            return None

    def upload_image_from_url(self, img_url, link_type="url"):
        file_path = self.download_image_from_url(img_url)
        if file_path:
            return self.upload_and_get_link(file_path, link_type)
        return None

if __name__ == "__main__":
    uploader = R2Uploader()
    file_path = './0aa00c3f-97fb-42b6-9297-812b2b0b7b61.png'
    link_type = 'markdown'  # 'url', 'markdown', or 'html'

    link = uploader.upload_and_get_link(file_path, link_type)
    print(f"Generated link: {link}")
