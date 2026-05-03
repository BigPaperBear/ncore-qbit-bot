import os
import sys
from unittest.mock import patch, AsyncMock, MagicMock

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from telegram.ext import ConversationHandler
import handlers


def _make_update(user_id=42, callback_data=None):
    update = MagicMock()
    update.effective_user.id = user_id
    update.effective_chat.id = 100
    update.message.reply_text = AsyncMock()
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    update.callback_query.data = callback_data
    return update


def _make_context(args=None, user_data=None):
    context = MagicMock()
    context.args = args or []
    context.user_data = user_data if user_data is not None else {}
    return context


@pytest.mark.asyncio
async def test_dl_command_rejects_disallowed_user():
    update = _make_update(user_id=999)
    context = _make_context(args=['Inception'])
    with patch.object(handlers.config, 'ALLOWED_USERS', [42]):
        result = await handlers.dl_command(update, context)
    assert result == ConversationHandler.END
    update.message.reply_text.assert_awaited_once()
    assert "permission" in update.message.reply_text.call_args[0][0].lower()


@pytest.mark.asyncio
async def test_dl_command_with_no_query_shows_usage():
    update = _make_update()
    context = _make_context(args=[])
    with patch.object(handlers.config, 'ALLOWED_USERS', [42]):
        result = await handlers.dl_command(update, context)
    assert result == ConversationHandler.END
    assert 'Usage' in update.message.reply_text.call_args[0][0]


@pytest.mark.asyncio
async def test_dl_command_with_query_asks_movie_or_series():
    update = _make_update()
    context = _make_context(args=['Inception'])
    with patch.object(handlers.config, 'ALLOWED_USERS', [42]):
        result = await handlers.dl_command(update, context)
    assert result == handlers.SELECTING_TYPE
    assert context.user_data['query'] == 'Inception'


@pytest.mark.asyncio
async def test_type_handler_lists_search_results():
    update = _make_update(callback_data='type:movie')
    context = _make_context(user_data={'query': 'Inception'})
    fake_results = [
        {'name': 'Inception 1080p', 'seeds': '120', 'size': '14 GB', 'link': 'x'},
    ]
    with patch.object(handlers.ncore, 'search', return_value=fake_results) as search_mock:
        result = await handlers.type_handler(update, context)
    assert result == handlers.SELECTING_RESULT
    search_mock.assert_called_once()
    assert context.user_data['results'] == fake_results


@pytest.mark.asyncio
async def test_type_handler_no_results_ends_conversation():
    update = _make_update(callback_data='type:movie')
    context = _make_context(user_data={'query': 'asdfqwerty'})
    with patch.object(handlers.ncore, 'search', return_value=[]):
        result = await handlers.type_handler(update, context)
    assert result == ConversationHandler.END
