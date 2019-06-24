import asyncio
import objects
import json

with open("./config.json", "r") as file:
	config = json.loads(file.read())

loop = asyncio.get_event_loop()
client = objects.client.Client(objects, config, loop=loop)
client.run(config["token"])