from discord.ext import commands

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
		return await cog_check(ctx.bot, ctx.guild)

	return commands.check(predicate)

def permission(permission):
	"""A checker that tells if the given permission is granted in the given context."""
	async def predicate(ctx):
		return await ctx.bot.has_permissions(ctx.author, ctx.channel, permission)

	return commands.check(predicate)

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