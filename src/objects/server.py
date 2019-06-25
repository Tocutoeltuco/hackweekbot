import asyncio
import json

class Server:
	def __init__(self, objects, client, config, loop=None):
		self.loop = loop or asyncio.new_event_loop()
		self.objects = objects
		self.client = client
		self.config = config

	async def send(self, writer, packet):
		writer.write(json.dumps(packet).encode() + b"\x01")
		await writer.drain()

	async def recv(self, reader):
		return json.loads((await reader.readuntil(b"\x01"))[:-1])

	async def parse_packet(self, packet):
		if packet["type"] == "update_guild":
			self.client.cache.remove("get_guild_config", (self.client, int(packet["guild"])))

	async def handle_client(self, reader, writer):
		if writer.get_extra_info("peername")[0] not in self.config["remote_web_socket"]:
			writer.close() # The IP is not whitelisted!
			return

		while True:
			await asyncio.sleep(.1)
			try:
				packet = await self.parse_packet(await self.recv(reader))

				if packet is not None:
					await self.send(writer, packet)
			except KeyError:
				writer.close() # Invalid syntax!
				return
			except:
				return

	async def main(self):
		await asyncio.start_server(self.handle_client, *self.config["web_socket"], loop=self.loop)