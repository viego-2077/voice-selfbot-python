#They're all vibe codes.

















































































































































































































































































































































































































































































































import sys
import subprocess
import importlib

def check_and_install(packages):
    for pkg in packages:
        try:
            importlib.import_module(pkg)
        except ImportError:
            print(f"[*] thiếu thư viện '{pkg}', đang cài đặt...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
                print(f"[+] Đã cài đặt thành công: {pkg}\n")
            except Exception as e:
                print(f"[-] Lỗi khi cài đặt {pkg}: {e}")
                print("Vui lòng mở CMD và gõ thủ công: pip install aiohttp websockets")
                sys.exit(1)


check_and_install(['aiohttp', 'websockets'])


banner = r"""
 ██████╗  ██████╗ ███████╗███████╗    ██╗   ██╗ ██████╗ ██╗ ██████╗███████╗
╚════██╗ ██╔═══██╗╚════██║╚════██║    ██║   ██║██╔═══██╗██║██╔════╝██╔════╝
 █████╔╝ ██║   ██║    ██╔╝    ██╔╝    ██║   ██║██║   ██║██║██║     █████╗  
██╔═══╝  ██║   ██║   ██╔╝    ██╔╝     ╚██╗ ██╔╝██║   ██║██║██║     ██╔══╝  
███████╗ ╚██████╔╝   ██║     ██║       ╚████╔╝ ╚██████╔╝██║╚██████╗███████╗
╚══════╝  ╚═════╝    ╚═╝     ╚═╝        ╚═══╝   ╚═════╝ ╚═╝ ╚═════╝╚══════╝
            =================================================
                       TOOL TREO ROOM TỐC ĐỘ CAO       
                       Made with ♥️ and 🔥 by 2077  
            =================================================
    """


import os
import sys
import time
import json
import asyncio
import aiohttp
import websockets
import random
from datetime import datetime

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

async def fetch_guild_id_for_channel(session, token, channel_id):
    headers = {"Authorization": token, "Content-Type": "application/json"}
    try:
        async with session.get(f"https://discord.com/api/v9/channels/{channel_id}", headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get("guild_id")
    except Exception as e:
        pass
    return None

class ProHangVoice:
    def __init__(self, token, channel_id, mute, deaf, stream, session, bot_index):
        self.token = token
        self.channel_id = str(channel_id)
        self.mute = mute
        self.deaf = deaf
        self.stream = stream
        self.session = session
        self.bot_index = bot_index
        
        self.ws = None
        self.guild_id = None
        self.session_id = None
        self.seq = None
        self.heartbeat_interval = 41.25
        self.is_running = True
        
        self.listen_task = None
        self.heartbeat_task = None

    def log(self, message):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [Token {self.bot_index}] {message}")

    async def start(self):
        self.guild_id = await fetch_guild_id_for_channel(self.session, self.token, self.channel_id)
        if not self.guild_id:
            self.log("không tìm thấy máy chủ")
            return

        while self.is_running:
            try:
                await self.connect()
            except Exception as e:
                self.log(f"Mất kết nối: {e}. Đang thử lại sau 5s...")
                await asyncio.sleep(5)

    async def connect(self):
        url = "wss://gateway.discord.gg/?v=9&encoding=json"
        async with websockets.connect(url, max_size=None) as ws:
            self.ws = ws
            
            if self.session_id and self.seq:
                await self.ws.send(json.dumps({
                    "op": 6,
                    "d": {"token": self.token, "session_id": self.session_id, "seq": self.seq}
                }))
            else:
                await self.ws.send(json.dumps({
                    "op": 2,
                    "d": {
                        "token": self.token,
                        "capabilities": 16381,
                        "properties": {"$os": "windows", "$browser": "chrome", "$device": "pc"},
                        "presence": {"status": "online", "since": 0, "activities": [], "afk": False},
                        "intents": 641
                    }
                }))

            self.listen_task = asyncio.create_task(self.listen())
            await self.listen_task

    async def listen(self):
        try:
            async for message in self.ws:
                data = json.loads(message)
                op = data.get("op")
                t = data.get("t")
                d = data.get("d")
                s = data.get("s")

                if s is not None:
                    self.seq = s

                if op == 10:
                    self.heartbeat_interval = d["heartbeat_interval"] / 1000
                    if self.heartbeat_task:
                        self.heartbeat_task.cancel()
                    self.heartbeat_task = asyncio.create_task(self.keep_alive())

                elif op == 0: 
                    if t == "READY":
                        self.session_id = d["session_id"]
                        self.log("Đăng nhập thành công! Đang kết nối Voice...")
                        await self.join_voice()
                        
                    elif t == "VOICE_SERVER_UPDATE":
                        if self.stream:
                            self.log("đang kích hoạt Stream...")
                            await self.fire_stream()

                elif op == 9:
                    self.log("Phiên hết hạn, đang tạo phiên mới...")
                    self.session_id = None
                    self.seq = None
                    return

        except websockets.exceptions.ConnectionClosed:
            self.log("Websocket bị đóng.")
        finally:
            if self.heartbeat_task:
                self.heartbeat_task.cancel()

    async def keep_alive(self):
        try:
            await asyncio.sleep(self.heartbeat_interval * random.uniform(0, 1))
            
            while self.is_running and getattr(self.ws, 'closed', False) is False:
                
                self.log(f"Piu Piu Heartbeat!") 
                
                await self.ws.send(json.dumps({"op": 1, "d": self.seq}))
                await asyncio.sleep(self.heartbeat_interval)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.log(f"Lỗi Heartbeat: {e}")

    async def join_voice(self):
        payload = {
            "op": 4,
            "d": {
                "guild_id": self.guild_id,
                "channel_id": self.channel_id,
                "self_mute": self.mute,
                "self_deaf": self.deaf,
                "self_video": False,
                "self_stream": self.stream
            }
        }
        await self.ws.send(json.dumps(payload))

    async def fire_stream(self):
        stream_payload = {
            "op": 18,
            "d": {
                "type": "guild",
                "guild_id": self.guild_id,
                "channel_id": self.channel_id,
                "preferred_region": "singapore",
                "quality": 100,
                "framerate": 30,
                "width": 1280,
                "height": 720
            }
        }
        await self.ws.send(json.dumps(stream_payload))

async def async_main():
    clear_screen()
    print(f"\033[96m{banner}\033[0m")
    
    token_file = input("Nhập file token: ")
    if not os.path.exists(token_file):
        print("Không tìm thấy file!")
        return
        
    channel_id = input("Nhập ID Channel Voice: ")
    mute = input("Tắt Mic? (y/n): ").lower() == 'y'
    deaf = input("Tắt Loa? (y/n): ").lower() == 'y'
    stream = input("Bật Stream? (y/n): ").lower() == 'y'

    with open(token_file, 'r') as f:
        tokens = [line.strip() for line in f if line.strip()]

    print(f"\nđang khởi động {len(tokens)} luồng")
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i, token in enumerate(tokens):
            bot = ProHangVoice(token, channel_id, mute, deaf, stream, session, i + 1)
            tasks.append(asyncio.create_task(bot.start()))
            await asyncio.sleep(0.2)
            
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\nbot shutdown!")
        
