import objects.utils as utils
import discord
from discord.ext import commands

import pydoc

utils.set_cog_name("cogs.docs")

class DocsCog(commands.Cog, name="Docs Cog"):
	def __init__(self):
		pass

	@commands.command()
	@utils.command_check()
	@commands.bot_has_permissions(send_messages=True)
	async def pydoc(self, ctx, keyword, page='0'):
		"""{{Shows the python documentation}}
		[[]]
		(([keyword] <page>))
		++.pydocs os.system++
		"""
		async def send(embed):
			ctx.bot.set_answer(
				ctx.message.id,
				await ctx.send(embed=embed)
			)

		if keyword.strip()=='':
			return await send(discord.Embed(
				title=f'Python documentation',
				description='```Error: Empty keyword```',
				color=0xDC143C
			))

		try:
			obj, name = pydoc.resolve(keyword)
			doc = pydoc.render_doc(obj, renderer=pydoc.plaintext)
		except Exception as e:
			return await send(discord.Embed(
				title=f'Python documentation for **`{keyword}`**',
				description=f'```{e.__class__.__name__}: {e}```',
				color=0xDC143C
			))

		embed = utils.PaginationEmbed()
		embed.title = f'Python documentation for **`{name or keyword}`**'
		embed.description = '\n'.join(doc.split('\n')[2:])
		embed.color = 0xDC143C
		embed.page = int(page if page.isdigit() else 0)
		page = min(embed.last_page, embed.page)
		embed.pages[page] = f"```{embed.pages[page]}```"

		await send(embed)


def setup(bot):
	bot.add_cog(DocsCog())