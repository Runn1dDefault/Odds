from logging import Logger, Formatter, StreamHandler
from typing import Any, OrderedDict, Iterable, Callable

from config import SPREADSHEET_ID, LOG_FORMAT
from google_api.spreadsheets.client import SpreadSheetClient
from google_api.spreadsheets.types import BatchBody, Dimension
from managers.types import TableField


class SpreadSheetWriter:
    def __init__(self, fields: OrderedDict[str, TableField]):
        """
        headers {field on table: key in data} ex: {'Match Name': 'match_name'}
        """
        self.fields = fields
        self.gsp_client = SpreadSheetClient(spreadsheet_id=SPREADSHEET_ID)

        self.logger = Logger(self.__class__.__name__)
        log_format = Formatter(LOG_FORMAT)
        console = StreamHandler()
        console.setFormatter(log_format)
        self.logger.addHandler(console)

    def write_headers(self, sheet_name: str, headers: Iterable[str] = None) -> None:
        self.logger.info('Writing headers...')
        self.gsp_client.write_headers(sheet_name=sheet_name,
                                      values=list(self.fields.keys()) if not headers else headers)

    def rewrite_to_sheet(self, sheet_name: str, data: list[dict[str, Any]]) -> None:
        self.logger.info('Checking sheet %s...' % sheet_name)
        self.gsp_client.create_sheet_if_not_exists(sheet_name)
        self.logger.info('Clearing sheet %s...' % sheet_name)
        self.gsp_client.clear_sheet(sheet_name=sheet_name)
        self.write_headers(sheet_name)
        self.write_to_sheet(sheet_name, data)

    def write_to_sheet(self, sheet_name: str, data: list[dict | OrderedDict], check_fields: bool = True,
                       a1_range: str = 'A2:Z') -> None:
        self.logger.info('Write data to sheet %s...' % sheet_name)
        result = self.gsp_client.batch_update_values(
            body=BatchBody(
                data=[
                    dict(
                        major_dimension=Dimension.ROWS.value,
                        range=f'{sheet_name}!{a1_range}',
                        values=self.convert_data_to_rows(data, check_fields)
                    )
                ],
            )
        )
        self.logger.debug(f"{result.get('totalUpdatedRows')} rows updated.")
        self.logger.info('Over write data to sheet %s' % sheet_name)

    def convert_data_to_rows(self, data: list[dict | OrderedDict], check_fields: bool = True) -> list[list[str]]:
        if check_fields:
            collected_rows = []

            for row_data in data:
                row = []

                for _, field in self.fields.items():
                    value = row_data.get(field.key)

                    if value and isinstance(field.validator, Callable):
                        value = field.validator(value)

                    if not value:
                        value = field.default_value

                    row.append(value)
                collected_rows.append(row)

            return collected_rows
        return [list(row.values()) for row in data]
