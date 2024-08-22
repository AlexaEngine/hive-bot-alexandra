from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CallbackContext, ConversationHandler
from app.config import logger
from app.bot.utils import (
    check_membership, 
    verify_number, 
    handle_verification_failure, 
    extract_initial_load_criteria, 
    check_missing_or_unclear_fields,
    get_gpt_help
)
from app.bot.calculations import calculate_approximate_rate_quote

# Define states for conversation handler
(START, ENTER_NUMBER, CONFIRM_COMPANY, AWAITING_RATE_COMMAND, 
 INITIALIZE_RATE_QUOTE, POST_RATE_ACTION, LOOKUP_NUMBER) = range(7)

async def start(update: Update, context: CallbackContext) -> int:
    """Start the bot by checking membership and requesting an MC or DOT number."""
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

    logger.info("Start command invoked")

    if not await check_membership(update, context):
        await update.message.reply_text('Sorry, this bot is only for members of our private channel.')
        return ConversationHandler.END
    
    await update.message.reply_text(
        "Hi, thanks for being a member of Hive Engine Logistics and welcome to our Hive-Bot! "
        "Please enter your MC or DOT number (e.g., 'MC 123456' or 'DOT 654321') to get started.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ENTER_NUMBER

async def enter_number(update: Update, context: CallbackContext) -> int:
    """Verify the MC/DOT number provided by the user."""
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

    logger.info(f"Received MC/DOT number: {update.message.text}")
    
    try:
        number_type, number = update.message.text.strip().split(maxsplit=1)
    except ValueError:
        await update.message.reply_text("Please enter a valid MC or DOT number in the format: 'MC 123456' or 'DOT 654321'.")
        return ENTER_NUMBER
    
    response = await verify_number(number_type.upper(), number.strip(), context, update)
    
    if response['status'] == 'verified':
        context.user_data['company_details'] = response['data']
        company_name = response['data']['carrier'].get('legalName') or response['data']['carrier'].get('dbaName', 'Unknown Company')
        
        reply_keyboard = [['YES', 'NO']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        await update.message.reply_text(f"Is {company_name} your company?", reply_markup=markup)
        return CONFIRM_COMPANY
    else:
        await update.message.reply_text("Your MC/DOT number could not be verified. Please try again.")
        return ENTER_NUMBER

async def confirm_company(update: Update, context: CallbackContext) -> int:
    """Handle company confirmation and display available commands if verified."""
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    
    user_response = update.message.text.strip().upper()
    if user_response == 'YES':
        await update.message.reply_text(
            "Your MC/DOT number is verified. You can now use the following commands:\n"
            "/help - See available commands.",
            reply_markup=ReplyKeyboardRemove()
        )
        await help_command(update, context)
        return AWAITING_RATE_COMMAND
    else:
        await update.message.reply_text("Please re-enter your MC/DOT number.")
        return ENTER_NUMBER

async def rate_quote(update: Update, context: CallbackContext) -> int:
    """Request details for calculating a rate quote."""
    logger.info("rate_quote function invoked")
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sure, let's calculate a rate quote. Please provide the following details: shipper city, consignee city, distance, weight, equipment type, hazmat (yes/no), number of extra stops, and driver assistance (yes/no).",
        reply_markup=ReplyKeyboardRemove(),
    )

    context.user_data['rate_quote_info'] = {}
    return INITIALIZE_RATE_QUOTE

async def extract_and_calculate_rate_quote(update: Update, context: CallbackContext) -> int:
    """Extract load criteria and calculate the rate quote based on user input."""
    logger.info("extract_and_calculate_rate_quote function invoked")
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

    load_criteria = await extract_initial_load_criteria(update, context)
    logger.debug(f"Load criteria extracted: {load_criteria}")

    if not load_criteria:
        await update.message.reply_text("I couldn't understand the details you provided. Let me try to assist you better.")
        gpt_response = await get_gpt_help(update.message.text)
        await update.message.reply_text(gpt_response)
        return INITIALIZE_RATE_QUOTE

    missing_fields = await check_missing_or_unclear_fields(load_criteria, update)

    if missing_fields:
        return INITIALIZE_RATE_QUOTE

    try:
        rate_quote = await calculate_approximate_rate_quote(load_criteria, update, context)
        logger.info(f"Calculated rate quote: {rate_quote}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"The estimated rate is: {rate_quote}")
    except Exception as e:
        await context.bot
    except Exception as e:
        logger.error(f"Error calculating rate quote: {e}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I encountered an issue while calculating the rate. Let me try another method.")
        
        # Attempt fallback calculation using GPT or another method
        gpt_response = await get_gpt_help(update.message.text)
        await update.message.reply_text(gpt_response)
        
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Please provide your feedback on the quote or let me know if you want to request another quote or switch to conversational mode.")
    return POST_RATE_ACTION

async def post_rate_action(update: Update, context: CallbackContext) -> int:
    """Handle post-quote user actions."""
    user_response = update.message.text.strip().upper()
    if user_response == 'YES':
        await update.message.reply_text(
            "Please provide the new details for your rate quote.",
            reply_markup=ReplyKeyboardRemove()
        )
        return INITIALIZE_RATE_QUOTE
    elif user_response == 'NO':
        await update.message.reply_text("Thank you for using Hive Bot. Have a great day!", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    else:
        await update.message.reply_text("Have another load to quote? Please reply with 'Yes' to continue or 'No' to exit.")
        return POST_RATE_ACTION

async def cancel(update: Update, context: CallbackContext) -> int:
    """Cancel the current operation."""
    await update.message.reply_text('Operation cancelled.', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def help_command(update: Update, context: CallbackContext):
    """Display help text with available bot commands."""
    help_text = (
        "/start - Start the bot and verify your MC/DOT number.\n"
        "/rate - Request a rate quote for a load.\n"
        "/lookup - Look up the safety rating of a company by MC/DOT number.\n"
        "/cancel - Cancel the current operation.\n"
        "/help - Display this help message."
    )
    await update.message.reply_text(help_text)

def error_handler(update: Update, context: CallbackContext):
    """Log errors and send an error message to the user."""
    logger.warning(f'Update "{update}" caused error "{context.error}"')
    context.bot.send_message(chat_id=update.effective_chat.id, text="An error occurred. Please try again or type '/cancel' to restart.")
