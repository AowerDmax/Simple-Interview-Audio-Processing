import pyaudio
import wave
from Config import Config

# 初始化 PyAudio
audio = pyaudio.PyAudio()

# 列出所有音频输入设备
for i in range(audio.get_device_count()):
    device_info = audio.get_device_info_by_index(i)
    print(f"Device {i}: {device_info['name']}")

# 选择 Aggregate Device 和麦克风的设备索引
aggregate_device_index = 12  # 根据上面的列表选择适合的设备索引
mic_device_index = 2  # 替换为你的麦克风设备索引

# 配置参数
FORMAT = pyaudio.paInt16
RATE = Config.AUDIO_FS
CHANNELS = 1  # 单声道可能更兼容不同的设备
chunk_size = 60 * Config.CHUNK_SIZE[1] / Config.CHUNK_INTERVAL
CHUNK = int(RATE / 1000 * chunk_size)

# 打开系统音频输入流（使用聚合设备）
system_stream = audio.open(format=FORMAT,
                           channels=CHANNELS,
                           rate=RATE,
                           input=True,
                           input_device_index=aggregate_device_index,
                           frames_per_buffer=CHUNK)

# 打开麦克风输入流
mic_stream = audio.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        input_device_index=mic_device_index,
                        frames_per_buffer=CHUNK)

print("Recording...")

# 捕获音频数据
system_frames = []
mic_frames = []

for _ in range(100):
    system_data = system_stream.read(CHUNK)
    mic_data = mic_stream.read(CHUNK)
    system_frames.append(system_data)
    mic_frames.append(mic_data)

# 停止并关闭流
system_stream.stop_stream()
system_stream.close()

mic_stream.stop_stream()
mic_stream.close()

audio.terminate()

# 保存系统音频到文件
with wave.open("system_audio.wav", 'wb') as wf:
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(system_frames))

# 保存麦克风音频到文件
with wave.open("mic_audio.wav", 'wb') as wf:
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(mic_frames))

print("Recording finished and saved to files.")
