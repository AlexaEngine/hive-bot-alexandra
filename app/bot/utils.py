import re
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import CallbackContext
import requests
import openai
import os
from app.config import FMCSA_API_KEY, logger

# Load environment variables for OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Function to check membership in a specific Telegram channel
async def check_membership(update: Update, context: CallbackContext) -> bool:
    channel_id = '-1001420252334'
    user_id = update.effective_user.id

    try:
        member = await context.bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator'] or member.user.username == 'Alvin_dispatch':
            return True
    except Exception as e:
        logger.error(f"Error checking membership: {e}")
    return False

# Function to verify MC or DOT number
async def verify_number(number_type: str, number: str, context: CallbackContext, update: Update) -> dict:
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

    if number_type.upper() == "DOT":
        response = await verify_dot(number, context, update)
    elif number_type.upper() == "MC":
        response = await verify_mc(number, context)
    else:
        return {'status': 'error', 'message': 'Invalid number type provided. Please specify either MC or DOT.'}

    return response

# Function to verify DOT number
async def verify_dot(user_message, context: CallbackContext, update: Update):
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    dot_number = user_message
    response = requests.get(f"https://mobile.fmcsa.dot.gov/qc/services/carriers/{dot_number}?webKey={FMCSA_API_KEY}")

    if response.status_code == 200:
        json_response = response.json()
        if "content" in json_response and json_response["content"]:
            return {'status': 'verified', 'message': 'MC/DOT number verified.', 'data': json_response["content"]}
        else:
            return {'status': 'not_verified', 'message': 'DOT info not found. Please re-enter an MC or DOT number.'}
    else:
        return {'status': 'not_verified', 'message': 'DOT info not found. Please re-enter an MC or DOT number.'}

# Function to verify MC number
async def verify_mc(user_message, context: CallbackContext):
    mc_number = user_message
    response = requests.get(f"https://mobile.fmcsa.dot.gov/qc/services/carriers/docket-number/{mc_number}?webKey={FMCSA_API_KEY}")
    if response.status_code == 200:
        json_response = response.json()
        if "content" in json_response and json_response["content"]:
            return {'status': 'verified', 'message': 'MC/DOT number verified.', 'data': json_response["content"][0]}
        else:
            return {'status': 'not_verified', 'message': 'MC info not found. Please re-enter an MC or DOT number.'}
    else:
        return {'status': 'not_verified', 'message': 'MC info not found. Please re-enter an MC or DOT number.'}

# Function to handle verification failure
async def handle_verification_failure(update: Update, response):
    if response and response['status'] == 'not_verified':
        message = "Your MC/DOT number could not be verified. Please try again or contact support."
    else:
        message = "I couldn't verify your MC/DOT number. Please ensure it's correct and try again."
    await update.message.reply_text(message, reply_markup=ReplyKeyboardRemove())

# Function to assist with unclear input using GPT
async def get_gpt_help(user_message: str) -> str:
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an assistant helping with freight logistics."},
                {"role": "user", "content": f"Please assist in interpreting the following input: '{user_message}'. Extract and clarify any unclear logistics details."}
            ],
            max_tokens=150
        )
        return response.choices[0]['message']['content'].strip()
    except Exception as e:
        return f"Sorry, I couldn't process your request due to an error: {e}"

# Function to extract initial load criteria from user message
async def extract_initial_load_criteria(update: Update, context: CallbackContext) -> dict:
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

# Function to check for missing or unclear fields in load criteria
async def check_missing_or_unclear_fields(load_criteria, update: Update):
    missing_fields = [field for field, value in load_criteria.items() if value is None or value == 'Unknown' or value == '']
    if missing_fields:
        message = "The following fields are missing or need clarification:\n"
        for field in missing_fields:
            message += f"{field}: \n"
        message += "Please re-enter only the missing fields, for example: 'distance: 280 miles.'"
        await update.message.reply_text(message)
    return missing_fields
