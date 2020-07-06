import asyncio
import json
import logging as logger
import os
from pyrogram import Client, Filters, KeyboardButton, Message, ReplyKeyboardMarkup
from pyrogram.errors import FloodWait
import re
import res
from res import Configurations

configurations_map = {
	"commands": "commands",
	"logger": "logger"
}

loop = asyncio.get_event_loop()

config = Configurations("config/config.json", configurations_map)
loop.run_until_complete(config.parse("known_devices.json"))
config.set("app_hash", os.environ.pop("app_hash", None))
config.set("app_id", int(os.environ.pop("app_id", 0)))
config.set("bot_token", os.environ.pop("bot_token", None))
config.set("bot_username", os.environ.pop("bot_username", None))
config.set("creator", int(os.environ.pop("creator", 0)))
config.set("nmap_command", "sudo nmap -sP -R 192.168.1.2-254 --exclude 192.168.1.2")

logger.basicConfig(
	filename=config.get("logger")["path"],
	datefmt="%d/%m/%Y %H:%M:%S",
	format=config.get("logger")["format"],
	level=config.get("logger").pop("level", logger.INFO))

logger.info("Initializing the Admins ...")
allowed_users_list = list(map(lambda n: n["id"], config.get("allowed_users")))

logger.info("Admins initializated\nInitializing the Client ...")
app = Client(session_name=config.get("bot_username"), api_id=config.get("app_id"), api_hash=config.get("app_hash"), bot_token=config.get("bot_token"), lang_code="it")


@app.on_message(Filters.command("help", prefixes="/") & Filters.user(allowed_users_list) & Filters.private)
async def help(_, message: Message):
	# /help
	global config

	commands = config.get("commands")

	# Filter the commands list in base at their domain
	if message.from_user.id != config.get("creator"):
		commands = list(filter(lambda n: n["domain"] != "creator", commands))

	await res.split_reply_text(config, message, "In this section you will find the list of the command of the bot.\n\t{}".format("\n\t".join(list(map(lambda n: "<code>/{}{}</code> - {}".format(n["name"], " {}".format(n["parameters"]) if n["parameters"] != "" else n["parameters"], n["description"])), commands))), quote=False)

	logger.info("I\'ve answered to /help because of {}.".format("@{}".format(message.from_user.username) if message.from_user.username is not None else message.from_user.id))


@app.on_message(Filters.command("init", prefixes="/") & Filters.user(allowed_users_list) & Filters.private)
async def initializing(client: Client, _):
	# /init
	global config

	# Setting the maximum message length
	max_length = await client.send(functions.help.GetConfig())
	config.set("message_max_length", max_length.message_length_max)

	# Retrieving the bot id
	bot = await client.get_users(config.get("bot_username"))
	config.set("bot_id", bot.id)

	logger.info("I\'ve answered to /init because of {}.".format("@{}".format(message.from_user.username) if message.from_user.username is not None else message.from_user.id))


@app.on_message(Filters.command("nmap", prefixes="/") & Filters.user(allowed_users_list) & Filters.private)
async def nmap(_, message: Message):
	# /nmap
	global config

	await res.split_reply_text(config, message, res.nmap_output(config.get("nmap_command")), quote=False)
	logger.info("I\'ve answered to /nmap because of {}.".format("@{}".format(message.from_user.username) if message.from_user.username is not None else message.from_user.id))


@app.on_message(Filters.command("query", prefixes="/") & Filters.user(allowed_users_list) & Filters.private)
async def query(client: Client, message: Message):
	# /query
	global config

	users = await client.get_users(res.parse_nmap(config))
	text = "Nobody is at home right now."

	if users is True:
		queryResult = "\t{}".format("\n\t".join(list(map(lambda n: "<a href=\"{}\">{} {}</a>".format("https://t.me/{}".format(n.username) if n.username is not None else "tg://user?id={}".format(n.id), n.first_name, n.last_name), users))))
		text = "At home there are:\n{}".format(queryResult)

	await res.split_reply_text(config, message, text, quote=False)
	logger.info("I\'ve answered to /query because of {}.".format("@{}".format(message.from_user.username) if message.from_user.username is not None else message.from_user.id))


@app.on_message(Filters.command("report", prefixes="/") & Filters.user(config.get("creator")) & Filters.private)
async def report(_, message: Message):
	# /report
	global config

	await res.split_reply_text(config, message, "\n".join(list(map(lambda n: "{} - {}".format(n["name"], n["description"]), config.get("commands")))), quote=False)

	logger.info("I\'ve answered to /report because of {}.".format("@{}".format(message.from_user.username) if message.from_user.username is not None else message.from_user.id))


@app.on_message(Filters.command("start", prefixes="/") & Filters.user(allowed_users_list) & Filters.private)
async def start(client: Client, message: Message):
	# /start
	global config

	await res.split_reply_text(config, "Welcome <a href=\"{}\">{}</a>.\nThis bot can tell you who\'s at home".format("https://t.me/{}".format(n.username) if n.username is not None else "tg://user?id={}".format(n.id), n.first_name), quote=False)
	logger.info("I\'ve answered to /start because of {}.".format("@{}".format(message.from_user.username) if message.from_user.username is not None else message.from_user.id))


@app.on_message(res.unknown_filter(config) & Filters.private)
async def unknown(_, message: Message):
	global config

	await res.split_reply_text(config, message, "This command isn\'t supported.", quote=False)
	logger.info("I managed an unsupported command.")


logger.info("Client initializated\nSetting the markup syntax ...")
app.set_parse_mode("html")
logger.info("Setted the markup syntax\nStarted serving ...")
app.run()
