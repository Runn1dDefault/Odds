from db.connections import db
from db.models.event import ExchangeEvent, BookmakerEvent, MatchesEvent


def create_all_models() -> None:
    with db:
        ExchangeEvent.create_table()
        BookmakerEvent.create_table()
        MatchesEvent.create_table()


def create_exchange_event(**query) -> ExchangeEvent:
    with db.atomic():
        return ExchangeEvent.create(**query)


def create_bookmaker_event(**query) -> BookmakerEvent:
    with db.atomic():
        return BookmakerEvent.create(**query)


def create_matches_event(**query) -> MatchesEvent:
    with db.atomic():
        return MatchesEvent.create(**query)
