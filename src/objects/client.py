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
			"welcome_channel": "",
			"welcome_message": "",
			"goodbye_channel": "",
			"goodbye_message": "",
			"cogs": config["cogs"]
		}
		self.default_permissions = {
			"access_del_cmd": {
				"granted": {
					"big_roles": [],
					"channels": [],
					"roles": []
				},
				"not_granted": {
					"channels": [],
					"roles": []
				},
				"default": False
			},
			"access_sancinfo_cmd": {
				"granted": {
					"big_roles": [],
					"channels": [],
					"roles": []
				},
				"not_granted": {
					"channels": [],
					"roles": []
				},
				"default": False
			},
			"access_remsanc_cmd": {
				"granted": {
					"big_roles": [],
					"channels": [],
					"roles": []
				},
				"not_granted": {
					"channels": [],
					"roles": []
				},
				"default": False
			},
			"access_mute_cmd": {
				"granted": {
					"big_roles": [],
					"channels": [],
					"roles": []
				},
				"not_granted": {
					"channels": [],
					"roles": []
				},
				"default": False
			},
			"access_kick_cmd": {
				"granted": {
					"big_roles": [],
					"channels": [],
					"roles": []
				},
				"not_granted": {
					"channels": [],
					"roles": []
				},
				"default": False
			},
			"access_ban_cmd": {
				"granted": {
					"big_roles": [],
					"channels": [],
					"roles": []
				},
				"not_granted": {
					"channels": [],
					"roles": []
				},
				"default": False
			},
			"access_translate_cmd": {
				"granted": {
					"big_roles": [],
					"channels": [],
					"roles": []
				},
				"not_granted": {
					"channels": [],
					"roles": []
				},
				"default": True
			},
			"edit_guild_config": {
				"granted": {
					"big_roles": [],
					"channels": [],
					"roles": []
				},
				"not_granted": {
					"channels": [],
					"roles": []
				},
				"default": False
			},
			"access_top_cmd": {
				"granted": {
					"big_roles": [],
					"channels": [],
					"roles": []
				},
				"not_granted": {
					"channels": [],
					"roles": []
				},
				"default": True
			},
			"access_level_cmd": {
				"granted": {
					"big_roles": [],
					"channels": [],
					"roles": []
				},
				"not_granted": {
					"channels": [],
					"roles": []
				},
				"default": True
			},
			"access_remind_cmd": {
				"granted": {
					"big_roles": [],
					"channels": [],
					"roles": []
				},
				"not_granted": {
					"channels": [],
					"roles": []
				},
				"default": True
			},
			"access_giveaway_cmd": {
				"granted": {
					"big_roles": [],
					"channels": [],
					"roles": []
				},
				"not_granted": {
					"channels": [],
					"roles": []
				},
				"default": False
			},
			"access_meme_cmd": {
				"granted": {
					"big_roles": [],
					"channels": [],
					"roles": []
				},
				"not_granted": {
					"channels": [],
					"roles": []
				},
				"default": True
			},
			"access_quote_cmd": {
				"granted": {
					"big_roles": [],
					"channels": [],
					"roles": []
				},
				"not_granted": {
					"channels": [],
					"roles": []
				},
				"default": True
			},
			"access_color_cmd": {
				"granted": {
					"big_roles": [],
					"channels": [],
					"roles": []
				},
				"not_granted": {
					"channels": [],
					"roles": []
				},
				"default": True
			},
			"access_exec_cmd": {
				"granted": {
					"big_roles": [],
					"channels": [],
					"roles": []
				},
				"not_granted": {
					"channels": [],
					"roles": []
				},
				"default": False
			},
			"access_urban_cmd": {
				"granted": {
					"big_roles": [],
					"channels": [],
					"roles": []
				},
				"not_granted": {
					"channels": [],
					"roles": []
				},
				"default": True
			},
			"access_dict_cmd": {
				"granted": {
					"big_roles": [],
					"channels": [],
					"roles": []
				},
				"not_granted": {
					"channels": [],
					"roles": []
				},
				"default": True
			},
			"access_anime_cmd": {
				"granted": {
					"big_roles": [],
					"channels": [],
					"roles": []
				},
				"not_granted": {
					"channels": [],
					"roles": []
				},
				"default": True
			},
			"access_country_cmd": {
				"granted": {
					"big_roles": [],
					"channels": [],
					"roles": []
				},
				"not_granted": {
					"channels": [],
					"roles": []
				},
				"default": True
			},
			"access_list_cmd": {
				"granted": {
					"big_roles": [],
					"channels": [],
					"roles": []
				},
				"not_granted": {
					"channels": [],
					"roles": []
				},
				"default": True
			},
			"access_searchin_cmd": {
				"granted": {
					"big_roles": [],
					"channels": [],
					"roles": []
				},
				"not_granted": {
					"channels": [],
					"roles": []
				},
				"default": True
			},
			"access_discrim_cmd": {
				"granted": {
					"big_roles": [],
					"channels": [],
					"roles": []
				},
				"not_granted": {
					"channels": [],
					"roles": []
				},
				"default": True
			}
		}
		self.running_later = []
		cache.maxsize = config["max_cache"]

		super().__init__(command_prefix=self.check_prefix, loop=loop)
		self.db = Database(*config["database"], config["db_pool_max_conn"], loop=self.loop)

		for cog in config["cogs"]:
			self.load_extension(cog)
		self.load_extension("cogs.testcog") # allow the bot to load this cog so we can easily debug the bot
		asyncio.ensure_future(self.bot_loop())

	def _has_permissions(self, config, member, channel, permission):
		permissions = config["permissions"]
		if not permission in permissions:
			return False

		if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
			return True

		has_role = False
		for role in member.roles:
			if role.id in permissions["granted"]["big_roles"]:
				return True

			if not has_role:
				if role.id in permissions["granted"]["roles"]:
					has_role = True

				elif role.id in permissions["not_granted"]["roles"]:
					return False

		if not (has_role and channel.id in permissions["granted"]["channels"]):
			return (channel.id not in permissions["not_granted"]["channels"]) and permissions["default"]

	async def has_permissions(self, member, channel, permission):
		return self._has_permissions(await self.get_guild_config(member.guild.id), member, channel, permission)

	def run_later(self, coro, when, specific=False):
		self.running_later.append([coro, when if specific else time.time() + when])

	async def bot_loop(self):
		while not self.is_closed():
			await asyncio.sleep(.1)

			current = time.time()
			remove_later = []

			for index, (coro, when) in enumerate(self.running_later.copy()):
				await asyncio.sleep(.1)
				if when <= current:
					asyncio.ensure_future(coro)
					remove_later.append(index)

			for index in reversed(remove_later):
				del self.running_later[index]

	async def _get_guild_config(self, guild_id):
		result = await self.db.query("SELECT * FROM `guild_configurations` WHERE `guild_id`=%s", str(guild_id), fetch="one")

		if result is not None:
			config = {}
			config["prefix"] = result["prefix"]
			config["welcome_channel"] = result["welcome_channel"]
			config["welcome_message"] = result["welcome_message"]
			config["goodbye_channel"] = result["goodbye_channel"]
			config["goodbye_message"] = result["goodbye_message"]
			config["cogs"] = []
			for cog, order in self.config["cogs_order"].items():
				if (result["cogs"] & (1 << order)) and (cog in self.config["cogs"]):
					config["cogs"].append(cog)

			if (guild_id == self.config["testserver"]) and ("cogs.testcog" not in config["cogs"]):
				config["cogs"].append("cogs.testcog")
			print(config)

			return config

		if guild_id == self.config["testserver"]:
			config = self.default_config
			config["cogs"].append("cogs.testcog")
			return config
		return self.default_config

	async def _get_guild_permissions(self, guild_id):
		result = await self.db.query("SELECT * FROM `guild_permissions` WHERE `guild_id`=%s", str(guild_id), fetch="all")

		if result is not None:
			permissions = copy.deepcopy(self.default_permissions)
			for row in result:
				permissions[row["name"]] = {
					"granted": {
						"big_roles": list(map(int, row["grant_big_roles"].split(","))) if row["grant_big_roles"] != "" else [],
						"channels": list(map(int, row["grant_channels"].split(","))) if row["grant_channels"] != "" else [],
						"roles": list(map(int, row["grant_roles"].split(","))) if row["grant_roles"] != "" else []
					},
					"not_granted": {
						"channels": list(map(int, row["dont_grant_channels"].split(","))) if row["dont_grant_channels"] != "" else [],
						"roles": list(map(int, row["dont_grant_roles"].split(","))) if row["dont_grant_roles"] != "" else []
					},
					"default": row["default_grant"] == 1
				}

			return permissions

		return self.default_permissions

	@cache.cache
	async def get_guild_config(self, guild_id):
		config = await self._get_guild_config(guild_id)
		config["permissions"] = await self._get_guild_permissions(guild_id)
		return config

	async def check_prefix(self, bot, msg): # self and bot are == since this is a subclass
		config = await self.get_guild_config(msg.guild.id)
		return config["prefix"]

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