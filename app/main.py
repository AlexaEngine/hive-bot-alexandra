import sys
import os
import logging
from telegram.ext import Application, CommandHandler, ConversationHandler, MessageHandler, filters

# Ensure the parent directory is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
print(f"sys.path: {sys.path}")  # Debugging: Print sys.path to verify correct paths

from app.bot.commands import add_command_handlers
from app.config import TELEGRAM_API_KEY, logger

# Create the Application and pass it your bot's token.
application = Application.builder().token(TELEGRAM_API_KEY).build()

# Add all command handlers using the function from commands.py
add_command_handlers(application)

# Start the Bot
if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    logger = logging.getLogger(__name__)
    application.run_polling()
