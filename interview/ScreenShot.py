import json
import os
from datetime import datetime
from pynput import keyboard
import pyautogui
import asyncio
from PIL import Image
from multiprocessing import Process
from R2Uploader import R2Uploader
from MultimodeManager import MultimodeManager
from DialogManager import DialogManager
from ChatgptManager import ChatgptManager
import platform


class ScreenshotManager:
    CONFIG_FILE = "config.json"
    DEFAULT_CONFIG = {
        "shortcuts": {
            "algorithm": ["<ctrl>", "<alt>", "a"],
            "personality": ["<ctrl>", "<alt>", "p"],
            "general": ["<ctrl>", "<alt>", "g"],
            "long_screenshot": ["<ctrl>", "<alt>", "l"],
            "help": ["<ctrl>", "<alt>", "h"],
            "fix": ["<ctrl>", "<alt>", "f"],
            "ocr": ["<ctrl>", "<alt>", "o"],
            "exit": ["<ctrl>", "c"]
        },
        "save_dir": "./screenshots",
        "scroll_delay": 1.5,
        "scroll_amount": 17,
        "max_screenshots": 3 
    }

    def __init__(self):
        self.config = self.load_config()
        self.current_keys = set()
        self.uploader = R2Uploader()
        self.link_type = 'url'
        self.prompt_dir = "./prompt/"
        self.dialog = DialogManager()
        self.multimodeManager = MultimodeManager()
        self.loop = None
        self.chatgpt_manager = ChatgptManager()
        self.system = platform.system()
        os.makedirs(self.config['save_dir'], exist_ok=True)

    def load_config(self):
        if os.path.exists(self.CONFIG_FILE):
            with open(self.CONFIG_FILE, 'r') as f:
                return json.load(f)
        return self.DEFAULT_CONFIG

    def save_config(self):
        with open(self.CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=4)

    def map_key_for_platform(self, key):
        if self.system == 'Windows':
            return self.map_key_for_windows(key)
        elif self.system == 'Darwin':
            return self.map_key_for_macos(key)
        elif self.system == 'Linux':
            return self.map_key_for_linux(key)
        return key

    def map_key_for_windows(self, key):
        if hasattr(key, 'vk'):
            vk = key.vk
            if 65 <= vk <= 90:
                return chr(vk).lower()
            if 48 <= vk <= 57:
                return chr(vk)

        key_mapping = {
            'Key.ctrl_l': '<ctrl>',
            'Key.ctrl_r': '<ctrl>',
            'Key.alt_l': '<alt>',
            'Key.alt_r': '<alt>',
            'Key.shift_l': '<shift>',
            'Key.shift_r': '<shift>',
            'Key.cmd': '<cmd>',
            'Key.enter': '<enter>',
            'Key.space': '<space>',
            'Key.tab': '<tab>',
            'Key.esc': '<esc>',
            'Key.backspace': '<backspace>',
        }
        return key_mapping.get(str(key), None)

    def map_key_for_macos(self, key):
        key_mapping = {
            'Key.cmd': '<cmd>',
            'Key.ctrl': '<ctrl>',
            'Key.alt': '<alt>',
            'Key.shift': '<shift>',
            'Key.enter': '<enter>',
            'Key.space': '<space>',
            'Key.tab': '<tab>',
            'Key.esc': '<esc>',
            'Key.backspace': '<backspace>',
            'Key.caps_lock': '<caps_lock>',
            'Key.right': '<right>',
            'Key.left': '<left>',
            'Key.up': '<up>',
            'Key.down': '<down>'
        }
        if isinstance(key, keyboard.KeyCode):
            return key.char.lower() if key.char else None
        else:
            return key_mapping.get(str(key), None)


    def map_key_for_linux(self, key):
        if hasattr(key, 'vk'):
            vk = key.vk
            if 65 <= vk <= 90:
                return chr(vk).lower()
            if 48 <= vk <= 57:
                return chr(vk)

        key_mapping = {
            'Key.ctrl_l': '<ctrl>',
            'Key.ctrl_r': '<ctrl>',
            'Key.alt_l': '<alt>',
            'Key.alt_r': '<alt>',
            'Key.shift_l': '<shift>',
            'Key.shift_r': '<shift>',
            'Key.enter': '<enter>',
            'Key.space': '<space>',
            'Key.tab': '<tab>',
            'Key.esc': '<esc>',
            'Key.backspace': '<backspace>',
        }
        return key_mapping.get(str(key), None)
    
    def take_screenshot(self):
        screenshot = pyautogui.screenshot()
        filename = datetime.now().strftime("screenshot_%Y%m%d_%H%M%S.png")
        filepath = os.path.join(self.config['save_dir'], filename)
        screenshot.save(filepath)
        print(f"Screenshot saved as {filepath}")
        return filepath
    
    async def take_long_screenshot(self):
        print("Taking long screenshot...")
        screen_width, screen_height = pyautogui.size()
        mouse_x, mouse_y = pyautogui.position()

        screenshots = []
        total_height = 0

        for i in range(self.config['max_screenshots']):
            print(f"Taking screenshot {i+1}/{self.config['max_screenshots']}...")
            
            current_screenshot = await self.safe_screenshot()
            if not current_screenshot:
                print(f"Failed to take screenshot {i+1}. Stopping capture.")
                break

            screenshots.append(current_screenshot)
            total_height += current_screenshot.height

            if i < self.config['max_screenshots'] - 1:
                print(f"Scrolling down {self.config['scroll_amount']} pixels...")
                pyautogui.scroll(-self.config['scroll_amount'])
                await asyncio.sleep(self.config['scroll_delay'])

        if not screenshots:
            print("No screenshots were captured. Aborting.")
            return None

        print(f"Captured {len(screenshots)} screenshots. Stitching them together...")
        long_screenshot = Image.new('RGB', (screen_width, total_height))

        current_height = 0
        for screenshot in screenshots:
            long_screenshot.paste(screenshot, (0, current_height))
            current_height += screenshot.height

        filename = datetime.now().strftime("long_screenshot_%Y%m%d_%H%M%S.png")
        filepath = os.path.join(self.config['save_dir'], filename)
        long_screenshot.save(filepath)
        print(f"Long screenshot saved as {filepath}")

        pyautogui.moveTo(mouse_x, mouse_y)
        return filepath


    async def async_screenshot(self):
        return await asyncio.to_thread(pyautogui.screenshot)
    
    async def safe_screenshot(self, timeout=5):
        try:
            return await asyncio.wait_for(self.async_screenshot(), timeout)
        except asyncio.TimeoutError:
            print(f"Screenshot timed out after {timeout} seconds.")
            return None
        

    async def generate_question(self, category, link):
        print(f"Generating {category} question...")
        await self.multimodeManager.multimode_process(category, link)

    def on_press(self, key):
        asyncio.run_coroutine_threadsafe(self._async_on_press(key), self.loop)

    async def _async_on_press(self, key):

        key_char = self.map_key_for_platform(key)

        if key_char is None:
            return

        self.current_keys.add(key_char)
        
        for category, shortcut in self.config['shortcuts'].items():
            if all(k in self.current_keys for k in shortcut):
                if category == "long_screenshot":
                    filepath = await self.take_long_screenshot()
                elif category == "help":
                    await self.run_chatgpt_workflow()
                elif category == "exit":
                    raise KeyboardInterrupt("Exit shortcut triggered")
                else:
                    filepath = self.take_screenshot()

                if filepath:
                    link = self.uploader.upload_and_get_link(filepath, self.link_type)
                    print(f"Generated link: {link}")
                    await self.generate_question(category, link)


    def on_release(self, key):
        key_char = self.map_key_for_platform(key)

        if key_char is None:
            return 
    
        if key_char in self.current_keys:
            self.current_keys.remove(key_char)

    async def run_chatgpt_workflow(self):
        print("Running ChatGPT workflow...")
        await self.chatgpt_manager.run_workflow()

    async def run(self):
        self.loop = asyncio.get_running_loop()
        
        with keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        ) as listener:
            print("Shortcut program is running. Press Ctrl+C to exit.")
            try:
                await asyncio.Event().wait()  # Run forever
            except KeyboardInterrupt:
                print("\nProgram terminated.")
            finally:
                listener.stop()

def listen_key_process():
    manager = ScreenshotManager()
    asyncio.run(manager.run())

if __name__ == "__main__":
    process = Process(target=listen_key_process)
    process.start()
    process.join()