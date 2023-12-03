from dataclasses import dataclass
from enum import Enum
from typing import Any


class ValueInputOption(Enum):
    # docs: https://developers.google.com/sheets/api/reference/rest/v4/ValueInputOption

    INPUT_VALUE_OPTION_UNSPECIFIED = 'INPUT_VALUE_OPTION_UNSPECIFIED'
    RAW = 'RAW'
    USER_ENTERED = 'USER_ENTERED'


class ValueRenderOption(Enum):
    # docs: https://developers.google.com/sheets/api/reference/rest/v4/ValueRenderOption

    FORMATTED_VALUE = 'FORMATTED_VALUE'
    UNFORMATTED_VALUE = 'UNFORMATTED_VALUE'
    FORMULA = 'FORMULA'


class DateTimeRenderOption(Enum):
    # docs: https://developers.google.com/sheets/api/reference/rest/v4/DateTimeRenderOption

    SERIAL_NUMBER = 'SERIAL_NUMBER'
    FORMATTED_STRING = 'FORMATTED_STRING'


class Dimension(Enum):
    # docs: https://developers.google.com/sheets/api/reference/rest/v4/Dimension
    DIMENSION_UNSPECIFIED = 'DIMENSION_UNSPECIFIED'
    ROWS = 'ROWS'
    COLUMNS = 'COLUMNS'


@dataclass
class GSBody:
    # docs: https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets.values#ValueRange
    range: str
    values: list
    major_dimension: Dimension = None

    def __post_init__(self):
        assert ':' in self.range, 'Invalid range %s. See %s to using A1 notation' % (
            self.range, 'https://developers.google.com/sheets/api/guides/concepts#cell'
        )
        assert self.values


@dataclass
class UpdateBody:
    data: GSBody | dict
    includeValuesInResponse: bool = False
    valueInputOption: ValueInputOption = ValueInputOption.USER_ENTERED
    responseValueRenderOption: ValueRenderOption = ValueRenderOption.FORMATTED_VALUE
    responseDateTimeRenderOption: DateTimeRenderOption = DateTimeRenderOption.SERIAL_NUMBER

    _range: str = None

    def __post_init__(self):
        if isinstance(self.data, GSBody):
            data = {'range': self.data.range, 'values': self.data.values}

            if self.data.major_dimension:
                data['majorDimension'] = self.data.major_dimension.value

            self.data = data

        match self.data:
            case {'range': str(), 'values': list()} | {'range': str(), 'values': list(), 'majorDimension': str()}:
                pass
            case _:
                raise ValueError('Invalid data!')

    def dict(self) -> dict[str, Any]:
        return {
            'range': self.data.pop('range'),
            'body': self.data,
            'valueInputOption': self.valueInputOption.value,
            'includeValuesInResponse': self.includeValuesInResponse,
            'responseValueRenderOption': self.responseValueRenderOption.value,
            'responseDateTimeRenderOption': self.responseDateTimeRenderOption.value
        }


@dataclass
class BatchBody:
    data: list[dict[str, Any]]
    valueInputOption: ValueInputOption = ValueInputOption.USER_ENTERED
    includeValuesInResponse: bool = False
    responseValueRenderOption: ValueRenderOption = ValueRenderOption.FORMATTED_VALUE
    responseDateTimeRenderOption: DateTimeRenderOption = DateTimeRenderOption.SERIAL_NUMBER

    def dict(self) -> dict[str, Any]:
        return {
            'data': self.data,
            'valueInputOption': self.valueInputOption.value,
            'includeValuesInResponse': self.includeValuesInResponse,
            'responseValueRenderOption': self.responseValueRenderOption.value,
            'responseDateTimeRenderOption': self.responseDateTimeRenderOption.value
        }
