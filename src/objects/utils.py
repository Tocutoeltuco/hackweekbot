from discord.ext import commands
import discord

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
			self.set_footer(text=f'Page {self.page}/{self.last_page}')

		result = super().to_dict()
		self._description = _description
		return result