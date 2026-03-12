"""FSM states for the bot."""
from aiogram.fsm.state import State, StatesGroup


class DownloadState(StatesGroup):
    """States for the URL download flow."""
    waiting_quality = State()    # user has sent URL, choosing quality
    downloading = State()        # download in progress


class CookieState(StatesGroup):
    """States for the /cookies flow."""
    waiting_file = State()       # waiting for .txt cookie file


class LanguageState(StatesGroup):
    """States for the /language flow."""
    choosing = State()


class FileUploadState(StatesGroup):
    """States for user-uploaded files."""
    idle = State()               # no active upload
