import objects.utils as utils
from discord.ext import commands

import aiohttp
import discord

utils.set_cog_name("cogs.api")

class ApiCog(commands.Cog, name="Api Cog"):
	"""Cog where all call to APIs are made."""

	def __init__(self, session):
		self.session = session

	@commands.command()
	@utils.command_check()
	@commands.bot_has_permissions(send_messages=True)
	async def urban(self, ctx, *args):
		"""{{Shows the definition of an expression.}}
		[[]]
		(([word(s)]))
		++.urban bruh++
		"""
		url = "http://urbanscraper.herokuapp.com"
		title = "Urban Search: `{}`"
		description = '\n'.join([
			'**__Definition__:**',
			'```{0[definition]}```',
			'**__Example__:**',
			'```{0[example]}```'
		])
		try:
			async with self.session.get(f'{url}/define/{" ".join(args)}') as resp:
				resp.raise_for_status()
				result = await resp.json()
		except aiohttp.client_exceptions.ClientResponseError:
			embed = discord.Embed()
			embed.title = title.format(' '.join(args))
			embed.description = "```Not Found```"
			embed.color = 0xDC143C
			embed.set_footer(text=url)
			return await ctx.send(embed=embed)

		embed = discord.Embed()
		embed.title = title.format(result.get('term'))
		embed.description = description.format(result)
		embed.color = 0xE86222
		embed.set_footer(text=url)

		await ctx.send(embed=embed)

	@commands.command()
	@utils.command_check()
	@commands.bot_has_permissions(send_messages=True)
	async def dict(self, ctx, *args):
		"""{{Shows the definition of a word.}}
		[[]]
		(([word]))
		++.dict postpone++
		"""
		params = {
			'define': ' '.join(args)
		}

		try:
			async with self.session.get('https://googledictionaryapi.eu-gb.mybluemix.net', params=params) as resp:
				resp.raise_for_status()
				result = (await resp.json())[0]
		except aiohttp.client_exceptions.ClientResponseError:
			return await ctx.send(embed=discord.Embed(title=f"Dictionary Search: `{' '.join(args)}`", description="```Not Found```", color=0xDC143C))

		meaning = list(result.get('meaning').values())[0][0]
		description = '\n'.join([
			f"**__Definition__:**\n```{meaning.get('definition')}```",
			f"**__Example__:**\n```{meaning.get('example')}```"
		])

		embed = discord.Embed()
		embed.title = f"Dictionary Search: `{result.get('word')}`"
		embed.description = description
		embed.add_field(name='Type 📖', value=f"{list(result.get('meaning').keys())[0]}", inline=True)
		embed.add_field(name='Phonetic 👂', value=f"`{result.get('phonetic')}`", inline=True)
		embed.color = 0xE86222
		embed.set_footer(text="https://googledictionaryapi.eu-gb.mybluemix.net/")

		await ctx.send(embed=embed)

	@commands.command()
	@utils.command_check()
	@commands.bot_has_permissions(send_messages=True)
	async def anime(self, ctx, *args):
		"""{{Shows informations about an anime.}}
		[[]]
		(([anime's name]))
		++.anime dororo++
		"""
		params = {
			'filter[text]': ' '.join(args)
		}

		try:
			async with self.session.get('https://kitsu.io/api/edge/anime', params=params) as resp:
				resp.raise_for_status()
				result = await resp.json()
				for i in range(len(result['data'])):
					if result['data'][i]['type']=='anime':
						anime = result['data'][i]['attributes']
						break
				else:
					raise aiohttp.client_exceptions.ClientResponseError()

		except aiohttp.client_exceptions.ClientResponseError:
			embed = discord.Embed()
			embed.title = f"Anime Search: `{' '.join(args)}`"
			embed.description = "```Not Found```"
			embed.color = 0xDC143C
			embed.set_footer(text="https://kitsu.io")
			return await ctx.send(embed=embed)

		synopsis = anime['synopsis']
		if len(synopsis)>=300:
			synopsis = f'{synopsis[:297]}[...](https://kitsu.io/anime/{anime.get("slug")})'

		embed = discord.Embed()
		embed.title = f"Anime Search: `{params['filter[text]']}`"
		embed.description = f"**{anime.get('canonicalTitle')}**\n*{synopsis}*"
		embed.set_image(url=anime.get('posterImage')['original'])
		embed.add_field(name='Rating', value=anime.get('averageRating'), inline=True)
		embed.add_field(name='Status', value=anime.get('status'), inline=True)
		embed.add_field(name='Number of episodes', value=anime.get('episodeCount'), inline=True)
		embed.add_field(name='Trailer', value=f"https://youtube.com/watch?v={anime.get('youtubeVideoId')}", inline=True)
		# embed.set_author(name=)
		embed.color = 0xE86222
		embed.set_footer(text="https://kitsu.io")

		await ctx.send(embed=embed)

	@commands.command()
	@utils.command_check()
	@commands.bot_has_permissions(send_messages=True)
	async def country(self, ctx, *args):
		"""{{Shows informations about a country..}}
		[[]]
		(([country's name]))
		++.country belgium++
		"""
		try:
			async with self.session.get(f'https://restcountries.eu/rest/v2/name/{" ".join(args)}') as resp:
				resp.raise_for_status()
				result = await resp.json()
				if (isinstance(result, dict) and result.get('status', 0)!=0) or len(result)==0:
					raise Exception('Not Found')
				else:
					data = result[0]
		except Exception:
			embed = discord.Embed()
			embed.title = ' '.join(args).capitalize()
			embed.description = "```Not Found```"
			embed.color = 0xDC143C
			embed.set_footer(text="https://restcountries.eu/")
			return await ctx.send(embed=embed)

		currencies = [f"{cur.get('name')} {cur.get('symbol')}" for cur in data.get('currencies')]
		languages = [lang.get('name') for lang in data.get('languages')]
		region = f"[{data.get('subregion')}](https://www.google.com/maps/place/{data.get('name').replace(' ', '%20')})"

		embed = discord.Embed()
		embed.title = f"Country `{data.get('name')}`"
		embed.set_thumbnail(url=f'http://flags.fmcdn.net/data/flags/w580/{data.get("alpha2Code").lower()}.png')
		embed.add_field(name='Capital 🏛', value=data.get('capital'), inline=True)
		embed.add_field(name='Region 📍', value=region, inline=True)
		embed.add_field(name='Area 📏', value=f"{round(data.get('area'))} km²", inline=True)
		embed.add_field(name='Population 👥', value=f"{data.get('population'):,}", inline=True)
		embed.add_field(name='Currency 💰', value=', '.join(currencies), inline=True)
		embed.add_field(name='Languages 🌐', value=', '.join(languages))
		# embed.set_author(name=)
		embed.color = 0xE86222
		embed.set_footer(text="https://restcountries.eu/")

		await ctx.send(embed=embed)


def setup(bot):
	timeout = aiohttp.ClientTimeout(total=3)
	session = aiohttp.ClientSession(timeout=timeout, loop=bot.loop)
	bot.add_cog(ApiCog(session))