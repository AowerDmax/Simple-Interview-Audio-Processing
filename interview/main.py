import asyncio
import signal
import sys
import time
from multiprocessing import Process
from Rookie import Rookie
from Interviewer import Interview
from DialogManager import DialogManager
from ScreenShot import listen_key_process
from SaveFile import SaveFile
from datetime import datetime

def interview_thread(id, chunk_begin, chunk_size):
    while True:
        try:
            interview = Interview()
            asyncio.run(interview.ws_client(id, chunk_begin, chunk_size))
        except Exception as e:
            print(f"Interview thread encountered an error: {e}")
            time.sleep(3)

def rookie_thread(id, chunk_begin, chunk_size):
    while True:
        try:
            rookie = Rookie()
            asyncio.run(rookie.ws_client(id, chunk_begin, chunk_size))
        except Exception as e:
            print(f"Rookie thread encountered an error: {e}")
            time.sleep(3)

def handle_exit(signum, frame):
    print("\nGracefully shutting down...")

    interview_process.terminate()
    rookie_process.terminate()
    listen_key_process.terminate()

    interview_process.join()
    rookie_process.join()
    listen_key_process.join()

    saveFile = SaveFile()
    current_time = datetime.now().strftime("%Y%m%d%H%M")
    file_name = f"dialogs_output_{current_time}.md"
    saveFile.export_dialogs_to_file(file_name)
    print(f"Dialogs saved to {file_name}. Exiting.")

    sys.exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, handle_exit)

    dialog_manager = DialogManager()
    dialog_manager.clear_all()
    dialog_manager.add_to_interviewer("")
    dialog_manager.add_to_chatgpt("")
    dialog_manager.add_to_rookie("")

    interview_process = Process(target=interview_thread, args=("interviewer", 0, 1))
    rookie_process = Process(target=rookie_thread, args=("rookie", 0, 1))
    listen_key_process = Process(target=listen_key_process)

    interview_process.start()
    rookie_process.start()
    listen_key_process.start()

    try:
        interview_process.join()
        rookie_process.join()
        listen_key_process.join()
    except KeyboardInterrupt:
        handle_exit(None, None)
