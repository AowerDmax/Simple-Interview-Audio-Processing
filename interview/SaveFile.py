import redis
import os
from Config import Config

class SaveFile:
    def __init__(self):
        self.redis = redis.StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, decode_responses=True)

        self.interviewer_key = "dialog_manager:interviewer"
        self.rookie_key = "dialog_manager:rookie"
        self.chatgpt_key = "dialog_manager:chatgpt"

    def _get_valid_entries(self, key, max_len):
        # 使用 eval() 解析 Redis 中的数据
        entries = [eval(item) for item in self.redis.lrange(key, 0, -1)]
        valid_entries = [item for item in entries if item['text'].strip() != ""]

        if len(valid_entries) > max_len:
            return valid_entries[-max_len:]
        else:
            return valid_entries

    def _get_icon(self, list_name):
        if list_name == "interviewer":
            return "🎤"
        elif list_name == "rookie":
            return "😅"
        elif list_name == "chatgpt":
            return "🤖"

    def export_dialogs_to_file(self, filename):
        interviewer_list = self._get_valid_entries(self.interviewer_key, Config.INTERVIEWER_DIALOG_LEN)
        rookie_list = self._get_valid_entries(self.rookie_key, Config.ROOKIE_DIALOG_LEN)
        chatgpt_list = self._get_valid_entries(self.chatgpt_key, Config.CHATGPT_DIALOG_LEN)

        combined_list = interviewer_list + rookie_list + chatgpt_list

        # 对提取出的元素按时间排序
        sorted_combined_list = sorted(combined_list, key=lambda x: x['time'])

        output = []
        for entry in sorted_combined_list:
            icon = self._get_icon(entry['list_name'])
            output.append(f"{entry['time']} {icon} {entry['list_name']} : \n\n {entry['text']}")

        result = "\n\n".join(output)

        with open(filename, 'w') as file:
            file.write(result)

        print(f"Dialogs have been saved to {filename}")

# 示例用法
if __name__ == "__main__":
    dialog_manager = SaveFile()

    dialog_manager.export_dialogs_to_file("dialogs_output.md")
