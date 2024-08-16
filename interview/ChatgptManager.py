from RequestSender import RequestSender
import os
from DialogManager import DialogManager

class ChatgptManager:
    def __init__(self):
        self.dialog = DialogManager()
        self.request_sender = RequestSender()
        self.prompt_directory = "prompt"

    async def run_workflow(self):
        files = sorted(os.listdir(self.prompt_directory))
        content_list = []

        for file_name in files:
            file_path = os.path.join(self.prompt_directory, file_name)
            if file_name.endswith('.md') and os.path.isfile(file_path):
                with open(file_path, 'r') as file:
                    content = file.read()        
                    content = self._replace_content(content)
                    self.dialog.add_to_chatgpt("")
                    content_list.append({
                        "content": content,
                        "role": "user"
                    })
                    receiveData = await self.request_sender.send_post_request(content_list)
                    content_list.append({
                        "content": receiveData,
                        "role": "assistant"
                    })
        
    def _replace_content(self, content):
        content = content.replace("${conversation}", self.dialog.get_dialog())
        return content

