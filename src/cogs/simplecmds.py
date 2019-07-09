# coding: utf-8

import objects.utils as utils
import discord
import asyncio
import aiohttp
import random
import json
import time
import io
import re
import datetime
import urllib.parse
from discord.ext import commands

class SimpleCmds(commands.Cog, name="Simple Commands"):
	def __init__(self, bot, session):
		self.bot = bot
		self.session = session
		self.bot.run_later(self.check_running_later(), 0, specific=True)

	async def check_running_later(self):
		rows = await self.bot.db.query("SELECT `discord_id`, `run_at`, `type` FROM `custom_run_later` WHERE `run_at`<%s", int(time.time() + 120), fetch="all")

		if rows is not None:
			for row in rows:
				if row["type"] == "giveaway":
					coro = self.sort_giveaway(row["discord_id"])

				elif row["type"] == "reminder":
					coro = self.remind_now(row["discord_id"])

				self.bot.run_later(coro, row["run_at"], specific=True)

		self.bot.run_later(self.check_running_later(), 120)

	async def sort_giveaway(self, id):
		giveaway = await self.bot.db.query("SELECT * FROM `custom_run_later` WHERE `discord_id`=%s", id, fetch="one")

		if giveaway is not None:
			guild = self.bot.get_guild(int(id))

			if guild is not None:
				channel_id, msg_id = giveaway["info"].split(";")
				channel = guild.get_channel(int(channel_id))

				try:
					message = await channel.fetch_message(int(msg_id))
				except:
					message = None

				if message is not None:
					winner = None
					for reaction in message.reactions:
						if reaction.emoji == u"🙋":
							users = []

							async for user in reaction.users():
								if isinstance(user, discord.Member) and user.id != self.bot.user.id:
									users.append(user)

							if len(users) > 0:
								winner = random.choice(users)
							break

					try:
						await channel.send(
							content=f"Congratulations <@{winner.id}>! You've won this giveaway! :tada:" if winner is not None else "",
							embed=discord.Embed(
								title="Finished giveaway!",
								description=f"""[This giveaway](https://discordapp.com/channels/{guild.id}/{channel.id}/{message.id}) has ended!
	{"Sadly, there is no winner :sob:" if winner is None else ""}""",
								colour=0xffff99
							)
						)
					except:
						pass

			await self.bot.db.query("DELETE FROM `custom_run_later` WHERE `discord_id`=%s", id, fetch=None)

	async def remind_now(self, id):
		reminder = await self.bot.db.query("SELECT * FROM `custom_run_later` WHERE `discord_id`=%s", id, fetch="one")

		if reminder is not None:
			user = self.bot.get_user(int(id))

			if user is not None:
				guild_id, channel_id, message = reminder["info"].split(";", 2)
				guild = self.bot.get_guild(int(guild_id))

				if guild is not None:
					channel = self.bot.get_channel(int(channel_id))

					if channel is not None:
						try:
							member = await guild.fetch_member(user.id)
						except:
							member = None

						if member is not None:
							try:
								await channel.send(content=f"<@{member.id}>", embed=discord.Embed(
									title="Reminder!",
									description=f"Some time ago you told me to remind something right now! This was the message:```\n{message}```",
									colour=0xffff99
								))
							except:
								pass

			await self.bot.db.query("DELETE FROM `custom_run_later` WHERE `discord_id`=%s", id, fetch=None)

	@commands.command()
	@utils.command_check("cogs.simplecmds")
	@utils.permission("access_giveaway_cmd")
	@commands.bot_has_permissions(send_messages=True)
	async def giveaway(self, ctx, when: utils.time, *, message: str):
		"""{{Makes a giveaway in this channel}}
		[[]]
		(([when] [message]))
		++1d1h1m1s This is a testing giveaway!++"""
		if await self.bot.db.query("SELECT * FROM `custom_run_later` WHERE `discord_id`=%s", str(ctx.guild.id), fetch="one") is not None:
			config = await self.bot.get_guild_config(ctx.guild.id)
			await ctx.send(f"<@{ctx.author.id}> You have an already running giveaway in this server! Stop it by writing **{config['prefix']}stopgiveaway** first.")
			return

		if when < 180:
			await ctx.send(f"<@{ctx.author.id}> You must set a time quantity that is greater than 3 minutes!")
			return

		embed = discord.Embed(
			title="Giveaway!",
			description=f"""Giveaway started by <@{ctx.author.id}> (**{ctx.author.name}**)```
{message}```React with {u'🙋'} and stay in the server to join the giveaway!""",
			colour=0xffff99,
			timestamp=datetime.datetime.utcfromtimestamp(time.time() + when)
		)
		embed.set_footer(text="Sorting at")
		message = await ctx.send(embed=embed)
		try:
			await message.add_reaction(u"🙋")
		except:
			pass
		try:
			await ctx.message.delete()
		except:
			pass
		await self.bot.db.query(
			"INSERT INTO `custom_run_later` (`discord_id`, `run_at`, `type`, `info`) VALUES (%s, %s, %s, %s)",
			str(ctx.guild.id), time.time() + when, "giveaway", f"{ctx.channel.id};{message.id}", fetch=None
		)

	@commands.command()
	@utils.command_check("cogs.simplecmds")
	@utils.permission("access_giveaway_cmd")
	@commands.bot_has_permissions(send_messages=True)
	async def stopgiveaway(self, ctx):
		"""{{Stops the server's giveaway, if any.}}
		[[]]
		(())
		++++
		"""
		result = await self.bot.db.query("SELECT `info` FROM `custom_run_later` WHERE `discord_id`=%s", str(ctx.guild.id), fetch="one")

		if result is not None:
			channel_id, message_id = result["info"].split(";")
			channel = ctx.guild.get_channel(int(channel_id))

			if channel is not None:
				message = await channel.fetch_message(int(message_id))

				if message is not None:
					await message.delete()

			await self.bot.db.query("DELETE FROM `custom_run_later` WHERE `discord_id`=%s", str(ctx.guild.id), fetch=None)
			message = await ctx.send(f"<@{ctx.author.id}> You can now start a new giveaway!")
			self.bot.set_answer(ctx.message.id, message)

		else:
			message = await ctx.send(f"<@{ctx.author.id}> There is no running giveaway right now.")
			self.bot.set_answer(ctx.message.id, message)

	@commands.command()
	@utils.command_check("cogs.simplecmds")
	@utils.permission("access_remind_cmd")
	@commands.bot_has_permissions(send_messages=True)
	async def remind(self, ctx, when: utils.time, *, message: str):
		"""{{Adds a reminder. Bot will remind you!}}
		[[]]
		(([when] [message]))
		++1d1h1m1s take a shower u smell++
		"""
		if await self.bot.db.query("SELECT * FROM `custom_run_later` WHERE `discord_id`=%s", str(ctx.author.id), fetch="one") is not None:
			config = await self.bot.get_guild_config(ctx.guild.id)
			message = await ctx.send(f"<@{ctx.author.id}> You have an already running reminder! Stop it by writing **{config['prefix']}stopreminder** first.")
			self.bot.set_answer(ctx.message.id, message)
			return

		if when < 180:
			message = await ctx.send(f"<@{ctx.author.id}> You must set a time quantity that is greater than 3 minutes!")
			self.bot.set_answer(ctx.message.id, message)
			return

		await self.bot.db.query(
			"INSERT INTO `custom_run_later` (`discord_id`, `run_at`, `type`, `info`) VALUES (%s, %s, %s, %s)",
			str(ctx.author.id), time.time() + when, "reminder", f"{ctx.guild.id};{ctx.channel.id};{message}", fetch=None
		)
		message = await ctx.send(f"<@{ctx.author.id}> Alright. I will remind you!")
		self.bot.set_answer(ctx.message.id, message)

	@commands.command()
	@utils.command_check("cogs.simplecmds")
	@utils.permission("access_remind_cmd")
	@commands.bot_has_permissions(send_messages=True)
	async def stopreminder(self, ctx):
		"""{{Cancels your ongoing reminder.}}
		[[]]
		(())
		++++
		"""
		await self.bot.db.query("DELETE FROM `custom_run_later` WHERE `discord_id`=%s", str(ctx.author.id), fetch=None)
		message = await ctx.send(f"<@{ctx.author.id}> You can now add a new reminder!")
		self.bot.set_answer(ctx.message.id, message)

	@commands.command()
	@utils.command_check("cogs.simplecmds")
	@utils.permission("access_help_cmd")
	@commands.bot_has_permissions(send_messages=True)
	async def help(self, ctx, command: str=None):
		"""{{Shows information about the commands}}
		[[]]
		((<command name>))
		++stopreminder++
		"""
		prefix = await self.bot.check_prefix(self.bot, ctx.message)

		if command is None:
			description = f":small_red_triangle_down: Use **`{prefix}help <command name>`** to get more information about a command.\n"

			for name, command in self.bot.all_commands.items():
				try:
					if not await command.can_run(ctx):
						continue
				except:
					continue

				_description = re.search(r"\{\{(.+?)\}\}", command.help)
				if _description is not None:
					_description = _description[1]
				description += f"\n:small_blue_diamond: **`{prefix}{name}`**{f' - {_description}' if _description is not None else ''}"

			embed = utils.PaginationEmbed(
				title="Help command",
				description=description,
				colour=0xffff99
			)
			message = await ctx.send(embed=embed)
			self.bot.set_answer(ctx.message.id, message)

			available_reactions = [u"⏪", u"◀", u"▶", u"⏩"]
			def check(reaction, user):
				return user == ctx.author and reaction.message.id == message.id and str(reaction) in available_reactions

			try:
				for reaction in available_reactions:
					await message.add_reaction(reaction)
			except:
				pass

			while True:
				try:
					reaction, user = await self.bot.wait_for("reaction_add", timeout=120.0, check=check)
				except asyncio.TimeoutError:
					try:
						await message.clear_reactions()
					except:
						pass
					return
				else:
					reaction = str(reaction)

					if reaction == available_reactions[0]:
						embed.page = 0

					elif reaction == available_reactions[1]:
						if embed.page > 0:
							embed.page -= 1

					elif reaction == available_reactions[2]:
						if embed.page < (embed.last_page - 1):
							embed.page += 1

					else:
						embed.page = embed.last_page - 1

					await message.edit(embed=embed)
					try:
						await message.remove_reaction(reaction, user)
					except:
						pass

		else:
			embed = discord.Embed(title="Help command")
			command = command.lower()

			if command in self.bot.all_commands:
				cmd = self.bot.all_commands[command]
				show = False
				try:
					if await cmd.can_run(ctx):
						show = True
				except:
					embed.colour = 0xff5555
					embed.description = f"You don't have access to the command **`{prefix}{command}`**!"

				if show:
					description = re.search(r"\{\{(.+?)\}\}", cmd.help)
					info = re.search(r"\[\[(.+?)\]\]", cmd.help)
					arguments = re.search(r"\(\((.+?)\)\)", cmd.help)
					example = re.search(r"\+\+(.+?)\+\+", cmd.help)

					if description is not None:
						description = description[1]
					else:
						description = ""
					if info is not None:
						info = info[1]
						if info.strip(" ") == "":
							info = None
					if arguments is not None:
						arguments = arguments[1]
						if arguments.strip(" ") == "":
							arguments = None
					if example is not None:
						example = " " + example[1]
						if example.strip(" ") == "":
							example = ""
					else:
						example = ""

					embed.colour = 0xffff99
					embed.description = f""":small_red_triangle_down: Command: **`{prefix}{command}`**
:small_orange_diamond: Description: **`{description}`**
{f":small_orange_diamond: Information: **`{info}`**" if info is not None else ""}

:small_blue_diamond: **`[argument]`** -> required; **`<argument>`** -> optional
:small_blue_diamond: Arguments: **`{arguments or "no arguments"}`**
:small_blue_diamond: Example: **`{prefix}{command}{example}`**"""

			else:
				embed.colour = 0xff5555
				embed.description = f"The command **`{prefix}{command}`** was not found :("

			message = await ctx.send(embed=embed)
			self.bot.set_answer(ctx.message.id, message)

	@commands.command()
	@utils.command_check("cogs.simplecmds")
	@utils.permission("access_quote_cmd")
	@commands.bot_has_permissions(send_messages=True)
	async def quote(self, ctx, info: str):
		"""{{Quotes a message from this or the given channel}}
		[[]]
		(([<channelid->messageid]))
		++592104443151908866-593978517948203008++
		"""
		splitted = info.split("-")[:2]
		if len(splitted) == 2:
			channel, msg = splitted
		else:
			channel, msg = splitted[0], None
		if not channel.isdigit():
			message = await ctx.send(f"Invalid syntax! Correct one: `{config['prefix']}quote <channelid->msgid`")
			self.bot.set_answer(ctx.message.id, message)
			return

		message = None
		if msg is None:
			msg = channel
			channel = ctx.channel
			try:
				message = await ctx.channel.fetch_message(int(msg))
			except:
				pass

		else:
			if not msg.isdigit():
				message = await ctx.send(f"Invalid syntax! Correct one: `{config['prefix']}quote <channelid->msgid`")
				self.bot.set_answer(ctx.message.id, message)
				return

			channel = ctx.guild.get_channel(int(channel))
			if channel is not None:
				try:
					message = await channel.fetch_message(int(msg))
				except:
					pass

		if message is not None:
			if not message.author.bot:
				embed = discord.Embed(
					colour=0xffff99,
					description=message.content,
					timestamp=message.created_at
				)
				embed.add_field(name="Link", value=f"[Click here](https://discordapp.com/channels/{ctx.guild.id}/{channel.id}/{message.id})")
				embed.set_author(name=message.author.name, icon_url=str(message.author.avatar_url))
				embed.set_footer(text=f"In {channel.category.name + '.#' if channel.category is not None else '#'}{channel.name}")

				message = await ctx.send(content=f"_Quote from <@{ctx.author.id}> **{ctx.author.name}**_", embed=embed)
				self.bot.set_answer(ctx.message.id, message)

			else:
				message = await ctx.send(f"Sadly, I can't quote that message. But there is the link: https://discordapp.com/channels/{ctx.guild.id}/{channel.id}/{message.id}")
				self.bot.set_answer(ctx.message.id, message)

		else:
			message = await ctx.send("Message not found.")
			self.bot.set_answer(ctx.message.id, message)

	@commands.command()
	@utils.command_check("cogs.simplecmds")
	@utils.permission("access_color_cmd")
	@commands.bot_has_permissions(send_messages=True)
	async def color(self, ctx, color: str):
		"""{{Shows a color}}
		[[]]
		(([color (hex or dec)]))
		++#ffff99++
		"""
		if color.isdigit():
			color = int(color)

		elif color.startswith("#"):
			try:
				color = int("0x" + color.replace("#", "", 1), 16)
			except:
				message = await ctx.send("Invalid color! Valid ones: `16777113`, `#ffff99`")
				self.bot.set_answer(ctx.message.id, message)
				return

		else:
			message = await ctx.send("Invalid color! Valid ones: `16777113`, `#ffff99`")
			self.bot.set_answer(ctx.message.id, message)
			return

		color &= 0xffffff
		hex_color = "%06x" % color
		embed = discord.Embed(colour=color)
		embed.set_author(name=f"#{hex_color.upper()} <{color}>")
		embed.set_image(url=f"https://www.colorhexa.com/{hex_color}.png")

		message = await ctx.send(embed=embed)
		self.bot.set_answer(ctx.message.id, message)

	@commands.command()
	@utils.command_check("cogs.simplecmds")
	@utils.permission("access_exec_cmd")
	@commands.bot_has_permissions(send_messages=True)
	async def exec(self, ctx, *, args: str):
		"""{{Loads a script using Rextester}}
		[[]]
		(([block quote with the language and code]))
		++\\`\\`\\`python
print("Hello world!")\\`\\`\\`++
		"""
		languages = {
			"c#": 1, "cs": 1,
			"lua": 14,
			"ada": 39,
			"assembly": 15,
			"bash": 38,
			"c++": 7, "cpp": 7, "c++ gcc": 7, "cpp gcc": 7,
			"c++ clang": 27, "cpp clang": 27,
			"c++ vc++": 28, "cpp vc++": 28, "c++ vcpp": 28, "cpp vcpp": 28,
			"c": 6, "c gcc": 6,
			"c clang": 26,
			"c vc": 29,
			"common lisp": 18,
			"d": 30,
			"elixir": 41,
			"erlang": 40,
			"f#": 3,
			"fortran": 45,
			"go": 20,
			"haskell": 11,
			"java": 4,
			"javascript": 17, "js": 17,
			"kotlin": 43,
			"node.js": 23,
			"ocaml": 42,
			"pascal": 9,
			"perl": 13,
			"prolog": 19,
			"python2": 5,
			"python3": 24, "python": 24, "py": 24,
			"r": 31,
			"ruby": 12,
			"scala": 21,
			"scheme": 22,
			"swift": 37,
			"tcl": 32,
			"visual basic": 2,
			"php": 8
		}
		compilerArgs = {
			7: "-Wall -std=c++14 -O2 -o a.out source_file.cpp",
			27: "-Wall -std=c++14 -stdlib=libc++ -O2 -o a.out source_file.cpp",
			28: "source_file.cpp -o a.exe /EHsc /MD /I C:\\boost_1_60_0 /link /LIBPATH:C:\\boost_1_60_0\\stage\\lib",
			6: "-Wall -std=gnu99 -O2 -o a.out source_file.c",
			26: "-Wall -std=gnu99 -O2 -o a.out source_file.c",
			29: "source_file.c -o a.exe",
		}

		scriptData = re.search("```(.+)\n((?:.|\n)+)```", args)
		if scriptData is not None:
			lang = scriptData[1]
			if lang in languages:
				script = scriptData[2]
				data = {
					"LanguageChoiceWrapper": languages[lang],
					"EditorChoiceWrapper": 1,
					"LayoutChoiceWrapper": 1,
					"Program": script,
					"Input": "",
					"Privacy": "",
					"PrivacyUsers": "",
					"Title": "",
					"SavedOutput": "",
					"WholeError": "",
					"WholeWarning": "",
					"StatsToSave": "",
					"CodeGuid": "",
					"IsInEditMode": "False",
					"IsLive": "False"
				}

				if languages[lang] in compilerArgs:
					data["CompilerArgs"] = compilerArgs

				async with self.session.post(
					"https://rextester.com/rundotnet/Run",
					headers={"User-Agent": "Mozilla/5.0", "Content-Type": "application/x-www-form-urlencoded"},
					data=urllib.parse.urlencode(data).encode()
				) as response:
					result = json.loads(await response.text())
				embeds = []

				if type(result["Errors"]) == str:
					embeds.append(discord.Embed(title="Script errors", description=result["Errors"], colour=0x990000))

				if type(result["Warnings"]) == str:
					embeds.append(discord.Embed(title="Script warnings", description=result["Warnings"], colour=0x999900))

				if type(result["Result"]) == str:
					embeds.append(discord.Embed(title="Script result", description=result["Result"], colour=0x0099ff))

				embeds.append(discord.Embed(title="Script stats", description=result["Stats"] + ", language: " + lang, colour=0x0099ff))

				for embed in embeds:
					await ctx.send(embed=embed)
			else:
				message = await ctx.send("Invalid language!")
				self.bot.set_answer(ctx.message.id, message)
		else:
			message = await ctx.send("Invalid command structure!")
			self.bot.set_answer(ctx.message.id, message)

	@commands.command()
	@utils.command_check("cogs.simplecmds")
	@utils.permission("access_meme_cmd")
	@commands.bot_has_permissions(send_messages=True)
	async def meme(self, ctx):
		"""{{Shows a random meme!}}
		[[]]
		(())
		++++
		"""
		try:
			async with self.session.get("https://meme-api.herokuapp.com/gimme") as response:
				result = json.loads(await response.text())
		except:
			await ctx.send("Can not fetch a meme right now. :cry:")
			return

		embed = discord.Embed(
			title=result["title"],
			colour=0xffff99
		)
		embed.set_image(url=result["url"])
		embed.set_footer(text="https://meme-api.herokuapp.com/")
		await ctx.send(embed=embed)

	@commands.command()
	@utils.command_check("cogs.simplecmds")
	@utils.permission("access_translate_cmd")
	@commands.bot_has_permissions(send_messages=True)
	async def translate(self, ctx, settings: str, *, text: str):
		"""{{Translates a sentence into from/to the language you want.}}
		[[]]
		(([<from_language->to_language] [text]))
		++es-en Hola, ¿cómo estás?++
		"""
		settings = settings.lower()

		if len(settings) == 2:
			source = "auto"
			target = settings

		elif len(settings) == 5 and "-" in settings:
			source, target = settings.split("-")[:2]

		else:
			config = await self.bot.get_guild_config(ctx.guild.id)
			message = await ctx.send(f"Invalid syntax. Correct one: `{config['prefix']}translate es Hello. This is a testing phrase` or `{config['prefix']}translate en-es Hello. This is a testing phrase`")
			self.bot.set_answer(ctx.message.id, message)
			return

		querystring = urllib.parse.urlencode({"client": "gtx", "sl": source, "tl": target, "dt": "t", "q": text})
		async with self.session.get(f"https://translate.googleapis.com/translate_a/single?{querystring}") as response:
			result = json.loads(await response.text())
		new_source = result[2]
		result_text = "".join(map(lambda item: item[0], result[0]))

		message = await ctx.send(embed=discord.Embed(
			title=":nerd: Quick translation",
			colour=0x7dc5b6,
			description=f"From language: **{new_source.upper()}**```\n{text}```To language: **{target.upper()}**```\n{result_text}```",
			timestamp=datetime.datetime.utcnow()
		))
		self.bot.set_answer(ctx.message.id, message)

def setup(bot):
	timeout = aiohttp.ClientTimeout(total=3)
	session = aiohttp.ClientSession(timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
	bot.add_cog(SimpleCmds(bot, session))