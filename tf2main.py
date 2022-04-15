import sqlite3
import disnake
from disnake.ext import commands

intents = disnake.Intents

bot = commands.Bot(command_prefix='unused lol', intents=intents)

bot.run(open('token.txt', 'r').read())