from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CallbackContext, ConversationHandler
from app.config import logger
from app.bot.utils import check_membership, verify_number, handle_verification_failure, extract_initial_load_criteria, check_missing_or_unclear_fields
from app.bot.calculations import calculate_approximate_rate_quote
from app.api.chatbot import get_chatbot_response

# Define the conversation states
START, ENTER_NUMBER, VERIFY_NUMBER, CONFIRM_COMPANY, AWAITING_RATE_COMMAND, INITIALIZE_RATE_QUOTE, COLLECTING_RATE_INFO, CALCULATING_RATE_QUOTE, AWAITING_RATE_DECISION, POST_RATE_ACTION = range(10)

async def start(update: Update, context: CallbackContext) -> int:
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

    if not await check_membership(update, context):
        await update.message.reply_text('Sorry, this bot is only for members of our private channel.')
        return ConversationHandler.END
    
    await update.message.reply_text(
        "Hi, thanks for being a member of Hive Engine Logistics and welcome to our Hive-Bot! Please enter your MC or DOT number to get started.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ENTER_NUMBER

async def enter_number(update: Update, context: CallbackContext) -> int:
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    number = update.message.text.strip()
    context.user_data['number'] = number
    
    response = await verify_number(number, context, update)
    
    if response['status'] == 'verified':
        context.user_data['company_details'] = response['data']
        companyName = response['data']['carrier']['legalName'] or response['data']['carrier']['dbaName']
        reply_keyboard = [['YES', 'NO']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        await update.message.reply_text(f"Is {companyName} your company?", reply_markup=markup)
        return CONFIRM_COMPANY
    else:
        await update.message.reply_text("Your MC/DOT number could not be verified. Please try again.")
        return ENTER_NUMBER

async def confirm_company(update: Update, context: CallbackContext) -> int:
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    user_response = update.message.text.strip().upper()
    if user_response == 'YES':
        await update.message.reply_text(
            "Your MC/DOT number is verified. You can now type '/rate' to request a rate quote.",
            reply_markup=ReplyKeyboardRemove()
        )
        return AWAITING_RATE_COMMAND
    else:
        await update.message.reply_text("Please re-enter your MC/DOT number.")
        return ENTER_NUMBER

async def rate_quote(update: Update, context: CallbackContext) -> int:
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sure, let's calculate a rate quote. Please provide these details about the load: shipper city, consignee city, distance, weight, equipment type, hazmat (yes/no), number of extra stops, and driver assistance (yes/no).",
        reply_markup=ReplyKeyboardRemove(),
    )
    context.user_data['rate_quote_info'] = {}
    return INITIALIZE_RATE_QUOTE

async def extract_and_calculate_rate_quote(update: Update, context: CallbackContext) -> int:
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    
    load_criteria = await extract_initial_load_criteria(update, context)
    missing_fields = await check_missing_or_unclear_fields(load_criteria, update)

    if missing_fields:
        if 'rate_quote' not in context.user_data:
            await ask_for_clarification(update.effective_chat.id, "Please provide more details.", context)
            context.user_data['rate_quote'] = True
            return INITIALIZE_RATE_QUOTE

    rate_quote = await calculate_approximate_rate_quote(load_criteria, update, context)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"The estimated rate is: ${rate_quote}")

    await context.bot.send_message(chat_id=update.effective_chat.id, text="Please provide your feedback on the quote or let me know if you want to request another quote or switch to conversational mode.")

    return POST_RATE_ACTION

async def collect_rate_info(update: Update, context: CallbackContext) -> int:
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

    load_criteria = await extract_initial_load_criteria(update, context)
    rate_quote_message = await calculate_approximate_rate_quote(load_criteria, update, context)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=rate_quote_message)
    return POST_RATE_ACTION

async def post_rate_action(update: Update, context: CallbackContext) -> int:
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

async def handle_rate_decision(update: Update, context: CallbackContext) -> int:
    user_response = update.message.text.strip().upper()
    if user_response == 'YES':
        await update.message.reply_text(
            "Great! Go ahead with another rate quote.",
            reply_markup=ReplyKeyboardRemove()
        )
        return INITIALIZE_RATE_QUOTE
    else:
        await update.message.reply_text(
            "Thank you for using Hive Bot. Have a great day!",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

async def ask_for_clarification(chat_id, prompt, context):
    response = get_chatbot_response(prompt)
    await context.bot.send_message(chat_id=chat_id, text=response)
    return "user response here"

def error_handler(update: Update, context: CallbackContext):
    logger.warning(f'Update "{update}" caused error "{context.error}"')
    context.bot.send_message(chat_id=update.effective_chat.id, text="An error occurred. Please try again or type '/cancel' to restart.")
    return POST_RATE_ACTION

async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text('Operation cancelled.', reply_markup=ReplyKeyboardRemove())
    return AWAITING_RATE_COMMAND
