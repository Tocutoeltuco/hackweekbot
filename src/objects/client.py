import asyncio
from discord.ext import commands
from .cache import Cache
from .database import Database

cache = Cache()

class Client(commands.Bot):
	def __init__(self, objects, config, loop=None):
		self.cache = cache
		self.objects = objects
		self.config = config
		self.default_config = {
			"prefix": "!",
			"cogs": config["cogs"]
		}
		cache.maxsize = config["max_cache"]

		super().__init__(command_prefix=self.check_prefix, loop=loop)
		self.db = Database(*config["database"], config["db_pool_max_conn"], loop=self.loop)

		for cog in config["cogs"]:
			self.load_extension(cog)

	@cache.cache
	async def get_guild_config(self, guild_id):
		result = await self.db.query("SELECT * FROM `guild_configurations` WHERE `guild_id`=%s", guild_id, fetch="one")

		if result is not None:
			config = {}
			config["prefix"] = result["prefix"]
			config["cogs"] = result["cogs"].split(",")

			return config
		return self.default_config

	async def check_prefix(self, bot, message):
		return (await self.get_guild_config(message.guild))["prefix"]