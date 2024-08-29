import asyncio
from DialogManager import DialogManager
from RequestSender import RequestSender
from Config import Config

class MultimodeManager:
    def __init__(self):
        self.request_sender = RequestSender()
        self.prompt_directory = "./prompt"
        self.dialog = DialogManager()

    async def multimode_process(self, category, link):
        content_list = []

        file_path = self.prompt_directory + "/" + category + ".md"
        print(file_path)
        with open(file_path, 'r') as file:
            file_content = file.read()
        if not self.dialog.get_last_rookie():
            self.dialog.update_last_rookie(file_content + f' \n <img src="{link}" alt="Description" style="width:100%;">')
        else:
            print(self.dialog.get_last_rookie())
            self.dialog.add_to_rookie(file_content + f' \n <img src="{link}" alt="Description" style="width:100%;">')

        content = [
            {"type": "text", "text": file_content},
            {"type": "image_url", "image_url": {"url": link}}
        ]
        
        content_list.append({
            "content": content,
            "role": "user"
        })

        print(content_list)
        
        await self.request_sender.send_post_request(content_list)

        self.dialog.add_to_rookie("")

async def main():
    multimodeManager = MultimodeManager()
    category = "algorithm"
    link = "xxxxxx"
    await multimodeManager.multimode_process(category, link)

if __name__ == '__main__':
    asyncio.run(main())




