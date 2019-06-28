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
		print("Sent", packet)

	async def recv(self, reader):
		result = json.loads((await reader.readuntil(b"\x01"))[:-1])
		print("Received", result)
		return result

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
			queries, arguments = "", []

			for name, permission in packet["permissions"].items():
				queries += """
				INSERT INTO `guild_permissions` (
					`name`, `guild_id`,
					`grant_big_roles`, `grant_big_roles`, `grant_roles`, `grant_channels`,
					`dont_grant_roles`, `dont_grant_channels`,
					`default`
				) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
				ON DUPLICATE KEY UPDATE `grant_big_roles`=%s, `grant_roles`=%s, `grant_channels`=%s, `dont_grant_roles`=%s, `dont_grant_channels`=%s, `default`=%s;
				"""
				arguments.append(name)
				arguments.append(packet["guild_id"])
				arguments.append(",".join(permission["granted_when"]["big_role_list"]))
				arguments.append(",".join(permission["granted_when"]["role_list"]))
				arguments.append(",".join(permission["granted_when"]["channel_list"]))
				arguments.append(",".join(permission["not_granted_when"]["role_list"]))
				arguments.append(",".join(permission["not_granted_when"]["channel_list"]))
				arguments.append(int(permission["default"]))
				arguments.append(",".join(permission["granted_when"]["big_role_list"]))
				arguments.append(",".join(permission["granted_when"]["role_list"]))
				arguments.append(",".join(permission["granted_when"]["channel_list"]))
				arguments.append(",".join(permission["not_granted_when"]["role_list"]))
				arguments.append(",".join(permission["not_granted_when"]["channel_list"]))
				arguments.append(int(permission["default"]))

			await self.client.db.query(queries, *arguments, fetch=None)
			self.client.cache.remove("get_guild_config", (self.client, int(packet["guild_id"])))

		elif packet["type"] == "guild_info":
			response = {
				"name": None,
				"icon": None,
				"cogs": {},
				"conf": {},
				"roles": [],
				"channels": [],
				"permissions": {}
			}

			guild = self.client.get_guild(int(packet["guild_id"]))

			if guild is not None:
				config = await self.client.get_guild_config(guild.id)

				for permission, data in config["permissions"].items():
					response["permissions"][permission] = {
						"big_roles": list(map(str, config["granted"]["big_roles"])),
						"allowed_channels": list(map(str, config["granted"]["channels"])),
						"allowed_roles": list(map(str, config["granted"]["roles"])),
						"denied_channels": list(map(str, config["granted"]["channels"])),
						"denied_roles": list(map(str, config["granted"]["roles"])),
						"default": config["default"]
					}

				cogs = {}
				conf = {
					"prefix": config["prefix"],
					"welcome_channel": config["welcome_channel"],
					"welcome_message": config["welcome_message"],
					"goodbye_channel": config["goodbye_channel"],
					"goodbye_message": config["goodbye_channel"]
				}
				cogs["testcog"] = "cogs.testcog" in config["cogs"]
				for cog in self.client.config["cogs"]:
					cogs[cog.split(".")[1]] = cog in config["cogs"]

				for role in guild.roles:
					response["roles"].append([str(role.id), role.name])

				for channel in guild.text_channels:
					response["channels"].append([channel.category.name if channel.category else None, str(channel.id), channel.name])

				response["name"] = guild.name
				response["icon"] = str(guild.icon_url)
				response["cogs"] = cogs
				response["conf"] = conf

			return response

		elif packet["type"] == "set_guild_info":
			guild = self.client.get_guild(int(packet["guild_id"]))

			if guild is not None:
				config = await self.client.get_guild_config(guild.id)
				query = """
				INSERT INTO `guild_configurations` (
					`guild_id`, `prefix`,
					`welcome_channel`, `welcome_message`,
					`goodbye_channel`, `goodbye_message`,
					`cogs`
				) VALUES (%s, %s, %s, %s, %s, %s, %s)
				ON DUPLICATE KEY UPDATE `prefix`=%s, `welcome_channel`=%s, `welcome_message`=%s, `goodbye_channel`=%s, `goodbye_message`=%s, `cogs`=%s
				"""

				cogs = config["cogs"].copy()
				for cog, enabled in packet["cogs"].items():
					cog = "cogs." + cog

					if cog in cogs:
						if not enabled:
							del cogs[cogs.index(cog)]
					else:
						if enabled:
							cogs.append(cog)
				bitnumber = 0
				for cog in cogs:
					bitnumber += 1 << self.client.configs["cogs_order"][cog]

				prefix = packet["conf"]["prefix"] if "prefix" in packet["conf"] else config["prefix"]
				welcome_channel = packet["conf"]["welcome_channel"] if "welcome_channel" in packet["conf"] else config["welcome_channel"]
				welcome_message = packet["conf"]["welcome_message"] if "welcome_message" in packet["conf"] else config["welcome_message"]
				goodbye_channel = packet["conf"]["goodbye_channel"] if "goodbye_channel" in packet["conf"] else config["goodbye_channel"]
				goodbye_message = packet["conf"]["goodbye_message"] if "goodbye_message" in packet["conf"] else config["goodbye_message"]

				await self.client.db.query(
					query, packet["guild_id"], prefix,
					welcome_channel, welcome_message,
					goodbye_channel, goodbye_message,
					bitnumber,
					welcome_message, welcome_message,
					goodbye_channel, goodbye_message,
					bitnumber, fetch=None
				)
				self.client.cache.remove("get_guild_config", (self.client, int(packet["guild_id"])))

		elif packet["type"] == "guild_list":
			new_list = []
			user_id = int(packet["user_id"])
			no_channel = discord.Object(0)
			no_channel.guild = discord.Object(0)

			for guild_id in packet["list"]:
				guild = self.client.get_guild(int(guild_id))

				if guild is not None:
					member = await guild.fetch_member(user_id)

					if member is not None:
						if await self.client.has_permission(member, no_channel, "edit_guild_config"):
							new_list.append(guild_id)

			return new_list

		else:
			raise KeyError()

		return {}

	async def handle_client(self, reader, writer):
		peername = writer.get_extra_info("peername")
		print("New connection!", peername)
		if peername[0] not in self.config["remote_web_socket"]:
			print(peername, "closed 1")
			writer.close() # The IP is not whitelisted!
			return

		while True:
			await asyncio.sleep(.1)
			try:
				packet = await self.parse_packet(await self.recv(reader))

				if packet is not None:
					if not "result" in packet:
						packet["result"] = "success"

					await self.send(writer, packet)

				else:
					await self.send(writer, {"result": "success"})
			except KeyError:
				try:
					await self.send(writer, {"result": "error"})
				except:
					print(peername, "closed 2")
					return
			except ValueError:
				try:
					await self.send(writer, {"result": "error"})
				except:
					print(peername, "closed 3")
					return
			except:
				print(peername, "closed 4")
				return

	async def main(self):
		await asyncio.start_server(self.handle_client, *self.config["web_socket"], loop=self.loop)