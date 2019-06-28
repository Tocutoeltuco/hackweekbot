import objects.utils as utils
import discord
from discord.ext import commands

utils.set_cog_name("cogs.testcog")

class TestCog(commands.Cog, name="Testing Cog"):
	def __init__(self, bot):
		self.bot = bot

	@commands.Cog.listener()
	async def on_ready(self):
		print("The bot is ready!")

def setup(bot):
	bot.add_cog(TestCog(bot))