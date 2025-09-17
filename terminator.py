import os
import sys
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
token = str(os.getenv("TOKEN"))
client_id = str(os.getenv("CLIENT_ID"))
ownerid = int(os.getenv("OWNER"))
stdout_channel_id = int(os.getenv("STDOUT"))

intents = discord.Intents.default()
intents.members = True
discord_bot = commands.Bot(command_prefix="!", intents=intents)

def owner():
	def predicate(interaction:discord.Interaction) -> bool:
		return interaction.user.id == ownerid
	return discord.app_commands.check(predicate)

@discord_bot.tree.command(description="Kill Skye-net")
@owner
async def kill(interaction:discord.Interaction):
	await interaction.response.defer()
	os.system("pkill -f 'skyenet.py'")
	await interaction.response.send_message("Skye-net TERMINATED")

@discord_bot.tree.command(description="Run Skye-net")
@owner
async def run(interaction:discord.Interaction):
	await interaction.response.defer()
	os.system("> nohup.out")
	os.system("nohup python3 skyenet.py &")
	await interaction.response.send_message("Skye-net RESURRECTED")

@discord_bot.tree.command(description="Restart Skye-net")
@owner
async def restart(interaction:discord.Interaction):
	await interaction.response.defer()
	os.system("pkill -f 'skyenet.py'")
	os.system("> nohup.out")
	os.system("nohup python3 skyenet.py &")
	await interaction.response.send_message("Skye-net TERMINATED and RESURRECTED")

@discord_bot.tree.command(description="Check nohup.out")
@owner
async def check(interaction:discord.Interaction):
	await interaction.response.defer()
	output = os.popen("cat nohup.out").read()
	if not output or len(output) == 0:
		output = "nohup.out is empty"
	await interaction.response.send_message(output)

@discord_bot.tree.command(description="Run custom commands")
@owner
async def run_custom_script(interaction:discord.Interaction, command:str="", message_id:int=0):
	await interaction.response.defer()
	if not command and message_id == 0:
		await interaction.response.send_message("Provide either a single command, or a message_id with multiple commands")
	elif command and message_id == 0:
		os.system(command)
		await interaction.response.send_message("Ran custom command")
	elif not command and message_id != 0:
		commands_message = await interaction.channel.fetch_message(message_id)
		commands_list = commands_message.content.split("\n")
		for cmd in commands_list:
			os.system(cmd)
		await interaction.response.send_message("Ran custom commands")
	else:
		await interaction.response.send_message("Provide either a single command, or a message_id with multiple commands. Not both")

@discord_bot.event
async def on_ready():
	await discord_bot.change_presence(status=discord.Status.do_not_disturb, activity=discord.CustomActivity("Watching Skye-net...", type=discord.ActivityType.watching))
	await discord_bot.tree.sync()
	print(f"{discord_bot.user} is ready and online >:)")

def send_message(channel:discord.abc.Messageable, message:str) -> None:
	if len(message) > 2000:  # discord won't allow longer than 2000 characters, so split it up
		for i in range(0, len(message), 2000):
			chunk = message[i:i+2000]
			asyncio.ensure_future(channel.send(chunk))
	else:
		asyncio.ensure_future(channel.send(message))

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