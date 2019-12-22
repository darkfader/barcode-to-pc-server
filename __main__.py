#!/usr/bin/env python3.7
# python3.7 -m pip install zeroconf aiohttp

from aiohttp import web, WSMsgType
import json

app = web.Application()


async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    async for msg in ws:
        if msg.type == WSMsgType.TEXT:
            j = json.loads(msg.data)
            if j['action'] == 'helo':
                await ws.send_str(json.dumps({}))
            elif j['action'] == 'ping':
                await ws.send_str(json.dumps({}))
            elif j['action'] == 'getVersion':
                await ws.send_str(json.dumps({}))
            elif j['action'] == 'putScanSessions':
                for session in j['scanSessions']:
                    print(session)
            else:
                await ws.close()
        elif msg.type == WSMsgType.ERROR:
            print('ws connection closed with exception %s' % ws.exception())

    print('websocket connection closed')

    return ws


from zeroconf import ServiceBrowser, Zeroconf, ServiceInfo, _TYPE_ANY
from time import sleep
import socket

TYPE = '_http._tcp.local.'

info = ServiceInfo(type_=TYPE,
                   name=f"barcode-to-pc-server.{TYPE}",
                   server=socket.gethostname(),
                   address=socket.inet_aton("0.0.0.0"),
                   port=57891,
                   properties={'path': '/'})

zeroconf = Zeroconf()  #  ip_version=IPVersion.V6Only)  # IPVersion.All)
print("Registration of a service, press Ctrl-C to exit...")
zeroconf.register_service(info)
try:
    app.add_routes([web.get('/', websocket_handler)])
    web.run_app(app, port=57891, reuse_address=True, reuse_port=True)
except KeyboardInterrupt:
    pass
finally:
    print("Unregistering...")
    zeroconf.unregister_service(info)
    zeroconf.close()
