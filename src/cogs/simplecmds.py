import objects.utils as utils
import discord
import aiohttp
import json
import datetime
import urllib.parse
from discord.ext import commands

utils.set_cog_name("cogs.simplecmds")

class SimpleCmds(commands.Cog, name="Simple Commands"):
	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	@utils.command_check()
	@utils.permission("access_translate_cmd")
	@commands.bot_has_permissions(send_messages=True)
	async def translate(self, ctx, settings: str, *, text: str):
		settings = settings.lower()

		if len(settings) == 2:
			source = "auto"
			target = settings

		elif len(settings) == 5 and "-" in settings:
			source, target = settings.split("-")[:2]

		else:
			config = await self.bot.get_guild_config(ctx.guild.id)
			await ctx.send(f"Invalid syntax. Correct one: `{config['prefix']}translate es Hello. This is a testing phrase` or `{config['prefix']}translate en-es Hello. This is a testing phrase`")
			return

		querystring = urllib.parse.urlencode({"client": "gtx", "sl": source, "tl": target, "dt": "t", "q": text})
		async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0"}) as session:
			async with session.get(f"https://translate.googleapis.com/translate_a/single?{querystring}") as response:
				result = json.loads(await response.text())
		new_source = result[2]
		result_text = "".join(map(lambda item: item[0], result[0]))

		await ctx.send(embed=discord.Embed(
			title=":nerd: Quick translation",
			colour=0x7dc5b6,
			description=f"From language: **{new_source.upper()}**```\n{text}```To language: **{target.upper()}**```\n{result_text}```",
			timestamp=datetime.datetime.utcnow()
		))

def setup(bot):
	bot.add_cog(SimpleCmds(bot))