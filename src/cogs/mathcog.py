import objects.utils as utils
from discord.ext import commands

import asyncio
import discord
import json
import math
import os
import subprocess
import sys

utils.set_cog_name("cogs.mathcog")

MATH_EXCLUDES = (
	'isclose',
	'isfinite',
	'isinf',
	'isnan'
)
MATH_FUNCTIONS = tuple(f for f in dir(math) if not f.startswith('__') and not f in MATH_EXCLUDES)

class DangerousError(Exception):
	"""Raised when dangerous expressions are evaluated."""
	pass


_eval_script = """
import sys, json, math
_G = json.loads(sys.argv[1])
expr = _G.pop('expr')
_G = {f:getattr(math, f) for f in _G.get('_G')}
_G.update(dict(__builtins__={}))
try:
	result = eval(expr, _G)
	success = True
except Exception as e:
	success = False
	result = f'{e.__class__.__name__}: {e}'

print(json.dumps({
	'success': success,
	'result': result
}))
"""

async def eval_math(expr):
	for dangerous in ('lambda', 'for', '__builtins__', '__class__'):
		if dangerous in expr:
			return False, f'DangerousError: The use of "{dangerous}" is not permitted.'

	_G = dict(expr=expr, _G=MATH_FUNCTIONS)

	if not os.path.exists('_eval_script.py'):
		with open('_eval_script.py', 'w') as f:
			f.write(_eval_script)

	process = subprocess.Popen([sys.executable, '_eval_script.py', json.dumps(_G)], stdout=subprocess.PIPE)

	loop = asyncio.get_running_loop()
	time = loop.time()
	while process.poll() is None:
		if loop.time()-time>=.5:
			process.kill()
			break
		await asyncio.sleep(.1)
	else:
		result = json.loads(process.stdout.read())
		return result.get('success'), result.get('result')
	return False, 'TimeoutError: The command took too much time.'


class MathCog(commands.Cog, name="Math Cog"):
	"""You can find here the math functions"""

	def __init__(self):
		pass

	@commands.Cog.listener()
	async def on_message(self, msg):
		if not msg.author.bot and msg.content.startswith('='):
			success, result = await eval_math(msg.content[1:])
			if not success:
				return await ctx.send(f'An error occurred: `{result}`')

			message = f'`{msg.content[1:]} = {result}`'
			if len(message)>1000:
				message = 'It seems that the result is too large for Discord. :thinking:'

			await msg.channel.send(message)

	@commands.command()
	@utils.command_check()
	@commands.bot_has_permissions(send_messages=True)
	async def math(self, ctx, *args):
		"""{{Compute a math expression}}
		[[Begins your message with `=expression` will trigger this command.]]
		(([expression]))
		++.math 1+1++
		"""
		success, result = await eval_math(' '.join(args))
		if not success:
			return await ctx.send(f'An error occurred: `{result}`')

		message = f'`{" ".join(args)} = {result}`'
		if len(message)>1000:
				message = 'It seems that the result is too large for Discord. :thinking:'

		await ctx.send(message)


def setup(bot):
	bot.add_cog(MathCog())