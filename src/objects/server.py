import asyncio
import discord
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
		if packet["type"] == "get_permissions":
			config = await self.client.get_guild_config(int(packet["guild_id"]))["permissions"][packet["permission"]]
			return {
				"granted_when": {
					"big_role_list": list(map(str, config["granted"]["big_roles"])),
					"role_list": list(map(str, config["granted"]["roles"])),
					"channel_list": list(map(str, config["granted"]["channels"]))
				}, "not_granted_when": {
					"role_list": list(map(str, config["granted"]["roles"])),
					"channel_list": list(map(str, config["granted"]["channels"]))
				},
				"default": config["default"]
			}

		elif packet["type"] == "set_permissions":
			query = "UPDATE `guild_permissions` SET `grant_big_roles`=%s, `grant_roles`=%s, `grant_channels`=%s, `dont_grant_roles`=%s, `dont_grant_channels`=%s, `default`=%s WHERE `name`=%s AND `guild_id`=%s"
			arguments = []
			arguments.append(",".join(packet["granted_when"]["big_role_list"]))
			arguments.append(",".join(packet["granted_when"]["role_list"]))
			arguments.append(",".join(packet["granted_when"]["channel_list"]))
			arguments.append(",".join(packet["not_granted_when"]["role_list"]))
			arguments.append(",".join(packet["not_granted_when"]["channel_list"]))
			arguments.append(int(packet["default"]))

			await self.client.db.query(query, *arguments, packet["permission"], packet["guild_id"], fetch=None)
			self.client.cache.remove("get_guild_config", (self.client, int(packet["guild_id"])))

		elif packet["type"] == "get_cogs":
			config = await self.client.get_guild_config(int(packet["guild_id"]))
			response = {"cogs": {}}

			for cog in self.client.config["cogs"]:
				response["cogs"][cog] = cog in config["cogs"]

			return response

		elif packet["type"] == "set_cogs":
			config = await self.client.get_guild_config(int(packet["guild_id"]))
			cogs_in = []
			for cog, enabled in packet["cogs"].items():
				if enabled:
					cogs_in.append(cog)
			for cog in config["cogs"]:
				if cog not in packet["cogs"]:
					cogs_in.append(cog)

			bitnumber = 0
			for cog in cogs_in:
				bitnumber += 1 << self.client.config["cogs_order"][cog]
			await self.client.db.query("UPDATE `guild_configurations` SET `cogs`=%s WHERE `guild_id`=%s", bitnumber, packet["guild_id"], fetch=None)
			self.client.cache.remove("get_guild_config", (self.client, int(packet["guild_id"])))

		elif packet["type"] == "guild_list":
			new_list = []
			user_id = int(packet["user_id"])
			no_channel = discord.Object(0)

			for guild_id in packet["list"]:
				guild = self.client.get_guild(int(guild_id))

				if guild is not None:
					member = await guild.fetch_member(user_id)

					if member is not None:
						if await self.client.has_permission(member, no_channel, "edit_guild_config"):
							new_list.append(guild_id)

			return new_list

		elif packet["type"] == "get_conf":
			conf = await self.client.get_guild_config(int(packet["guild_id"]))
			return {
				"prefix": conf["prefix"],
				"welcome_channel": conf["welcome_channel"],
				"welcome_message": conf["welcome_message"],
				"goodbye_channel": conf["goodbye_channel"],
				"goodbye_message": conf["goodbye_message"]
			}

		elif packet["type"] == "set_conf":
			queries, arguments = "", []

			for index, value in packet["conf"].items():
				queries += f"`{index}`=%s,"
				arguments.append(value)

			await self.client.db.query(f"UPDATE `guild_configurations` SET {queries[:-1]} WHERE `guild_id`=%s", *arguments, packet["guild_id"], fetch=None)
			self.client.cache.remove("get_guild_config", (self.client, int(packet["guild_id"])))

		elif packet["type"] == "get_roles":
			response = []
			guild = self.client.get_guild(int(packet["guild_id"]))

			if guild is not None:
				for role in guild.roles:
					response.append([str(role.id), role.name])

			return response

		elif packet["type"] == "get_channels":
			response = []
			guild = self.client.get_guild(int(packet["guild_id"]))

			if guild is not None:
				for channel in guild.text_channels:
					response.append([str(channel.id), channel.name])

			return response

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
			except ValueError:
				writer.close() # Invalid syntax!
				return
			except:
				return

	async def main(self):
		await asyncio.start_server(self.handle_client, *self.config["web_socket"], loop=self.loop)