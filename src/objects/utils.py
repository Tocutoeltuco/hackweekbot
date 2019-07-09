import re
from discord.ext import commands
import discord

cog_name = None

def set_cog_name(name):
	global cog_name
	cog_name = name

async def cog_check(bot, guild):
	if cog_name is None:
		raise EnvironmentError("objects.utils.cog_name was never set. Set it with objects.utils.set_cog_name")

	if guild is None:
		return False

	guild_conf = await bot.get_guild_config(guild.id)
	if cog_name in guild_conf["cogs"]:
		return True
	return False

def command_check():
	"""A checker to tell whether the command can execute in this guild or not."""
	async def predicate(ctx):
		result = await cog_check(ctx.bot, ctx.guild)
		print("command check", result)
		return result

	return commands.check(predicate)

def permission(permission):
	"""A checker that tells if the given permission is granted in the given context."""
	async def predicate(ctx):
		result = await ctx.bot.has_permissions(ctx.author, ctx.channel, permission)
		print("permission check", result)
		return result

	return commands.check(predicate)

def time(arg):
	arg = arg.lower()

	seconds = re.search(r"(\d+)s", arg)
	minutes = re.search(r"(\d+)m", arg)
	hours = re.search(r"(\d+)h", arg)
	days = re.search(r"(\d+)d", arg)

	time_quantity = 0
	if seconds is not None:
		time_quantity += int(seconds[1])
	if minutes is not None:
		time_quantity += int(minutes[1]) * 60
	if hours is not None:
		time_quantity += int(hours[1]) * 3600
	if days is not None:
		time_quantity += int(days[1]) * 86400

	return time_quantity

def integer(arg):
	try:
		return int(arg)
	except ValueError:
		pass

	try:
		return int(round(float(arg)))
	except ValueError:
		raise commands.BadArgument("Argument is not a number.")

def double(arg):
	try:
		return float(arg)
	except ValueError:
		raise commands.BadArgument("")

class PaginationEmbed(discord.Embed):
	def __init__(self, **kwargs):
		self._fields = []
		self.page = 0
		self.last_page = 0
		self.pages = []
		super().__init__(**kwargs)

	@property
	def description(self):
		return self._description

	@description.setter
	def description(self, value):
		if value==discord.embeds.EmptyEmbed:
			value = ''
		self._description = value
		self.get_pages()

	def get_pages(self):
		_desc = self.description.split('\n')

		self.pages = pages = []
		description = []
		index = 0
		while index<len(_desc):
			while len(description)<=20 and len('\n'.join(description))<2048 and index<len(_desc):
				description.append(_desc[index])
				index += 1
			pages.append('\n'.join(description))
			description.clear()

		self.last_page = len(pages)
		self.page = min(self.page, self.last_page)

	def to_dict(self):
		_description = self.description

		self._description = self.pages[self.page]

		if self.last_page>1:
			self.set_footer(text=f'Page {self.page + 1}/{self.last_page}')

		result = super().to_dict()
		self._description = _description
		return result