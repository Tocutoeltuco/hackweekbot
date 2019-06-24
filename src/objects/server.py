import asyncio
import json

class Server:
	def __init__(self, objects, client, config, loop=None):
		self.loop = loop or asyncio.new_event_loop()
		self.objects = objects
		self.client = client
		self.config = config

	async def send(self, writer, packet):
		data = json.dumps(packet).encode()
		length = len(data)

		writer.write(bytes([(length >> 8) & 255, length & 255]) + data)
		await writer.drain()

	async def recv(self, reader):
		length = await reader.read(2)
		return json.loads(await reader.read(length[0] << 8 + length[1]))

	async def parse_packet(self, packet):
		if packet["type"] == "update_guild":
			self.client.cache.remove("get_guild_config", (self.client, packet["guild"]))

	async def handle_client(self, reader, writer):
		while True:
			await asyncio.sleep(.1)
			try:
				packet = await parse_packet(await self.recv(reader))

				if packet is not None:
					await self.send(writer, packet)
			except KeyError:
				writer.close() # Invalid syntax!
				return
			except:
				return

	async def main(self):
		await asyncio.start_server(self.handle_client, self.config["web_socket"][0], self.config["web_socket"][1], loop=self.loop)