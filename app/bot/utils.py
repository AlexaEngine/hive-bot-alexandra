import re
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import CallbackContext
import requests
from app.config import FMCSA_API_KEY, logger
from app.api.chatbot import get_chatbot_response

async def check_membership(update: Update, context: CallbackContext) -> bool:
    """Check if the user is a member of the required Telegram channel."""
    channel_id = '-1001420252334'
    user_id = update.effective_user.id
    
    try:
        member = await context.bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
    except Exception as e:
        logger.error(f"Error checking membership: {e}")
    return False

async def verify_number(number_type: str, number: str, context: CallbackContext, update: Update) -> dict:
    """Verify the provided MC or DOT number using the FMCSA API."""
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

    if number_type == "DOT":
        response = await verify_dot(number, context, update)
    elif number_type == "MC":
        response = await verify_mc(number, context)
    else:
        return {'status': 'error', 'message': 'Invalid number type provided. Please specify either MC or DOT.'}

    return response

async def verify_dot(number, context: CallbackContext, update: Update):
    """Verify a DOT number using the FMCSA API."""
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    response = requests.get(f"https://mobile.fmcsa.dot.gov/qc/services/carriers/{number}?webKey={FMCSA_API_KEY}")

    if response.status_code == 200:
        json_response = response.json()
        if "content" in json_response and json_response["content"]:
            return {'status': 'verified', 'message': 'MC/DOT number verified.', 'data': json_response["content"]}
        else:
            return {'status': 'not_verified', 'message': 'DOT info not found. Please re-enter an MC or DOT number.'}
    else:
        return {'status': 'not_verified', 'message': 'DOT info not found. Please re-enter an MC or DOT number.'}

async def verify_mc(number, context: CallbackContext):
    """Verify an MC number using the FMCSA API."""
    response = requests.get(f"https://mobile.fmcsa.dot.gov/qc/services/carriers/docket-number/{number}?webKey={FMCSA_API_KEY}")
    if response.status_code == 200:
        json_response = response.json()
        if "content" in json_response and json_response["content"]:
            return {'status': 'verified', 'message': 'MC/DOT number verified.', 'data': json_response["content"][0]}
        else:
            return {'status': 'not_verified', 'message': 'MC info not found. Please re-enter an MC or DOT number.'}
    else:
        return {'status': 'not_verified', 'message': 'MC info not found. Please re-enter an MC or DOT number.'}

async def handle_verification_failure(update: Update, response):
    """Handle failure to verify MC or DOT number."""
    if response and response['status'] == 'not_verified':
        message = "Your MC/DOT number could not be verified. Please try again or contact support."
    else:
        message = "I couldn't verify your MC/DOT number. Please ensure it's correct and try again."
    await update.message.reply_text(message, reply_markup=ReplyKeyboardRemove())

async def extract_initial_load_criteria(update: Update, context: CallbackContext) -> dict:
    """Extract initial load criteria from the user's message."""
    user_message = update.message.text.lower()

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

    load_criteria = {
        'driverAssistance': 'No',
        'equipmentType': 'V',
        'hazmatRouting': 'No'
    }

    regex_patterns = {
        'shipperCity': r"\b(?:from|shipper|pickup|loading)\s*([a-zA-Z\s]+),?\s*([a-zA-Z]{2})?\b",
        'consigneeCity': r"\b(?:to|consignee|delivery|unloading)\s*([a-zA-Z\s]+),?\s*([a-zA-Z]{2})?\b",
        'billDistance': r"\b(\d+)\s*miles",
        'weight': r"\b(\d+)\s*lbs",
        'equipmentType': r"(?i)\b(dry van|van|reefer|flatbed|power only|flatbed moffett|van moffett|reefer moffett)\b",
        'hazmatRouting': r"(?i)\b(hazmat|no hazmat)\b",
        'driverAssistance': r"(?i)\b(driver assist|no driver assist)\b"
    }

    for key, pattern in regex_patterns.items():
        match = re.search(pattern, user_message)
        if match:
            if key in ['shipperCity', 'consigneeCity']:
                city = match.group(1).strip()
                state = match.group(2) or ''
                load_criteria[key] = f"{city}, {state}".strip()
            else:
                load_criteria[key] = int(match.group(1)) if key in ['billDistance', 'weight'] else match.group(1)

    # If critical fields are missing, use GPT to assist
    if not all(load_criteria.values()):
        gpt_response = await get_gpt_help(user_message)
        await update.message.reply_text(gpt_response)
        return None  # Return None to indicate failure

    return load_criteria

async def check_missing_or_unclear_fields(load_criteria, update: Update):
    """Check for missing or unclear fields in the extracted load criteria."""
    missing_fields = [field for field, value in load_criteria.items() if value is None or value == 'Unknown' or value == '']
    if missing_fields:
        message = "The following fields are missing or need clarification:\n"
        for field in missing_fields:
            message += f"{field}: \n"
        message += "Please re-enter only the missing fields, for example: 'distance: 280 miles.'"
        await update.message.reply_text(message)
    return missing_fields

async def get_gpt_help(user_message: str) -> str:
    """Use GPT to assist in understanding unclear logistics details."""
    try:
        response = await get_chatbot_response(
            f"Please assist in interpreting the following input: '{user_message}'. Extract and clarify any unclear logistics details."
        )
        return response
    except Exception as e:
        logger.error(f"Error during GPT assistance: {e}")
        return "Sorry, I couldn't process your request due to an error."
