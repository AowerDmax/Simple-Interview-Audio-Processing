import pyaudio
import wave
from Config import Config

# 初始化 PyAudio
audio = pyaudio.PyAudio()

# 列出所有音频输入设备
for i in range(audio.get_device_count()):
    device_info = audio.get_device_info_by_index(i)
    print(f"Device {i}: {device_info['name']}")

def print_device_info(audio, index):
    try:
        info = audio.get_device_info_by_index(index)
        print(f"Device {index}:")
        print(f"  Name: {info['name']}")
        print(f"  Max Input Channels: {info['maxInputChannels']}")
        print(f"  Max Output Channels: {info['maxOutputChannels']}")
        print(f"  Default Sample Rate: {info['defaultSampleRate']}")
    except Exception as e:
        print(f"Error getting info for device {index}: {e}")

# 选择 Aggregate Device 和麦克风的设备索引
aggregate_device_index = 12  # 根据上面的列表选择适合的设备索引
mic_device_index = 1  # 替换为你的麦克风设备索引

print_device_info(audio, aggregate_device_index)
print_device_info(audio, mic_device_index)



# 配置参数
FORMAT = pyaudio.paInt16
System_RATE  = 48000  # 单声道可能会兼容不同的设备
Mic_RATE  = 16000  # 单声道可能会兼容不同的设备
System_CHANNELS = 1  # 单声道可能会兼容不同的设备
Mic_CHANNELS = 1  # 单声道可能会兼容不同的设备
chunk_size = 60 * Config.CHUNK_SIZE[1] / Config.CHUNK_INTERVAL
Mic_CHUNK = int(Mic_RATE / 1000 * chunk_size)
System_CHUNK = int(System_RATE / 1000 * chunk_size)
# 打开系统音频输入流（使用聚合设备）
system_stream = audio.open(format=FORMAT,
                           channels=System_CHANNELS,
                           rate=System_RATE,
                           input=True,
                           input_device_index=aggregate_device_index,
                           frames_per_buffer=System_CHUNK)

# 打开麦克风输入流
mic_stream = audio.open(format=FORMAT,
                        channels=Mic_CHANNELS,
                        rate=Mic_RATE,
                        input=True,
                        input_device_index=mic_device_index,
                        frames_per_buffer=Mic_CHUNK)

print("Recording...")

# 捕获音频数据
system_frames = []
mic_frames = []

for _ in range(50):
    system_data = system_stream.read(System_CHUNK)
    mic_data = mic_stream.read(Mic_CHUNK)
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
    wf.setnchannels(System_CHANNELS)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(System_RATE)
    wf.writeframes(b''.join(system_frames))

# 保存麦克风音频到文件
with wave.open("mic_audio.wav", 'wb') as wf:
    wf.setnchannels(Mic_CHANNELS)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(Mic_RATE)
    wf.writeframes(b''.join(mic_frames))

print("Recording finished and saved to files.")
