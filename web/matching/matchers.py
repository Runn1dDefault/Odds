import logging
from typing import Any

from cdifflib import CSequenceMatcher
from pandas import DataFrame, np

from config import LOG_FORMAT


class SimilarityExchangeMatcher:
    WORDS_TO_REMOVE = ("FC", "City", "United", "(Res)", "Deportivo", "Town", "Atletico")

    def __init__(
        self,
        bm_events_df: DataFrame,
        exchange_data: dict[str, Any],
        total_min_similarity: float = 1.4,
        teams_min_similarity: float = 0.5,
        words_to_remove: list[str] = None
    ):
        self.bm_events_df = bm_events_df
        self.exchange_data = exchange_data
        self.total_min_similarity = total_min_similarity
        self.teams_min_similarity = teams_min_similarity
        self.words_to_remove = self.WORDS_TO_REMOVE if not words_to_remove else words_to_remove

        self.logger = logging.Logger(self.__class__.__name__, level=logging.NOTSET)
        log_format = logging.Formatter(LOG_FORMAT)
        console = logging.StreamHandler()
        console.setFormatter(log_format)
        self.logger.addHandler(console)

    def _remove_words(self, exc_team_first: str, exc_team_second: str, bm_team_first: str, bm_team_second: str):
        for word in self.words_to_remove:
            exc_team_first = exc_team_first.replace(word, "").replace("  ", " ")
            exc_team_second = exc_team_second.replace(word, "").replace("  ", " ")

            bm_team_first = bm_team_first.replace(word, "").replace("  ", " ")
            bm_team_second = bm_team_second.replace(word, "").replace("  ", " ")

        return exc_team_first, exc_team_second, bm_team_first, bm_team_second

    def make_matching(self) -> dict | None:
        best_match = None
        match self.exchange_data:
            case {
                'bet': str() as exc_bet,
                'match_name': str() as exc_match_name,
                'first_team': str() as exc_first_team,
                'second_team': str() as exc_second_team,
                **exc_other_fields
            }:
                self.logger.debug('Start matching for event %s' % exc_match_name)
                best_match = self._get_best_match(exc_bet, exc_first_team, exc_second_team)

                if best_match is not None:
                    self.logger.debug('Match for event %s is %s' % (' vs '.join([exc_first_team, exc_second_team]),
                                                                    best_match['bm_event_data']['match_name']))
        return best_match

    def _get_best_match(self, exc_bet, exc_first_team, exc_second_team) -> dict | None:
        best_match = None
        best_similarity = 0.0
        exc_is_draw = (exc_bet.lower() == 'draw')

        for bm_data in self.bm_events_df.replace({np.nan: None}).to_dict(orient='records'):
            match bm_data:
                case {
                    'first_team': str() as bm_first_team,
                    'second_team': str() as bm_second_team,
                    'bet': str() as bm_bet,
                    **bm_other_fields
                }:
                    bm_is_draw = (bm_bet.lower() == 'draw')
                    if exc_is_draw != bm_is_draw:
                        continue

                    # if (exc_is_draw is False and bm_is_draw is True) or (exc_is_draw is True and bm_is_draw is False):
                    #     continue

                    exc_first, exc_second, bm_first, bm_second = self._remove_words(
                        exc_team_first=exc_first_team,
                        exc_team_second=exc_second_team,
                        bm_team_first=bm_first_team,
                        bm_team_second=bm_second_team
                    )
                    similarity_by_first_teams = CSequenceMatcher(None, exc_first, bm_first).ratio()
                    if similarity_by_first_teams < self.teams_min_similarity:
                        continue

                    similarity_by_second_teams = CSequenceMatcher(None, exc_second, bm_second).ratio()
                    if similarity_by_second_teams < self.teams_min_similarity:
                        continue

                    similarity_score = similarity_by_first_teams + similarity_by_second_teams

                    if similarity_score >= self.total_min_similarity and similarity_score > best_similarity:
                        best_similarity = similarity_score
                        best_match = {
                            "similarity_by_first_teams": similarity_by_first_teams,
                            "similarity_by_second_teams": similarity_by_second_teams,
                            "bm_event_data": bm_data
                        }
        return best_match
