from dataclasses import dataclass
from enum import Enum


class Exchange(Enum):
    SMARKETS = 'smarkets'


class Bookmaker(Enum):
    BET99 = 'bet99'


@dataclass
class Pair:
    exchange: Exchange | str
    bookmaker: Bookmaker | str

    def __post_init__(self):
        if isinstance(self.exchange, str):
            for exc in Exchange:
                if exc.value != self.exchange:
                    continue

                self.exchange = exc
                break

        assert isinstance(self.exchange, Exchange)

        if isinstance(self.bookmaker, str):
            for bk in Bookmaker:
                if bk.value != self.bookmaker:
                    continue

                self.bookmaker = bk
                break

        assert isinstance(self.bookmaker, Bookmaker)
