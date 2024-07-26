from telegram.ext import CommandHandler
from app.bot.handlers import start, rate_quote

def add_command_handlers(dispatcher):
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('rate', rate_quote))
