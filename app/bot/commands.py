from telegram.ext import CommandHandler, ConversationHandler, MessageHandler, filters
from app.bot.handlers import start, rate_quote, help_command, cancel
from app.bot.lookup import lookup_start, lookup_process, cancel_lookup

def add_command_handlers(dispatcher):
    """Add all command handlers to the dispatcher."""
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('rate', rate_quote))
    dispatcher.add_handler(CommandHandler('help', help_command))
    dispatcher.add_handler(CommandHandler('cancel', cancel))

    # Add conversation handler for the lookup command
    lookup_handler = ConversationHandler(
        entry_points=[CommandHandler('lookup', lookup_start)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, lookup_process)],
        },
        fallbacks=[CommandHandler('cancel', cancel_lookup)],
    )

    dispatcher.add_handler(lookup_handler)
