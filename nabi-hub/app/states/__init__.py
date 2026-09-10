"""Stateهای FSM پروژه / FSM states."""
from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    """فرآیندهای سمت کاربر."""

    waiting_password = State()


class UploadStates(StatesGroup):
    """فرآیند آپلود فایل."""

    waiting_file = State()
    waiting_album = State()
    waiting_link = State()
    waiting_caption = State()


class AdminStates(StatesGroup):
    """فرآیندهای مدیریتی."""

    waiting_broadcast = State()
    waiting_forward_broadcast = State()
    waiting_channel = State()
    waiting_reaction_post = State()
    waiting_reaction_emoji = State()
    waiting_admin_id = State()
    waiting_user_id = State()
    waiting_delete_code = State()
    waiting_timer = State()
    waiting_password = State()
    waiting_file_password = State()
    waiting_group = State()
    waiting_log_channel = State()


class TextStates(StatesGroup):
    """ویرایش متون."""

    waiting_start_text = State()
    waiting_lock_text = State()
    waiting_caption = State()
