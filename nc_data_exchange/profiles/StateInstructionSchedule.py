from pydantic import Field, field_serializer
from typing import Optional
from nc_data_exchange.profiles.Base import IdentifiedObject
from nc_data_exchange.profiles.Enumerations import TimeSeriesInterpolationKind
from datetime import datetime

"""
For simple Assessed Element Schedule instance creation workflow is as follows:
    AssessedElementSchedule -> AssessedElementTimePoint
    ContingencySchedule -> ContingencyTimePoint
    GridStateAlterationSchedule -> GridStateAlterationTimePoint
"""


class BaseTimeSeries(IdentifiedObject):
    # Class attributes
    interpolationKind: TimeSeriesInterpolationKind = TimeSeriesInterpolationKind.none


class BaseIrregularTimeSeries(BaseTimeSeries):
    pass


class AssessedElementSchedule(BaseIrregularTimeSeries):
    # References to objects outside profile
    AssessedElement: str = Field(max_length=36, min_length=36)


class AssessedElementTimePoint(IdentifiedObject):
    # Class attributes
    atTime: str | datetime
    enabled: Optional[bool] = None

    # References to objects inside profile
    AssessedElementSchedule: object


class ContingencySchedule(BaseIrregularTimeSeries):
    # References to objects outside profile
    Contingency: str = Field(max_length=36, min_length=36)


class ContingencyTimePoint(IdentifiedObject):
    # Class attributes
    atTime: str | datetime
    mustStudy: Optional[bool] = None
    probability: Optional[float] = None

    # References to objects inside profile
    ContingencySchedule: object


class GridStateAlterationSchedule(BaseIrregularTimeSeries):
    # References to objects outside profile
    GridStateAlteration: str = Field(max_length=36, min_length=36)


class GridStateAlterationTimePoint(IdentifiedObject):
    # References to objects inside profile
    GridStateAlterationSchedule: object

    # Class attributes
    atTime: str | datetime
    enabled: Optional[bool] = None
    participationFactor: Optional[float] = None


if __name__ == '__main__':
    import pandas as pd
    # Test data
    START_TIME = "2024-05-28T05:30:00Z"
    END_TIME = "2024-05-28T08:30:00Z"
    time_range = pd.date_range(start=START_TIME, end=END_TIME, freq="h")
    time_range_str = time_range.map(lambda x: f"{x:%Y-%m-%dT%H:%M:%SZ}")

    assessed_element_schedule = AssessedElementSchedule(
        name="Schedule of assessed element LN332",
        AssessedElement="336d98e6-79fe-11e6-a326-d89d67d10dc7",
    )

    from nc_data_exchange.profile_constructor import Profile

    # Building profile graph
    profile = Profile(profile_name='StateInstructionSchedule')
    profile.add_document_header(start_date=START_TIME, end_date=END_TIME)
    profile.add_element(element=assessed_element_schedule)
    # creating time points
    for timestamp in time_range_str:
        assessed_element_time_point = AssessedElementTimePoint(
            AssessedElementSchedule=assessed_element_schedule,
            atTime=timestamp,
            enabled=True
        )
        profile.add_element(element=assessed_element_time_point)

    # Print/save test data profile
    print(profile.rdf_pretty_xml)
    # profile.export_graph(output_path=r"../tests/samples/ex_StateInstructionSchedule(test_data).xml")
    profile.get_profile_xml(
        output_path=r"../tests/samples/ex_StateInstructionSchedule(test_data).xml",
        fix_rdf_about=True,
        remove_rdf_datatype=True,
        save=True,
    )
