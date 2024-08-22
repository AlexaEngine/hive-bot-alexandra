from telegram import Update, ReplyKeyboardRemove
from telegram.ext import CallbackContext, ConversationHandler
from app.bot.utils import verify_number, handle_verification_failure

# Define states for the conversation handler specific to lookup
LOOKUP_NUMBER = 1

async def lookup_start(update: Update, context: CallbackContext) -> int:
    """Initiate the lookup process by asking for an MC or DOT number."""
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    await update.message.reply_text(
        "Please provide the MC or DOT number (e.g., 'MC 123456' or 'DOT 654321')."
    )
    return LOOKUP_NUMBER

async def lookup_process(update: Update, context: CallbackContext) -> int:
    """Process the MC or DOT number provided and return the company details."""
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

    # Process the user input without requiring a command prefix
    user_input = update.message.text.strip().split()
    if len(user_input) != 2:
        await update.message.reply_text(
            "Please provide a valid number in the format: 'MC 123456' or 'DOT 654321'."
        )
        return LOOKUP_NUMBER

    number_type, number = user_input

    response = await verify_number(number_type.upper(), number.strip(), context, update)

    if response['status'] == 'verified':
        company_data = response['data']
        safety_rating = company_data.get('safetyRating', 'No safety rating available')
        company_name = company_data.get('carrier', {}).get('legalName') or company_data.get('carrier', {}).get('dbaName', 'Unknown Company')
        drivers = company_data.get('carrier', {}).get('drivers', 'N/A')
        inspections = company_data.get('inspections', {}).get('totalInspections', 'N/A')
        insurance = company_data.get('insurance', 'No insurance data available')
        operation_type = company_data.get('operationType', 'Unknown Operation Type')
        address = company_data.get('carrier', {}).get('address', 'No address available')
        allowed_to_operate = company_data.get('carrier', {}).get('allowedToOperate', 'Unknown')

        await update.message.reply_text(
            f"**Carrier Information**\n"
            f"Legal Name: {company_name}\n"
            f"DOT Number: {number.strip()}\n"
            f"Allowed to Operate: {allowed_to_operate}\n"
            f"Operation Type: {operation_type}\n"
            f"Total Drivers: {drivers}\n"
            f"Total Inspections: {inspections}\n"
            f"Insurance: {insurance}\n"
            f"Physical Address: {address}\n"
        )
        await update.message.reply_text(
            "Thanks for using HiveEngine Rate Bot! Send another MC or DOT number to perform another lookup or '/rate' to request a rate quote."
        )
    else:
        await handle_verification_failure(update, response)

    return ConversationHandler.END

async def cancel_lookup(update: Update, context: CallbackContext) -> int:
    """Cancel the lookup operation."""
    await update.message.reply_text("Lookup operation has been canceled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END
