import os
import sys
import platform
import signal
import asyncio
import discord
from discord.ext import commands
import json

with open("/volume1/documents/git/skye-net-terminator/config.json") as f:
    config = json.load(f)

bot_ready = False

token = config["TOKEN"]
client_id = config["CLIENT_ID"]
ownerid = config["OWNER"]
stdout_channel_id = config["STDOUT"]

intents = discord.Intents.default()
intents.members = True
discord_bot = commands.Bot(command_prefix="!", intents=intents)

script_kill = "pkill -f 'skyenet.py'"
script_run = "nohup python3 /volume1/documents/git/skye-net/skyenet.py &"
script_clear_nohup = "> nohup.out"
script_read_nohup = "cat nohup.out"

def kill_skyenet():
	os.system(script_kill)

def run_skyenet():
	os.system(script_clear_nohup)
	os.system(script_run)

def restart_skyenet():
	kill_skyenet()
	run_skyenet()

def owner():
	def predicate(interaction:discord.Interaction) -> bool:
		return interaction.user.id == ownerid
	return discord.app_commands.check(predicate)

@discord_bot.tree.command(description="Kill Terminator")
@owner()
async def die(interaction:discord.Interaction):
	await interaction.followup.send("Terminator TERMINATED")
	kill_skyenet()
	await discord_bot.close()

	if platform.system() == "Windows":
		os.kill(os.getpid(), signal.SIGTERM)
	else:
		os.kill(os.getpid(), signal.SIGKILL)

@discord_bot.tree.command(description="Kill Skye-net")
@owner()
async def kill(interaction:discord.Interaction):
	await interaction.response.defer()
	kill_skyenet()
	await interaction.response.send_message("Skye-net TERMINATED")

@discord_bot.tree.command(description="Run Skye-net")
@owner()
async def run(interaction:discord.Interaction):
	await interaction.response.defer()
	run_skyenet()
	await interaction.response.send_message("Skye-net RESURRECTED")

@discord_bot.tree.command(description="Restart Skye-net")
@owner()
async def restart(interaction:discord.Interaction):
	await interaction.response.defer()
	kill_skyenet()
	await run(interaction)

@discord_bot.tree.command(description="Check nohup.out")
@owner()
async def check(interaction:discord.Interaction):
	await interaction.response.defer()
	output = os.popen(script_read_nohup).read()
	if not output or len(output) == 0:
		output = "nohup.out is empty"
	await interaction.response.send_message(output)

@discord_bot.tree.command(description="Run custom commands")
@owner()
async def script(interaction:discord.Interaction, command:str="", message_id:int=0):
	await interaction.response.defer()
	if not command and message_id == 0:
		await interaction.response.send_message("Provide either a single command, or a message_id with multiple commands")
	elif command and message_id == 0:
		os.system(command)
		await interaction.response.send_message(f"Ran custom command `{command}`")
	elif not command and message_id != 0:
		commands_message = await interaction.channel.fetch_message(message_id)
		commands_list = commands_message.content.split("\n")
		for cmd in commands_list:
			os.system(cmd)
		await interaction.response.send_message("Ran custom commands")
	else:
		await interaction.response.send_message("Provide either a single command, or a message_id with multiple commands. Not both")

@discord_bot.tree.command(description="Print working directory")
@owner()
async def pwd(interaction:discord.Interaction):
	await interaction.response.send_message(os.getcwd())

@discord_bot.event
async def on_ready():
	global bot_ready
	await discord_bot.change_presence(status=discord.Status.do_not_disturb, activity=discord.CustomActivity("Watching Skye-net...", type=discord.ActivityType.watching))
	await discord_bot.tree.sync()
	print(f"{discord_bot.user} is ready and online >:)")
	if not bot_ready:
		# First time starting
		restart_skyenet()
		print("Starting Skye-net...")
	bot_ready = True

def send_message(channel:discord.abc.Messageable, message:str) -> None:
	if len(message) > 2000:  # discord won't allow longer than 2000 characters, so split it up
		for i in range(0, len(message), 2000):
			chunk = message[i:i+2000]
			_ = asyncio.ensure_future(channel.send(chunk)) # pretend to save to variable to prevent garbage collection
	else:
		_ = asyncio.ensure_future(channel.send(message))

def send_output_to_discord(message:str):
	message = message.strip()
	if message:
		channel = discord_bot.get_channel(stdout_channel_id)
		if channel:
			try: # catch error code 32: broken pipe
				send_message(channel, message)
			except discord.HTTPException as e:
				if e.code == 32:
					asyncio.sleep(0.5) # wait for a bit and try again
					send_message(channel, message)

async def run_bot():
	sys.stdout.write = send_output_to_discord
	sys.stderr.write = send_output_to_discord

	try:
		await discord_bot.start(token)
	except Exception as e:
		print(f"Error: {e}")

try:
	asyncio.run(run_bot())
except KeyboardInterrupt:
	pass
