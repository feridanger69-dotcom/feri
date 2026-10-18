"""Run on the Kermanshah laptop. Only files inside the user's home folder are accessible."""
import asyncio, base64, json, os
from pathlib import Path
import websockets

PAIR_CODE = "MyLaptop-7264-private"
RELAY_URL = os.getenv("RELAY_URL", "wss://YOUR-RAILWAY-DOMAIN/ws")
HOME = Path.home().resolve()
MAX_FILE_BYTES = 20 * 1024 * 1024

def safe_path(raw):
    p = (HOME / raw).resolve()
    if p != HOME and HOME not in p.parents:
        raise ValueError("فقط به فایل‌های داخل پوشه کاربر دسترسی داری")
    return p

async def main():
    url = RELAY_URL.rstrip("/")
    if "YOUR-RAILWAY-DOMAIN" in url:
        print("اول RELAY_URL را با آدرس Railway خودت تنظیم کن.")
        return
    while True:
        try:
            async with websockets.connect(url, max_size=MAX_FILE_BYTES * 2, ping_interval=20) as ws:
                await ws.send(json.dumps({"role": "agent", "code": PAIR_CODE}))
                print("Agent کرمانشاه وصل شد؛ برای خروج Ctrl+C بزن.")
                async for raw in ws:
                    req = json.loads(raw)
                    out = {"id": req.get("id"), "ok": False}
                    try:
                        action = req.get("action")
                        p = safe_path(req.get("path", "."))
                        if action == "list":
                            if not p.is_dir(): raise ValueError("این مسیر پوشه نیست")
                            out["items"] = [{"name": x.name, "is_dir": x.is_dir()} for x in sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))]
                            out["ok"] = True
                        elif action == "get":
                            if not p.is_file(): raise ValueError("فایل پیدا نشد")
                            if p.stat().st_size > MAX_FILE_BYTES: raise ValueError("فایل بزرگ‌تر از ۲۰ مگابایت است")
                            out["data"] = base64.b64encode(p.read_bytes()).decode("ascii")
                            out["ok"] = True
                        else: raise ValueError("درخواست نامعتبر")
                    except Exception as e:
                        out["error"] = str(e)
                    await ws.send(json.dumps(out))
        except (OSError, websockets.WebSocketException) as e:
            print("اتصال قطع شد؛ ۵ ثانیه دیگر تلاش می‌کنم:", e)
            await asyncio.sleep(5)

if __name__ == "__main__":
    try: asyncio.run(main())
    except KeyboardInterrupt: pass
