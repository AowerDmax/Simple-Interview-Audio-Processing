import asyncio
from multiprocessing import Process
from Rookie import Rookie
from Interviewer import Interview
from DialogManager import DialogManager

def interview_thread(id, chunk_begin, chunk_size):
    interview = Interview()
    asyncio.run(interview.ws_client(id, chunk_begin, chunk_size))

def rookie_thread(id, chunk_begin, chunk_size):
    rookie = Rookie()
    asyncio.run(rookie.ws_client(id, chunk_begin, chunk_size))


if __name__ == '__main__':

    dialog_manager = DialogManager()
    dialog_manager.clear_all()
    interview_process = Process(target=interview_thread, args=("interviewer", 0, 1))
    rookie_process = Process(target=rookie_thread, args=("rookie", 0, 1))
    
    interview_process.start()
    rookie_process.start()

    interview_process.join()
    rookie_process.join()
