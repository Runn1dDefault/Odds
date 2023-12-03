from datetime import datetime

import peewee as pw

from db.models.base import BaseModel


class Event(BaseModel):
    first_team = pw.CharField()
    second_team = pw.CharField()
    match_name = pw.TextField()
    category = pw.CharField()
    url = pw.CharField(null=True)
    created_at = pw.DateTimeField(default=datetime.utcnow)
    bet = pw.CharField()

    @classmethod
    def not_matches_query(cls, start_time, end_time):
        return cls.select().where(
            (cls.created_at >= start_time) &
            (cls.created_at <= end_time)
        )


class ExchangeEvent(Event):
    exchange = pw.CharField()
    lay = pw.FloatField(null=True)

    @classmethod
    def not_matches_query(cls, exchange: str, *args, **kwargs):
        return super().not_matches_query(*args, **kwargs).where(cls.exchange == exchange)


class BookmakerEvent(Event):
    bookmaker = pw.CharField()
    odds = pw.FloatField(null=True)

    @classmethod
    def not_matches_query(cls, bookmaker: str, *args, **kwargs):
        return super().not_matches_query(*args, **kwargs).where(cls.bookmaker == bookmaker)


class MatchesEvent(BaseModel):
    category = pw.CharField()
    exchange = pw.CharField()
    exchange_match_name = pw.TextField()
    lay = pw.FloatField(null=True)
    bookmaker = pw.CharField()
    bookmaker_match_name = pw.TextField()
    odds = pw.FloatField(null=True)
    created_at = pw.DateTimeField(default=datetime.utcnow)
    similarity_by_first_teams = pw.FloatField(null=True)
    similarity_by_second_teams = pw.FloatField(null=True)
    bet = pw.CharField()

    @property
    def total_similarity(self) -> float:
        similarity_first = self.similarity_by_first_teams if self.similarity_by_second_teams else 0.0
        similarity_second = self.similarity_by_second_teams if self.similarity_by_second_teams else 0.0
        return round(similarity_first + similarity_second, 2)

    @property
    def rating(self) -> float | None:
        if self.lay and self.odds:
            return self.odds / self.lay
    