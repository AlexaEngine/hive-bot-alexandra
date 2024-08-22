import logging
from telegram.ext import Application, CommandHandler, ConversationHandler, MessageHandler, filters
from app.bot.handlers import (
    start, 
    enter_number, 
    confirm_company, 
    rate_quote, 
    extract_and_calculate_rate_quote, 
    post_rate_action, 
    cancel, 
    help_command
)
from app.bot.lookup import lookup_start, lookup_process, cancel_lookup
from app.config import TELEGRAM_API_KEY

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

application = Application.builder().token(TELEGRAM_API_KEY).build()

# Define conversation states
(START, ENTER_NUMBER, CONFIRM_COMPANY, AWAITING_RATE_COMMAND, 
 INITIALIZE_RATE_QUOTE, POST_RATE_ACTION, LOOKUP_NUMBER) = range(7)

# Define the main conversation handler
conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        ENTER_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_number)],
        CONFIRM_COMPANY: [MessageHandler(filters.TEXT, confirm_company)],
        AWAITING_RATE_COMMAND: [
            CommandHandler('rate', rate_quote),
            CommandHandler('lookup', lookup_start),
        ],
        INITIALIZE_RATE_QUOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, extract_and_calculate_rate_quote)],
        POST_RATE_ACTION: [MessageHandler(filters.TEXT, post_rate_action)],
        LOOKUP_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, lookup_process)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
)

# Add handlers to the application
application.add_handler(conv_handler)
application.add_handler(CommandHandler('help', help_command))

# Start the bot
if __name__ == '__main__':
    application.run_polling()
