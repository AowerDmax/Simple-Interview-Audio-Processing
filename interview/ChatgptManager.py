import os
import time
import asyncio
from DialogManager import DialogManager
from RequestSender import RequestSender
from Config import Config
from RagManager import RagManager

class ChatgptManager:
    def __init__(self):
        self.dialog = DialogManager()
        self.request_sender = RequestSender()
        self.prompt_directory = "./workflows/prompt_2"
        self.last_processed_id = 3
        self.rag = RagManager()

    async def run_workflow(self):
        files = sorted(os.listdir(self.prompt_directory))
        content_list = []

        for file_name in files:
            file_path = os.path.join(self.prompt_directory, file_name)
            if file_name.endswith('.md') and os.path.isfile(file_path):
                with open(file_path, 'r') as file:
                    content = file.read()
                
                content = await self._replace_content(content)
                
                content_list.append({
                    "content": content,
                    "role": "user"
                })
                
                receiveData = await self.request_sender.send_post_request(content_list)
                content_list.append({
                    "content": receiveData,
                    "role": "assistant"
                })

    async def _replace_content(self, content):
        content = content.replace("${conversation}", self.dialog.get_dialog())
        if Config.RAG_ENABLED:
            rag_answers = await self.rag.query_meilisearch()
            if rag_answers:
                RAG_content = "\n下面是辅助数据:\n" + "\n".join(rag_answers)
                content += RAG_content
        return content

    def should_process(self):
        interviewer_list = self.dialog._get_list(self.dialog.interviewer_key)
        
        if not interviewer_list:
            return False

        last_entry = interviewer_list[-1]
        if last_entry['id'] > self.last_processed_id:
            if last_entry['text'].strip() == "":
                self.last_processed_id = last_entry['id']
                return True

        return False

def chatgpt_process():
    chatgpt_manager = ChatgptManager()
    while True:
        if chatgpt_manager.should_process():
            asyncio.run(chatgpt_manager.run_workflow())
        
        time.sleep(Config.INTERVIEWER_WAIT_TIME / 1000)

if __name__ == "__main__":
    chatgpt_process()