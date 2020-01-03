#!/usr/bin/env python3.7
# python3.7 -m pip install zeroconf aiohttp

import logging
import asyncio
from barcode_to_pc.barcode_to_pc import Server


async def main(server):
    loop = asyncio.get_running_loop()

    queue = asyncio.Queue()

    async def test():
        while True:
            code = await queue.get()
            print(code)

    await server.start(queue, loop=loop)

    await test()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    server = Server()
    try:
        asyncio.run(main(server))
    except KeyboardInterrupt as e:
        asyncio.run(server.stop())
    finally:
        pass
