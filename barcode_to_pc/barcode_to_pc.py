import logging
import asyncio
from aiohttp import web, WSMsgType
import json
from zeroconf import ServiceBrowser, Zeroconf, ServiceInfo, _TYPE_ANY
from time import sleep
import socket


async def websocket_handler(request):
    ws = web.WebSocketResponse(autoping=True)
    await ws.prepare(request)

    queue: asyncio.Queue = request.app['queue']

    async for msg in ws:
        if msg.type == WSMsgType.TEXT:
            j = json.loads(msg.data)
            if j['action'] == 'helo':
                request.app.logger.debug(f"helo {j['version']} {j['deviceName']} {j['deviceId']}")
                await ws.send_str(
                    json.dumps({
                        'action': 'helo',
                        'version': "0.9",
                        # 'outputProfiles': [     # ???
                        #     {
                        #         'name': "Output template 1",
                        #         'outputBlocks': [
                        #             { 'name': 'BARCODE', 'value': 'BARCODE', 'type': 'barcode', 'editable': True, 'skipOutput': False },
                        #             { 'name': 'ENTER', 'value': 'enter', 'type': 'key', 'modifiers': [] }
                        #         ]
                        #     },
                        # ],
                    }))
            elif j['action'] == 'ping':
                request.app.logger.debug(f"ping")
                await ws.send_str(json.dumps({'action': 'pong'}))
            elif j['action'] == 'getVersion':
                request.app.logger.debug(f"getVersion")
                await ws.send_str(json.dumps({}))
            elif j['action'] == 'deleteScan':
                request.app.logger.debug(f"deleteScan {j['scanSessionId']} {j['scan']}")
                await ws.send_str(json.dumps({}))
            elif j['action'] == 'deleteScanSessions':
                request.app.logger.debug(f"deleteScanSessions {j['scanSessionIds']}")
                await ws.send_str(json.dumps({}))
            elif j['action'] == 'putScanSessions':
                request.app.logger.debug(f"putScanSessions {j['sendKeystrokes']} {j['deviceId']}")
                for s in j['scanSessions']:
                    request.app.logger.debug(f"{s['id']} {s['name']} {s['date']} {s['selected']}")
                    for c in s['scannings']:
                        request.app.logger.debug(
                            f"{c['id']} {c['repeated']} {c['date']} {c['text']} {c['displayValue']}")
                        # for b in s['outputBlocks']:
                        #     request.app.logger.debug(f"{b['name']} {b['value']} {b['type']}") #, b['editable'], b['skipOutput'], b['modifiers']}")
                        queue.put_nowait(c['text'])

                await ws.send_str(json.dumps({}))
            elif j['action'] == 'updateScanSession':
                request.app.logger.debug(f"updateScanSession {j}")
                await ws.send_str(json.dumps({}))
            elif j['action'] == 'clearScanSessions':
                request.app.logger.debug(f"clearScanSessions {j}")
                await ws.send_str(json.dumps({}))
            else:
                request.app.logger.debug(j)
                await ws.close()
        elif msg.type == WSMsgType.ERROR:
            request.app.logger.info(f"ws connection closed with exception {ws.exception()}")

    request.app.logger.info("websocket connection closed")

    return ws


class Server:
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        # self.logger.setLevel(logging.DEBUG)

        TYPE = '_http._tcp.local.'
        self.info = ServiceInfo(
            type_=TYPE,
            name=f"barcode-to-pc-server.{TYPE}",
            server=socket.gethostname(),
            address=None,  #socket.inet_aton("0.0.0.0"),
            port=57891,
            properties={'path': '/'})
        self.zeroconf = Zeroconf()  #  ip_version=IPVersion.V6Only)  # IPVersion.All)

    async def start(self, queue: asyncio.Queue, loop=None):
        self.logger.debug("server")
        app = web.Application(logger=self.logger, loop=loop)
        app['queue'] = queue
        app.add_routes([web.get('/', websocket_handler)])
        # web.run_app(app, port=57891, reuse_address=True, reuse_port=True)
        self.runner = web.AppRunner(app)  #, handle_signals=True)

        self.logger.info("Registration of the service...")
        self.zeroconf.register_service(self.info)

        await self.runner.setup()
        self.site = web.TCPSite(self.runner, port=57891, reuse_address=True, reuse_port=True)
        self.logger.debug("start...")
        await self.site.start()

    async def stop(self):
        await self.runner.cleanup()
        self.logger.info("Unregistering...")
        self.zeroconf.unregister_service(self.info)
        self.zeroconf.close()
