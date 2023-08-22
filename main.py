#! /usr/bin/env python3
import time

from aiohttp import web
import json
import asyncio

from crosslab.api_client import APIClient
from crosslab.soa_client.device_handler import DeviceHandler
from crosslab.soa_services.message import MessageService__Producer, MessageService__Consumer, MessageServiceEvent
from latency import Latency

LED_ON_MESSAGE = "_led=on"
LED_OFF_MESSAGE = "led=off"

PROTOCOL_TCP = "TCP"
PROTOCOL_UDP = "UDP"


async def main_async():
    latency_calc = Latency()

    async def run_server():
        app = web.Application()
        app.router.add_route('GET', '/', handle_index)
        app.router.add_route('GET', '/ledon', handle_led_on)
        app.router.add_route('GET', '/ledoff', handle_led_off)
        app.router.add_route('GET', '/start_tcp', start_measurement_tcp)
        app.router.add_route('GET', '/start_udp', start_measurement_udp)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', 8000)
        await site.start()

    async def handle_index(request):
        # Read the contents of the index.html file
        with open('index.html', 'r') as f:
            html_content = f.read()

        # Return the HTML content as the response
        return web.Response(text=html_content, content_type='text/html')

    async def handle_led_on(request):
        print("led on")
        latency_calc.start()
        await messageServiceProducer.sendMessage(f"{LED_ON_MESSAGE};{PROTOCOL_TCP}", "info")
        return web.Response(text="LED turned on")

    async def handle_led_off(request):
        print("led off")
        latency_calc.start()
        await messageServiceProducer.sendMessage(f"{LED_OFF_MESSAGE};{PROTOCOL_TCP}", "info")
        return web.Response(text="LED turned off")

    async def start_measurement_tcp(request):
        print("Start measurement")
        await measurement_task(PROTOCOL_TCP)
        return web.Response(text="Finished!")

    async def start_measurement_udp(request):
        print("Start measurement")
        await measurement_task(PROTOCOL_UDP)
        return web.Response(text="Finished!")

    async def measurement_task(protocol):
        for i in range(0, 100):
            print(f"Iteration: {i} {protocol}")
            if (i % 2) == 0:
                latency_calc.start()
                await messageServiceProducer.sendMessage(f"{LED_ON_MESSAGE};{protocol}", "info")
                await asyncio.sleep(3)
            else:
                latency_calc.start()
                await messageServiceProducer.sendMessage(f"{LED_OFF_MESSAGE};{protocol}", "info")
                await asyncio.sleep(3)

        await asyncio.sleep(3)
        latency_calc.cleanUpData()
        latency_calc.calculateRTTJitter()
        latency_calc.calculateOWDMetrics()
        latency_calc.calculateRTTMetrics()
        latency_calc.saveAsJSON()
        latency_calc.saveMetricsAsTxt()

    # read config from file
    with open("config.json", "r") as configfile:
        conf = json.load(configfile)

    # debug; delete for prod
    print(conf)

    deviceHandler = DeviceHandler()

    # --------------------------------------------------------------#
    #   I/O                                                         #
    # --------------------------------------------------------------#
    # message service:
    messageServiceProducer = MessageService__Producer("messageP")
    deviceHandler.add_service(messageServiceProducer)

    messageServiceConsumer = MessageService__Consumer("messageC")

    async def onMessage(message: MessageServiceEvent):
        print("Received Message of type", message["message_type"])
        print("Message content:", message["message"])
        latency_calc.calculateLatency(message["message"])
        latency_calc.printLatency()

    messageServiceConsumer.on("message", onMessage)
    deviceHandler.add_service(messageServiceConsumer)
    url = conf["auth"]["deviceURL"]

    async with APIClient(url) as client:
        client.set_auth_token(conf["auth"]["deviceAuthToken"])
        # Create the HTTP server as a coroutine task
        server_task = asyncio.create_task(run_server())

        deviceHandlerTask = asyncio.create_task(
            deviceHandler.connect("{url}/devices/{did}".format(
                url=conf["auth"]["deviceURL"],
                did=conf["auth"]["deviceID"]
            ), client)
        )

        await asyncio.gather(server_task, deviceHandlerTask)


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
