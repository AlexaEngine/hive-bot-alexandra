from telegram import Update
from telegram.ext import CallbackContext

# Import utility functions if needed
from app.bot.utils import verify_number

async def lookup_start(update: Update, context: CallbackContext):
    """Start the lookup process."""
    await update.message.reply_text(
        "Please provide the MC or DOT number in the format: '/lookup MC 123456' or '/lookup DOT 654321'."
    )
    return 1  # Transition to the next state

async def lookup_process(update: Update, context: CallbackContext):
    """Process the lookup of the MC or DOT number."""
    number_type, number = update.message.text.strip().split(maxsplit=1)
    response = await verify_number(number_type.upper(), number.strip(), context, update)
    
    if response['status'] == 'verified':
        company_data = response['data']
        safety_rating = company_data.get('safetyRating', 'No safety rating available')
        company_name = company_data.get('carrier', {}).get('legalName') or company_data.get('carrier', {}).get('dbaName', 'Unknown Company')
        await update.message.reply_text(
            f"Company: {company_name}\nSafety Rating: {safety_rating}"
        )
    else:
        await update.message.reply_text("The MC/DOT number you provided could not be verified. Please try again.")
    return ConversationHandler.END  # End the conversation after the lookup

async def cancel_lookup(update: Update, context: CallbackContext):
    """Cancel the lookup operation."""
    await update.message.reply_text("Lookup operation has been canceled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END  # End the conversation
