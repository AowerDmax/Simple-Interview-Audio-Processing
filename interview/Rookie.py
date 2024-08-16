import pyaudio
import json
import asyncio
import websockets
from Config import Config
import os
from queue import Queue
from multiprocessing import Process
from DialogManager import DialogManager

class Rookie:
    def __init__(self):
        self.voices = []
        self.offline_msg_done = False
        self.websocket = None
        self.text_print_2pass_offline = ""
        self.text_print_2pass_online = ""
        self.dialog = DialogManager()

    async def ws_client(self, id="Rookie", chunk_begin=0, chunk_size=1):
        for i in range(chunk_begin, chunk_begin + chunk_size):
            self.offline_msg_done = False
            self.voices = Queue()
            
            uri = f"ws://{Config.ROOKIE_HOST}:{Config.ROOKIE_PORT}"
            ssl_context = None
            
            print("connect to", uri)
            try:
                async with websockets.connect(uri, subprotocols=["binary"], ping_interval=None, ssl=ssl_context) as self.websocket:
                    task1 = asyncio.create_task(self.record_microphone())
                    task2 = asyncio.create_task(self.message(id))
                    await asyncio.gather(task1, task2)
            except websockets.exceptions.ConnectionClosedError as e:
                print(f"WebSocket connection closed with error: {e}")
                break
            except Exception as e:
                print(f"An error occurred: {e}")
                break

    async def record_microphone(self):
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = Config.AUDIO_FS
        chunk_size = 60 * Config.CHUNK_SIZE[1] / Config.CHUNK_INTERVAL
        CHUNK = int(RATE / 1000 * chunk_size)
        audio = pyaudio.PyAudio()

        mic_stream = audio.open(format=FORMAT,
                                   channels=CHANNELS,
                                   rate=RATE,
                                   input=True,
                                   input_device_index=Config.MIC_DEVICE_INDEX,
                                   frames_per_buffer=CHUNK)

        fst_dict, hotword_msg = self.prepare_hotword_message()

        use_itn = Config.USE_ITN == 1
        message = json.dumps({
            "mode": Config.MODE,
            "chunk_size": Config.CHUNK_SIZE,
            "chunk_interval": Config.CHUNK_INTERVAL,
            "wav_name": "system_voice",
            "is_speaking": True,
            "hotwords": hotword_msg,
            "itn": use_itn
        })

        await self.websocket.send(message)
        while True:
            data = mic_stream.read(CHUNK)
            try:
                await self.websocket.send(data)
                await asyncio.sleep(0.01)
            except websockets.exceptions.ConnectionClosedError as e:
                print(f"Connection closed with error: {e}")
                break

    async def message(self, id):
        if Config.OUTPUT_DIR is not None:
            ibest_writer = open(os.path.join(Config.OUTPUT_DIR, f"text.{id}"), "a", encoding="utf-8")
        else:
            ibest_writer = None
        try:
            while True:
                try:
                    meg = await asyncio.wait_for(self.websocket.recv(), timeout=Config.ROOKIE_WAIT_TIME / 1000)
                    meg = json.loads(meg)
                    wav_name = meg.get("wav_name", "demo")
                    text = meg["text"]
                    timestamp = ""
                    self.offline_msg_done = meg.get("is_final", False)

                    if "timestamp" in meg:
                        timestamp = meg["timestamp"]

                    if ibest_writer is not None:
                        if timestamp != "":
                            text_write_line = f"{wav_name}\t{text}\t{timestamp}\n"
                        else:
                            text_write_line = f"{wav_name}\t{text}\n"
                        ibest_writer.write(text_write_line)

                    if 'mode' not in meg:
                        continue

                    if meg["mode"] == "2pass-online":
                        self.text_print_2pass_online += "{}".format(text)
                        text_print = self.text_print_2pass_offline + self.text_print_2pass_online
                        text_print = text_print[-Config.WORDS_MAX_PRINT:]
                        self.dialog.update_last_rookie(text_print)
                    else:
                        self.text_print_2pass_online = ""
                        text_print = self.text_print_2pass_offline + "{}".format(text)
                        text_print = text_print[-Config.WORDS_MAX_PRINT:]
                        self.dialog.update_last_rookie(text_print)
                        self.text_print_2pass_offline += "{}".format(text)
                except asyncio.TimeoutError:
                    if self.text_print_2pass_offline:
                        self.text_print_2pass_offline = ""
                        self.dialog.add_to_rookie("")

        except Exception as e:
            print("Exception:", e)

    def prepare_hotword_message(self):
        fst_dict = {}
        hotword_msg = ""
        if Config.HOTWORD.strip():
            with open(Config.HOTWORD) as f_scp:
                hot_lines = f_scp.readlines()
                for line in hot_lines:
                    words = line.strip().split(" ")
                    if len(words) < 2:
                        print("Please check format of hotwords")
                        continue
                    try:
                        fst_dict[" ".join(words[:-1])] = int(words[-1])
                    except ValueError:
                        print("Please check format of hotwords")
            hotword_msg = json.dumps(fst_dict)
        return fst_dict, hotword_msg


def rookie_thread(id, chunk_begin, chunk_size):
    rookie = Rookie()
    asyncio.run(rookie.ws_client(id, chunk_begin, chunk_size))

if __name__ == '__main__':
    p = Process(target=rookie_thread, args=("rookie", 0, 1))
    p.start()
    p.join()
