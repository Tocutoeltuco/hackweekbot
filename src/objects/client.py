import sys
import copy
import time
import asyncio
import traceback
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
			"prefix": ".",
			"cogs": config["cogs"]
		}
		self.running_later = []
		cache.maxsize = config["max_cache"]

		super().__init__(command_prefix=self.check_prefix, loop=loop)
		self.db = Database(*config["database"], config["db_pool_max_conn"], loop=self.loop)

		for cog in config["cogs"]:
			self.load_extension(cog)
		self.load_extension("cogs.testcog") # allow the bot to load this cog so we can easily debug the bot
		asyncio.ensure_future(self.bot_loop())

	def run_later(self, coro, when, specific=False):
		self.running_later.append([coro, when if specific else time.time() + when])

	async def bot_loop(self):
		while not self.is_closed():
			await asyncio.sleep(.1)

			current = time.time()
			remove_later = []

			for index, (coro, when) in enumerate(self.running_later):
				await asyncio.sleep(.1)
				if when <= current:
					asyncio.ensure_future(coro)
					remove_later.append(index)

			for index in remove_later:
				del self.running_later[index]

	@cache.cache
	async def get_guild_config(self, guild_id):
		result = await self.db.query("SELECT * FROM `guild_configurations` WHERE `guild_id`=%s", guild_id, fetch="one")

		if result is not None:
			config = {}
			config["prefix"] = result["prefix"]
			config["cogs"] = []
			for cog, order in self.config["cogs_order"].items():
				if (result["cogs"] & (1 << order)) and (cog in self.config["cogs"]):
					config["cogs"].append(cog)

			if (guild_id == self.config["testserver"]) and ("cogs.testcog" not in config["cogs"]):
				config["cogs"].append("cogs.testcog")

			return config

		if guild_id == self.config["testserver"]:
			config = copy.deepcopy(self.default_config)
			config["cogs"].append("cogs.testcog")
			return config
		return copy.deepcopy(self.default_config)

	async def command_prefix(self, bot, msg): # self and bot are == since this is a subclass
		config = await self.get_guild_config(msg.guild.id)
		return config["prefix"]

	async def check_prefix(self, bot, message):
		return (await self.get_guild_config(message.guild))["prefix"]

	async def on_command_error(self, ctx, exception):
		if isinstance(exception, (
			commands.CheckFailure, commands.CommandNotFound, commands.TooManyArguments,
			commands.DisabledCommand, commands.BadArgument, commands.ExpectedClosingQuoteError,
			commands.InvalidEndOfQuotedStringError, commands.UnexpectedQuoteError,
			commands.MissingRequiredArgument, commands.NoPrivateMessage,
			commands.DisabledCommand, commands.CommandOnCooldown, commands.UserInputError,
			commands.NotOwner, commands.MissingPermissions
		)):
			return

		print("Ignoring exception in command {}:".format(ctx.command), file=sys.stderr)
		traceback.print_exception(type(exception), exception, exception.__traceback__, file=sys.stderr)