from collections import OrderedDict

from managers.types import TableField
from managers.utils import round_two_after_point


FIELDS = OrderedDict(
    Time=TableField(key='matched_time', validator=str),
    Event=TableField(key='match_name'),
    Bet=TableField(key='bet'),
    Bookmaker=TableField(key='bookmaker'),
    Odds=TableField(key='odds', validator=round_two_after_point, default_value='-'),
    Exchange=TableField(key='exchange'),
    Lay=TableField(key='lay', validator=round_two_after_point, default_value='-'),
    Category=TableField(key='category')
)

BACK_WATCH_MINUTES = 10  # how many minutes ago you need to get saved matched events
TASKS_WAIT_MINUTES = 3  # waiting time minutes for all tasks
MATCHING_WAIT_SECONDS = 10
RESULTS_WATCH_MINUTES = 3

EXCHANGE_EVENTS_QUERY = """
    SELECT DISTINCT ON (first_team, second_team) 
        first_team, second_team, match_name, category, lay, exchange, bet FROM exchangeevent 
        WHERE created_at >= '%s' AND created_at <= '%s' AND exchange = '%s'
"""
BOOKMAKER_EVENTS_QUERY = """
    SELECT DISTINCT ON (first_team, second_team) 
        first_team, second_team, match_name, category, odds, bookmaker, bet FROM bookmakerevent 
        WHERE created_at >= '%s' AND created_at <= '%s' AND bookmaker = '%s'
"""
