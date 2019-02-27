import asyncio
from enum import IntEnum

from dczd_simserver_agent.tcp_client import TcpClient

class Message(IntEnum):
    LIABILITY = 2
    LIABILITY_FINISH = 3

class Client:
    result_msg = ''

    def __init__(self):
        self.__loop = asyncio.get_event_loop()
        address, port = "18.191.118.91:3344".split(':')
        port = int(port)

        drone = 'salvor'
        contract = 'toxic_accident'

        self.proxy_client = TcpClient(self.on_message, address, port, self.__loop)
        self.__main_task = asyncio.ensure_future(self.create_main_task(drone, contract))

    def send_liability(self, drone, contract):
        self.proxy_client.write_msg({
            'type': int(Message.LIABILITY),
            'drone': drone,
            'contract': contract,
        })

    def on_message(self, send, msg):
        print('got %s message' % Message(msg['type']))
        if msg['type'] == Message.LIABILITY_FINISH:
            print("got measurements: ", msg['measurements'])
            self.result_msg = msg['measurements']
            self.__main_task.cancel()

    async def create_main_task(self, drone, contract):
        await self.proxy_client.connect()
        self.send_liability(drone, contract)
        try:
            await self.proxy_client.read_msgs()
        except asyncio.CancelledError:
            pass

    def run(self):
        try:
            self.__loop.run_until_complete(self.__main_task)
        finally:
            self.__loop.close()

