import pyaudio
import json
import asyncio
import numpy as np
import websockets
from Config import Config
import os
import time
from queue import Queue
from multiprocessing import Process
from DialogManager import DialogManager
from ChatgptManager import ChatgptManager
import multiprocessing

class Interview:
    def __init__(self):
        self.voices = []
        self.offline_msg_done = False
        self.websocket = None
        self.text_print_2pass_offline = ""
        self.text_print_2pass_online = ""
        self.dialog = DialogManager()
        self.chatgpt = ChatgptManager()


    async def ws_client(self, id="Interview", chunk_begin=0, chunk_size=1):
        while True:
            for i in range(chunk_begin, chunk_begin + chunk_size):
                self.offline_msg_done = False
                self.voices = Queue()
                
                uri = f"ws://{Config.INTERVIEWER_HOST}:{Config.INTERVIEWER_PORT}"
                ssl_context = None
                
                print("Connecting to", uri)
                try:
                    async with websockets.connect(uri, subprotocols=["binary"], ping_interval=None, ssl=ssl_context) as self.websocket:
                        task1 = asyncio.create_task(self.record_system_voice())
                        task2 = asyncio.create_task(self.message(id))
                        await asyncio.gather(task1, task2)
                except websockets.exceptions.ConnectionClosedError as e:
                    print(f"WebSocket connection closed with error: {e}")
                    await asyncio.sleep(3)
                except Exception as e:
                    print(f"Interviewer error occurred: {e}")
                    import traceback
                    traceback.print_exc()
                    await asyncio.sleep(3)

    async def record_system_voice(self):
        FORMAT = pyaudio.paInt16
        CHANNELS = Config.AUDIO_CHANNEL
        RATE = Config.AUDIO_FS
        chunk_size = 60 * Config.CHUNK_SIZE[1] / Config.CHUNK_INTERVAL
        CHUNK = int(RATE / 1000 * chunk_size)
        audio = pyaudio.PyAudio()
        TARGET_RATE = 16000  
        TARGET_CHANNELS = 1


        while True:
            try:
                audio = pyaudio.PyAudio()
                system_stream = audio.open(format=FORMAT,
                                           channels=CHANNELS,
                                           rate=RATE,
                                           input=True,
                                           input_device_index=Config.AGGREGATE_DEVICE_INDEX,
                                           frames_per_buffer=CHUNK)
                break
            except OSError as e:
                print(f"Error opening audio stream: {e}")
            except Exception as e:
                print(f"pyaudio error occurred: {e}")

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

        def convert_to_mono(data, channels):
            audio_data = np.frombuffer(data, dtype=np.int16)
            mono_data = audio_data.reshape((-1, channels)).mean(axis=1)
            return mono_data.astype(np.int16)

        def resample_audio(data, original_rate, target_rate):
            audio_data = np.frombuffer(data, dtype=np.int16)
            resampled_data = np.interp(np.linspace(0, len(audio_data), int(len(audio_data) * target_rate / original_rate)),
                                    np.arange(len(audio_data)), audio_data)
            return resampled_data.astype(np.int16)

        while True:
            data = system_stream.read(CHUNK)

            try:
                if CHANNELS == TARGET_CHANNELS and RATE == TARGET_RATE:
                    await self.websocket.send(data)
                else:
                    mono_data = convert_to_mono(data, CHANNELS)

                    resampled_data = resample_audio(mono_data, RATE, TARGET_RATE)

                    output_data = resampled_data.tobytes()

                    await self.websocket.send(output_data)
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
                    meg = await asyncio.wait_for(self.websocket.recv(), timeout=Config.INTERVIEWER_WAIT_TIME / 1000)
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
                        self.dialog.update_last_interviewer(text_print)
                    else:
                        self.text_print_2pass_online = ""
                        text_print = self.text_print_2pass_offline + "{}".format(text)
                        text_print = text_print[-Config.WORDS_MAX_PRINT:]
                        self.dialog.update_last_interviewer(text_print)
                        self.text_print_2pass_offline += "{}".format(text)
                except asyncio.TimeoutError: 
                    if self.text_print_2pass_offline:
                        self.text_print_2pass_offline = ""
                        self.dialog.add_to_interviewer("")
        except Exception as e:
            print("Interview receive ws message Exception:", e)


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


def interview_thread(id, chunk_begin, chunk_size):
    while True:
        try:
            interview = Interview()
            asyncio.run(interview.ws_client(id, chunk_begin, chunk_size))
        except Exception as e:
            print(f"Interview thread encountered an error: {e}")
            time.sleep(3)

if __name__ == '__main__':
    p = Process(target=interview_thread, args=("interviewer", 0, 1))
    p.start()
    p.join()
