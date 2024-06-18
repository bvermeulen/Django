# common values for app boards
MESSAGE_FIELD_SIZE = 20000
BOARD_NAME_SIZE = 30
DESCRIPTION_SIZE = 100
TOPIC_SUBJECT_SIZE = 255
POSTS_PER_PAGE = 10
TOPICS_PER_PAGE = 10
HAS_MANY_PAGES_LIMIT = 3
POST_SUBJECT_SIZE = 255
EXCLUDE_USERS = ["default_user", "moderator"]
MAX_SYMBOLS_ALLOWED = 20

# common values for app newsfeed
DELAY_FACTOR = 35
MIN_CHARS = 350
BANNER_LENGTH = 150
WIDTH_TITLE = 120
HELP_ARROWS = "Use left/ right arrow keys to toggle news items or press auto-scroll. "
HELP_BANNER = "Press banner to toggle it on or off. "
IMG_WIDTH_PX = 900
IMG_WIDTH_PERC = "70%"
RIGHT_ARROW = "\u25B6"
LEFT_ARROW = "\u25C0"
ITEMS_PER_PAGE = 15

# common values for app stock
URL_ALPHAVANTAGE = "www.alphavantage.co"
URL_WORLDTRADE = "www.worldtradedata.com"
URL_FMP = "financialmodelingprep.com"
MARKETS = ["XNAS", "XNYS", "XAMS", "INDEX"]
BASE_CURRENCIES = [("EUR", "EUR"), ("USD", "USD")]
STOCK_DETAILS = [("Graphs", "Graphs"), ("News", "News"), ("Press", "Press")]
CARET_UP = "\u25B2"  # up triangle
CARET_DOWN = "\u25BC"  # down triangle
CARET_NO_CHANGE = "\u25AC"  # rectangle
PLOT_PERIODS = ["0.5", "1", "3", "max"]

# accoount variables
CAPTCHA_FONT_SIZE = 30
CAPTCHA_LETTER_ROTATION = (-40, 20)
CAPTCHA_BACKGROUND_COLOR = "yellow"
CAPTCHA_FOREGROUND_COLOR = "blue"
TEXT_VERIFICATION_SUCCESS_MESSAGE = """
Your email is verified successfully and your account has been activated.
You can login with your credentials now...
"""
TEXT_VERIFICATION_FAILED_MESSAGE = """
There is something wrong with this link, we cannot verify the user.
"""