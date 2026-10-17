import argparse
import array
import asyncio
import datetime as dt
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import AsyncMock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"code/laptop"))
import server
from protocol import decode_text, validate_binary, validate_outgoing, SESSION, SessionGone
from speech import Segmenter, scale_pcm
from reminders import Reminders, parse_when
from transport import RobotLink
from websockets.asyncio.server import serve
from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed

TOKEN = "1" * 64

class ProtocolTests(unittest.TestCase):
    def test_reject_malformed_json_and_types(self):
        for raw in ['[]', 'null', '{', '{"type":5}', '{"type":"status","v":NaN}', ' '*16385]:
            with self.subTest(raw=raw[:50]), self.assertRaises((ValueError, json.JSONDecodeError)):
                decode_text(raw)

    def test_motion_limits_and_types(self):
        validate_outgoing(dict(type="move",dir="forward",duty=40,ms=400))
        for d, duty, ms in [("reverse",30,100),("pivot_left",30,251),("forward",41,100),("forward",True,100),("forward",30,-1),("forward",30,1.5)]:
            with self.subTest(d=d,duty=duty,ms=ms), self.assertRaises(ValueError):
                validate_outgoing(dict(type="move",dir=d,duty=duty,ms=ms))

    def test_binary_bounds(self):
        self.assertEqual(validate_binary(b'A\x00\x00'), (65,b'\x00\x00'))
        for data in [b'',b'A',b'A\0',b'A'+bytes(1282),b'X12',b'Ibad']:
            with self.subTest(data=data[:8]), self.assertRaises(ValueError): validate_binary(data)

    def test_audio_segmentation_is_bounded(self):
        segmenter = Segmenter()
        loud = array.array('h',[3000,-3000]*320).tobytes()
        utterances=[]
        for _ in range(250):
            result=segmenter.feed(loud)
            if result: utterances.append(result)
        self.assertTrue(utterances)
        self.assertLessEqual(max(map(len,utterances)), 16000*2*8+1280)
        self.assertLessEqual(len(segmenter.pre),8000)
        with self.assertRaises(ValueError): segmenter.feed(b'\0')

    def test_pcm_clipping(self):
        values=array.array('h',scale_pcm(array.array('h',[32767,-32768]).tobytes(),2))
        self.assertEqual(list(values),[32767,-32768])

    def test_reminders_persist_and_validate_time(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'reminders.db'
            r=Reminders(path)
            rid=r.add(dt.datetime.now()-dt.timedelta(minutes=1),'read time book')
            self.assertEqual(len(r.due()),1)
            r.db.close(); r=Reminders(path)
            self.assertEqual(r.pending()[0][0],rid)
            r.done(rid); self.assertFalse(r.due()); r.db.close()
        for value in [['25:00'],['2026-02-30','10:00'],[]]: self.assertIsNone(parse_when(value))

class BobFixture:
    async def asyncSetUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.dbpatch=patch.object(server,'DB_PATH',Path(self.tmp.name)/'db')
        self.photopatch=patch.object(server,'PHOTOS',Path(self.tmp.name)/'photos')
        self.dbpatch.start(); self.photopatch.start()
        self.bob=server.Bob(argparse.Namespace(no_stt=True,model='tiny.en',volume=.4,duty=30,verbose=False,token=TOKEN))

    async def asyncTearDown(self):
        await self.bob.cancel_work()
        self.bob.reminders.db.close()
        self.dbpatch.stop(); self.photopatch.stop(); self.tmp.cleanup()

class BobTests(BobFixture, unittest.IsolatedAsyncioTestCase):
    async def test_negated_move_does_not_move(self):
        self.bob.send=AsyncMock(); self.bob.say=AsyncMock()
        await self.bob.command('do not move forward')
        self.assertFalse(any(c.kwargs.get('type')=='move' for c in self.bob.send.call_args_list))

    async def test_reminder_title_not_executed(self):
        self.bob.send=AsyncMock(); self.bob.say=AsyncMock()
        await self.bob.command('remind me to read the time at 6 30 pm')
        self.assertEqual(self.bob.reminders.pending()[0][3],'read the time')

    async def test_old_session_cannot_send(self):
        old=object(); self.bob.ws=AsyncMock()
        marker=SESSION.set(old)
        try:
            with self.assertRaises(SessionGone): await self.bob.send(type='stop')
        finally: SESSION.reset(marker)
        self.bob.ws.send.assert_not_called()

    async def test_photo_timeout_releases_slot(self):
        self.bob.send=AsyncMock()
        self.assertIsNone(await self.bob.take_photo(.01))
        self.assertIsNone(self.bob.photo_waiter)

    async def test_photo_requests_are_serialized(self):
        self.bob.send=AsyncMock()
        first=asyncio.create_task(self.bob.take_photo(1))
        await asyncio.sleep(.01)
        first_waiter=self.bob.photo_waiter
        second=asyncio.create_task(self.bob.take_photo(1))
        await asyncio.sleep(.01)
        self.assertIs(self.bob.photo_waiter,first_waiter)
        await self.bob.on_binary(b'I\xff\xd8test\xff\xd9')
        path1=await first
        await asyncio.sleep(.01)
        await self.bob.on_binary(b'I\xff\xd8test\xff\xd9')
        path2=await second
        self.assertNotEqual(path1,path2)

    async def test_sequence_order(self):
        self.bob.ws=AsyncMock()
        await asyncio.gather(*(self.bob.send(type='ping') for _ in range(10)))
        seq=[json.loads(c.args[0])['seq'] for c in self.bob.ws.send.call_args_list]
        self.assertEqual(seq,list(range(1,11)))

    async def test_bounded_tasks(self):
        for _ in range(9): self.bob.spawn(asyncio.sleep(1))
        self.assertEqual(len(self.bob.tasks),8)

class LinkTests(BobFixture, unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await super().asyncSetUp()
        self.listener=await serve(RobotLink(self.bob).handle,'127.0.0.1',0,max_size=524289,compression=None)
        self.url=f'ws://127.0.0.1:{self.listener.sockets[0].getsockname()[1]}/bob'

    async def asyncTearDown(self):
        self.listener.close(); await self.listener.wait_closed()
        await super().asyncTearDown()

    async def test_authentication_and_single_owner(self):
        async with connect(self.url) as bad:
            with self.assertRaises(ConnectionClosed): await bad.recv()
        async with connect(self.url,additional_headers={'Authorization':'Bearer '+TOKEN}) as good:
            first=json.loads(await good.recv()); self.assertEqual(first['type'],'ping')
            async with connect(self.url,additional_headers={'Authorization':'Bearer '+TOKEN}) as second:
                with self.assertRaises(ConnectionClosed): await second.recv()
            await good.send('{"type":"status","battery_v":3.9}')
            await asyncio.sleep(.02)
            self.assertEqual(self.bob.status['battery_v'],3.9)

    async def test_malformed_disconnect_and_reconnect(self):
        async with connect(self.url,additional_headers={'Authorization':'Bearer '+TOKEN}) as ws:
            await ws.recv(); await ws.send('[]')
            with self.assertRaises(ConnectionClosed): await ws.recv()
        await asyncio.sleep(.02)
        async with connect(self.url,additional_headers={'Authorization':'Bearer '+TOKEN}) as ws:
            self.assertEqual(json.loads(await ws.recv())['seq'],1)

    async def test_heartbeat_and_move_delivery(self):
        async with connect(self.url,additional_headers={'Authorization':'Bearer '+TOKEN}) as ws:
            await ws.recv()
            await self.bob.console('move pivot_left')
            command=json.loads(await ws.recv())
            self.assertEqual(command['ms'],200)
            self.assertEqual(command['token'],TOKEN)
            self.assertEqual(json.loads(await asyncio.wait_for(ws.recv(),.7))['type'],'ping')

    async def test_disconnect_cancels_pending_commands(self):
        async with connect(self.url,additional_headers={'Authorization':'Bearer '+TOKEN}) as ws:
            await ws.recv()
            self.bob.spawn(asyncio.sleep(30))
        for _ in range(50):
            if self.bob.ws is None: break
            await asyncio.sleep(.01)
        self.assertIsNone(self.bob.ws)
        self.assertFalse(self.bob.tasks)
