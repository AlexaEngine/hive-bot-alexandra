import sys
import os
import logging
from telegram.ext import Application, CommandHandler, ConversationHandler, MessageHandler, filters

# Add the parent directory of 'app' to the system path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.bot.handlers import start, enter_number, confirm_company, rate_quote, extract_and_calculate_rate_quote, collect_rate_info, post_rate_action, error_handler, cancel
from app.config import TELEGRAM_API_KEY, FMCSA_API_KEY, MONGO_CLIENT, OPENAI_API_KEY, MAX_TOKENS_LIMIT, logger

# Create the Application and pass it your bot's token.
application = Application.builder().token(TELEGRAM_API_KEY).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        ENTER_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_number)],
        CONFIRM_COMPANY: [MessageHandler(filters.TEXT, confirm_company)],
        AWAITING_RATE_COMMAND: [CommandHandler('rate', rate_quote)],
        INITIALIZE_RATE_QUOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_rate_info)],
        CALCULATING_RATE_QUOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, extract_and_calculate_rate_quote)],
        POST_RATE_ACTION: [MessageHandler(filters.TEXT, post_rate_action)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
)

application.add_handler(conv_handler)

# Start the Bot
if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    logger = logging.getLogger(__name__)
    application.run_polling()