from logging import getLogger
from typing import Any

from google_api.connections import spreadsheets_service
from google_api.decorators import retry_with_backoff
from google_api.spreadsheets.types import BatchBody, UpdateBody, GSBody, Dimension


class SpreadSheetClient:
    _service = None

    def __init__(self, spreadsheet_id: str, api_version: str = 'v4'):
        self.logger = getLogger(self.__class__.__name__)
        self.spreadsheet_id = spreadsheet_id
        self.api_version = api_version
        self.__auth()

    def __auth(self) -> None:
        self._service = spreadsheets_service(self.api_version)

    def sheet_exists(self, sheet_name: str):
        sheet_metadata = self._service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
        sheets = sheet_metadata.get('sheets', [])
        if not sheets:
            return False
        return sheet_name in [sheet.get('properties', {}).get('title') for sheet in sheets]

    def create_sheet_if_not_exists(self, sheet_name: str):
        if not self.sheet_exists(sheet_name):
            self._service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body={'requests': [{'addSheet': {'properties': {'title': sheet_name}}}]}
            ).execute()

    def write_headers(self, sheet_name: str, values: list[str]):
        self.update_values(
            body=UpdateBody(
                data=GSBody(range=f'{sheet_name}!A1:Z1', major_dimension=Dimension.ROWS, values=[values])
            )
        )

    @retry_with_backoff
    def update_values(self, body: UpdateBody) -> dict[str, Any]:
        return self._service.spreadsheets().values().update(spreadsheetId=self.spreadsheet_id, **body.dict()).execute()

    @retry_with_backoff
    def batch_update_values(self, body: BatchBody) -> dict[str, Any]:
        return self._service.spreadsheets().values().batchUpdate(spreadsheetId=self.spreadsheet_id,
                                                                 body=body.dict()).execute()

    @retry_with_backoff
    def clear_sheet(self, sheet_name: str, col_ranges: str = 'A:Z') -> dict[str, Any]:
        assert ':' in col_ranges

        clear_range = f'{sheet_name}!{col_ranges.upper()}'
        self.logger.warning("Be careful, you've run a table range cleanup: " + clear_range)
        return self._service.spreadsheets().values().batchClear(spreadsheetId=self.spreadsheet_id,
                                                                body={'ranges': [clear_range]}).execute()

    @retry_with_backoff
    def get_sheet_data(self, sheet_name: str, col_ranges: str = 'A:Z',
                       major_dimension: Dimension = Dimension.DIMENSION_UNSPECIFIED) -> list[dict[str, Any]]:
        assert ':' in col_ranges

        result = self._service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range=f'{sheet_name}!{col_ranges.upper()}',
            majorDimension=major_dimension.value
        ).execute()
        return result.get('values')

    @retry_with_backoff
    def get_sheet_meta(self, sheet_name: str) -> dict:
        result = self._service.spreadsheets().get(spreadsheetId=self.spreadsheet_id, ranges=[sheet_name]).execute()
        sheets_meta = result.get('sheets')
        if not sheets_meta:
            raise ValueError('Invalid sheet_name %s' % sheet_name)
        return sheets_meta[0]['properties']

    @retry_with_backoff
    def add_new_rows(self, sheet_name: str, rows_num: int = 1000):
        sheet_id = self.get_sheet_meta(sheet_name)['sheetId']
        self._service.spreadsheets().batchUpdate(
            spreadsheetId=self.spreadsheet_id,
            body={'requests': [
                {
                    "appendDimension": {
                        "sheetId": sheet_id, "dimension": "ROWS", "length": rows_num
                    }
                }
            ]}
        ).execute()


if __name__ == '__main__':
    from config import SPREADSHEET_ID

    client = SpreadSheetClient(SPREADSHEET_ID)
    x = client.get_sheet_meta('Sheet13')
    print(x)

