import asyncio
import json
import sys

from datetime import datetime, timedelta
from functools import wraps

class throttle(object):
    """
    Decorator that prevents a function from being called more than once every
    time period.
    To create a function that cannot be called more than once a minute:
        @throttle(minutes=1)
        def my_fun():
            pass
    """
    def __init__(self, seconds=0, minutes=0, hours=0):
        self.throttle_period = timedelta(
            seconds=seconds, minutes=minutes, hours=hours
        )
        self.time_of_last_call = datetime.min

    def __call__(self, fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            now = datetime.now()
            time_since_last_call = now - self.time_of_last_call

            if time_since_last_call > self.throttle_period:
                self.time_of_last_call = now
                return fn(*args, **kwargs)

        return wrapper


def log(*args, **kwargs):
    print(*args, **kwargs)


def log_error(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr)

def log_exception():
    import traceback
    traceback.print_exc()

def log_throttle(sec, *args, **kwargs):
    @throttle(seconds=sec)
    def impl():
        print(*args, **kwargs)
    impl()

class TcpClient:
    def __init__(self, on_message, address, port, loop=None):
        self.on_message = on_message
        self.__address = address
        self.__port = port
        self.__loop = loop
        self._reset_state()

    def _reset_state(self):
        self.buffer = b''

    async def run(self):
        while True:
            log('trying to connect')
            await self.connect()
            await self.read_msgs()


    async def connect(self):
        while True:
            try:
                conn = await asyncio.open_connection(self.__address, self.__port, loop=self.__loop)
            except ConnectionRefusedError:
                log_throttle(3, 'connection refused')
            except BaseException as e:
                log_error(e)
            else:
                assert conn is not None
                self.__reader, self.__writer = conn
                log('connected')
                break


    def _on_connection_error(self, e):
        log_error('connection error', str(e))
        self.disconnect()

    async def read_msgs(self):
        while True:
            try:
                self.buffer += await self.__reader.read(4 - len(self.buffer))
                if len(self.buffer) < 4:
                    return

                size = int.from_bytes(self.buffer, byteorder='little')
                self.buffer = b''
                # log('got size %d', size)

                msg = await self.__reader.readexactly(size)
            except ConnectionError as e:
                self._on_connection_error(e)
                break

            try:
                msg = json.loads(msg.decode())
                log('received message\n', msg)
                self.on_message(self.write_msg, msg)
            except BaseException:
                log_exception()

    def write_msg(self, msg):
        log('sending msg\n', msg)
        try:
            msg_str = json.dumps(msg)
            self.__writer.write(len(msg_str).to_bytes(4, byteorder='little'))
            self.__writer.write(msg_str.encode())
        except ConnectionError as e:
            self._on_connection_error(e)
        except BaseException:
            log_exception()

    def disconnect(self):
        if self.__writer:
            self.__writer.close()
        self._reset_state()
