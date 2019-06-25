from discord.ext import commands

cog_name = None

def set_cog_name(name):
	global cog_name
	cog_name = name

def command_check():
	"""A checker to tell whether the command can execute in this guild or not."""
	async def predicate(ctx):
		if cog_name is None:
			raise EnvironmentError("objects.utils.cog_name was never set. Set it with objects.utils.set_cog_name")

		if ctx.guild is None:
			return False

		guild_conf = await ctx.bot.get_guild_config(ctx.guild.id)
		if cog_name in guild_conf["cogs"]:
			return True
		return False

	return commands.check(predicate)