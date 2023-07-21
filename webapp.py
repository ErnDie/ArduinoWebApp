#!/usr/bin/env python

from main import *
import asyncio


class MyRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/ledon":
            asyncio.run(turnLEDOn())
            self.send_response(200)
            self.end_headers()
        elif self.path == "/ledoff":
            asyncio.run(turnLEDOff())
            self.send_response(200)
            self.end_headers()
        elif self.path == "/":
            with open('index.html', "rb") as file:
                content = file.read()
            self.send_response(200)
            self.end_headers()
            # Send a response message back to the HTML page
            self.wfile.write(content)


async def turnLEDOn():
    print("led on")
    await messageServiceProducer.sendMessage("led=on", 'info')


async def turnLEDOff():
    print("led off")
    await messageServiceProducer.sendMessage("led=off", 'info')


def run_server():
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, MyRequestHandler)
    print('Starting server...')
    httpd.serve_forever()


subprocess.Popen(["python", "main.py"])
run_server()
