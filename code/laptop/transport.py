"""One authenticated robot per server; no work may outlive its connection."""
import asyncio
import hmac
import time
from protocol import SESSION, decode_text
from speech import Segmenter

class RobotLink:
    def __init__(self, bob):
        self.bob = bob

    async def heartbeat(self, ws):
        while self.bob.ws is ws:
            await self.bob.send(type="ping")
            if self.bob.listening_until and time.monotonic() >= self.bob.listening_until:
                self.bob.listening_until = 0
                await self.bob.send(type="listen", active=False)
            await asyncio.sleep(0.4)

    async def handle(self, ws):
        bob = self.bob
        # Do not mutate active session state before authentication and ownership checks.
        auth = ws.request.headers.get_all("Authorization")
        expected = "Bearer " + bob.token
        if ws.request.path != "/bob" or len(auth) != 1 or not hmac.compare_digest(auth[0], expected):
            await ws.close(1008, "authentication required")
            return
        if bob.ws is not None:
            await ws.close(1008, "robot already connected")
            return
        bob.ws = ws
        bob.status = {}
        bob.segmenter = Segmenter()
        bob.listening_until = 0
        bob.sequence = 0
        marker = SESSION.set(ws)
        heartbeat = asyncio.create_task(self.heartbeat(ws))
        try:
            async for raw in ws:
                if isinstance(raw, bytes):
                    await bob.on_binary(raw)
                else:
                    await bob.on_text(decode_text(raw))
                if heartbeat.done():
                    heartbeat.result()
        except Exception as exc:
            print(f"Robot connection ended: {exc}")
            await ws.close(1008, "invalid frame or link error")
        finally:
            heartbeat.cancel()
            await asyncio.gather(heartbeat, return_exceptions=True)
            if bob.photo_waiter and not bob.photo_waiter.done():
                bob.photo_waiter.cancel()
            await bob.cancel_work()
            bob.segmenter = Segmenter()
            bob.listening_until = 0
            if bob.ws is ws:
                bob.ws = None
            SESSION.reset(marker)
