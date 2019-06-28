import threading
import asyncio
import objects
import json
import os

with open("./config.json", "r") as file:
	config = json.loads(file.read())

clientloop = asyncio.get_event_loop()
serverloop = asyncio.new_event_loop()

client = objects.client.Client(objects, config, loop=clientloop)
server = objects.server.Server(objects, client, config, loop=serverloop)
client.server = server

serverloop.create_task(server.main())
threading.Thread(target=serverloop.run_forever).start()
client.run(os.getenv("DISCO_TOKEN"))
# stops the server loop after the client is closed.
serverloop.call_soon_threadsafe(serverloop.stop)