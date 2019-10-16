from .connector import ButtplugClientConnector, ButtplugClientConnectorError
from ..core.messages import ButtplugMessage
import websockets
import asyncio
import json
from typing import Optional
from logging import getLogger


logger = getLogger("buttplug")


class ButtplugClientWebsocketConnector(ButtplugClientConnector):

    def __init__(self, addr: str):
        super().__init__()
        self.addr: str = addr
        self.ws: Optional[websockets.WebSocketClientProtocol]

    async def connect(self):
        try:
            self.ws = await websockets.connect(self.addr)
        except ConnectionRefusedError as e:
            raise ButtplugClientConnectorError(e)
        self._connected = True
        asyncio.create_task(self._consumer_handler())

    async def _consumer_handler(self):
        # Guessing that this fails out once the websocket disconnects?
        while True:
            try:
                message = await self.ws.recv()
            except Exception as e:
                logger.getChild("websocket").error("Exiting read loop")
                logger.getChild("websocket").error(e)
                break
            msg_array = json.loads(message)
            for msg in msg_array:
                bp_msg = ButtplugMessage.from_dict(msg)
                logger.getChild("websocket").info(bp_msg)
                await self._notify_observers(bp_msg)

    async def send(self, msg: ButtplugMessage):
        msg_str = msg.as_json()
        msg_str = "[" + msg_str + "]"
        logger.getChild("websocket").info(msg_str)
        await self.ws.send(msg_str)

    async def disconnect(self):
        await self.ws.close()
        self._connected = False
