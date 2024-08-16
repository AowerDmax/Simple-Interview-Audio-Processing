import os
import time
import random
import redis
from multiprocessing import Process
from Config import Config
from redis.exceptions import LockNotOwnedError

class DialogManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DialogManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.redis = redis.StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, decode_responses=True)

        self.interviewer_key = "dialog_manager:interviewer"
        self.rookie_key = "dialog_manager:rookie"
        self.chatgpt_key = "dialog_manager:chatgpt"

        self.interviewer_icons = ["🎤"]
        self.rookie_icons = ["😅"]
        self.chatgpt_icons = ["🤖"]

    def _get_icon(self, list_name):
        if list_name == "interviewer":
            return random.choice(self.interviewer_icons)
        elif list_name == "rookie":
            return random.choice(self.rookie_icons)
        elif list_name == "chatgpt":
            return random.choice(self.chatgpt_icons)

    def _get_valid_entries(self, key, max_len):
        entries = self._get_list(key)
        valid_entries = [item for item in entries if item['text'].strip() != ""]

        if len(valid_entries) > max_len:
            return valid_entries[-max_len:]
        else:
            return valid_entries

    def _notify_change(self, out = True):
        interviewer_list = self._get_valid_entries(self.interviewer_key, Config.INTERVIEWER_DIALOG_LEN)
        rookie_list = self._get_valid_entries(self.rookie_key, Config.ROOKIE_DIALOG_LEN)
        chatgpt_list = self._get_valid_entries(self.chatgpt_key, Config.CHATGPT_DIALOG_LEN)

        combined_list = interviewer_list + rookie_list + chatgpt_list

        sorted_combined_list = sorted(combined_list, key=lambda x: x['time'])

        output = []
        for entry in sorted_combined_list:
            icon = self._get_icon(entry['list_name'])
            output.append(f"{entry['time']} {icon} {entry['list_name']} : {entry['text']}")

        result = "\n".join(output)
        if out:
            os.system('clear')
            print(result)
        return result

    def _get_list(self, key):
        return [eval(item) for item in self.redis.lrange(key, 0, -1)]

    def _add_to_list(self, key, element):
        lock = self.redis.lock("dialog_manager_lock", timeout=10, blocking_timeout=5)
        try:
            lock.acquire()
            self.redis.rpush(key, str(element))
            self._notify_change()
        finally:
            try:
                lock.release()
            except LockNotOwnedError:
                pass

    def _update_last_in_list(self, key, element):
        lock = self.redis.lock("dialog_manager_lock", timeout=10, blocking_timeout=5)
        try:
            lock.acquire()
            current_list = self._get_list(key)
            if current_list:
                current_list[-1] = element
                self.redis.lset(key, -1, str(element))
            else:
                self.redis.rpush(key, str(element))
            self._notify_change()
        finally:
            try:
                lock.release()
            except LockNotOwnedError:
                pass

    def get_dialog(self):
        return self._notify_change(False)
    
    def add_to_interviewer(self, element):
        current_time = time.strftime("[%H:%M:%S]", time.localtime())
        entry = {'time': current_time, 'list_name': 'interviewer', 'text': element}
        self._add_to_list(self.interviewer_key, entry)

    def add_to_rookie(self, element):
        current_time = time.strftime("[%H:%M:%S]", time.localtime())
        entry = {'time': current_time, 'list_name': 'rookie', 'text': element}
        self._add_to_list(self.rookie_key, entry)

    def add_to_chatgpt(self, element):
        current_time = time.strftime("[%H:%M:%S]", time.localtime())
        entry = {'time': current_time, 'list_name': 'chatgpt', 'text': element}
        self._add_to_list(self.chatgpt_key, entry)

    def update_last_interviewer(self, element):
        current_time = time.strftime("[%H:%M:%S]", time.localtime())
        entry = {'time': current_time, 'list_name': 'interviewer', 'text': element}
        self._update_last_in_list(self.interviewer_key, entry)

    def update_last_rookie(self, element):
        current_time = time.strftime("[%H:%M:%S]", time.localtime())
        entry = {'time': current_time, 'list_name': 'rookie', 'text': element}
        self._update_last_in_list(self.rookie_key, entry)

    def update_last_chatgpt(self, element):
        current_time = time.strftime("[%H:%M:%S]", time.localtime())
        entry = {'time': current_time, 'list_name': 'chatgpt', 'text': element}
        self._update_last_in_list(self.chatgpt_key, entry)
    
    def clear_all(self):
        lock = self.redis.lock("dialog_manager_lock", timeout=10, blocking_timeout=5)
        try:
            lock.acquire()
            self.redis.delete(self.interviewer_key)
            self.redis.delete(self.rookie_key)
            self.redis.delete(self.chatgpt_key)
            print("All keys have been cleared.")
        finally:
            try:
                lock.release()
            except LockNotOwnedError:
                pass


def process_1():
    dialog_manager = DialogManager()
    dialog_manager.add_to_interviewer("Question 1")
    time.sleep(1)
    dialog_manager.add_to_rookie("Answer 1")
    time.sleep(1)
    dialog_manager.add_to_chatgpt("Suggestion 1")
    time.sleep(1)

def process_2():
    dialog_manager = DialogManager()
    dialog_manager.add_to_interviewer("Question 2")
    time.sleep(1)
    dialog_manager.add_to_rookie("Answer 2")
    time.sleep(1)
    dialog_manager.add_to_rookie("Answer 3")
    time.sleep(1)
    dialog_manager.add_to_chatgpt("Suggestion 2")
    time.sleep(1)

def process_3():
    dialog_manager = DialogManager()
    dialog_manager.update_last_interviewer("Updated Question 2")
    dialog_manager.update_last_rookie("Updated Answer 5")
    dialog_manager.update_last_chatgpt("Updated Suggestion 2")
    time.sleep(1)
    dialog_manager.update_last_interviewer("Question 3 (new)")
    dialog_manager.update_last_rookie("Answer 4 (new)")
    dialog_manager.update_last_chatgpt("Suggestion 3 (new)")

if __name__ == "__main__":
    p1 = Process(target=process_1)
    p2 = Process(target=process_2)
    p3 = Process(target=process_3)

    p1.start()
    p2.start()
    p3.start()

    p1.join()
    p2.join()
    p3.join()

    print('end')
