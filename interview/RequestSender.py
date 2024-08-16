import aiohttp
import json
from dotenv import load_dotenv
import os
import logging
from DialogManager import DialogManager
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RequestSender:
    def __init__(self):
        load_dotenv()
        self.url = os.getenv('CHATGPT_BASE_URL')
        self.headers = {
            'Authorization': "Bearer " + os.getenv('AUTHORIZATION'),
            'Content-Type': 'application/json', 
            "Accept": 'application/json'
        }
        self.dialog = DialogManager()
        self.model = os.getenv('MODEL')

    async def send_post_request(self, contentList):
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": self.model,
                "messages": contentList, 
                "stream": True
            }
            receiveData = ""
            buffer = ""
            buffer_time = 0.5
            try:
                async with session.post(self.url, headers=self.headers, data=json.dumps(payload)) as response:
                    if response.status == 200:
                        last_update_time = time.time()
                        async for line in response.content:
                            if line.startswith(b'data: '):
                                sse_message = line.decode('utf-8').strip()[6:]
                                if sse_message == '[DONE]':
                                    receiveData += buffer
                                    self.dialog.update_last_chatgpt(receiveData)
                                    break
                                message_data = self.extract_id_and_content(json.loads(sse_message))
                                if 'content' in message_data and message_data['content']:
                                    buffer += message_data['content']
                                    
                                    if time.time() - last_update_time > buffer_time:
                                        receiveData += buffer
                                        self.dialog.update_last_chatgpt(receiveData)
                                        buffer = ""
                                        last_update_time = time.time()

                            else:
                                logger.debug(f"Received non-data line: {line}")
            except aiohttp.ClientError as e:
                logger.error(f"Request failed: {str(e)}")
            
            return receiveData
    
    def extract_id_and_content(self, response_data):
        try:
            response_id = response_data.get('id')
            content = response_data.get('choices', [])[0].get('delta', {}).get('content')
            return {
                "id": response_id,
                "content": content
            }
        except (IndexError, KeyError, TypeError) as e:
            logger.error(f"Error extracting id and content: {e}")
            return {"error": "Invalid response format"}

