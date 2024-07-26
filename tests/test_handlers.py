import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../app/bot')))

import unittest
from unittest.mock import AsyncMock, patch
from handlers import confirm_company, rate_quote
from telegram import ReplyKeyboardRemove

class TestHandlers(unittest.IsolatedAsyncioTestCase):

    @patch('handlers.CallbackContext')
    @patch('handlers.Update')
    async def test_confirm_company_yes(self, mock_update, mock_context):
        mock_update.message.text = 'YES'
        mock_update.effective_chat.id = 12345
        mock_context.bot.send_chat_action = AsyncMock()
        mock_context.bot.send_message = AsyncMock()
        mock_context.bot.send_message.return_value = AsyncMock()
        
        result = await confirm_company(mock_update, mock_context)
        self.assertEqual(result, 'AWAITING_RATE_COMMAND')
        mock_update.message.reply_text.assert_called_with(
            "Your MC/DOT number is verified. You can now type '/rate' to request a rate quote.",
            reply_markup=ReplyKeyboardRemove()
        )

    @patch('handlers.CallbackContext')
    @patch('handlers.Update')
    async def test_confirm_company_no(self, mock_update, mock_context):
        mock_update.message.text = 'NO'
        mock_update.effective_chat.id = 12345
        mock_context.bot.send_chat_action = AsyncMock()
        mock_context.bot.send_message = AsyncMock()
        mock_context.bot.send_message.return_value = AsyncMock()
        
        result = await confirm_company(mock_update, mock_context)
        self.assertEqual(result, 'ENTER_NUMBER')
        mock_update.message.reply_text.assert_called_with("Please re-enter your MC/DOT number.")

    @patch('handlers.CallbackContext')
    @patch('handlers.Update')
    async def test_rate_quote(self, mock_update, mock_context):
        mock_update.effective_chat.id = 12345
        mock_context.bot.send_message = AsyncMock()
        
        result = await rate_quote(mock_update, mock_context)
        self.assertEqual(result, 'INITIALIZE_RATE_QUOTE')
        mock_context.bot.send_message.assert_called_with(
            chat_id=12345,
            text="Sure, let's calculate a rate quote. Please provide these details about the load: shipper city, consignee city, distance, weight, equipment type, hazmat (yes/no), number of extra stops, and driver assistance (yes/no).",
            reply_markup=ReplyKeyboardRemove(),
        )

if __name__ == '__main__':
    unittest.main()