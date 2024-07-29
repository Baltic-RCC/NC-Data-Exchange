from pydantic import Field, field_serializer, BaseModel
from typing import Optional
from nc_csa_profiles.profiles.Base import IdentifiedObject
from nc_csa_profiles.profiles.Enumerations import AvailabilityScheduleCauseKind, AvailabilityFunctionKind, TimeSeriesInterpolationKind
from rcc_common_tools.configurations.areas import Areas
from datetime import datetime


class AvailabilitySchedule(IdentifiedObject):
    # Class attributes
    causeKind: AvailabilityScheduleCauseKind = AvailabilityScheduleCauseKind.maintenance
    priority: int
    cancelledDateTime: Optional[str | datetime]
    causeDescription: Optional[str]
    daytimeRestitutionDuration: Optional[str]
    eveningRestitutionDuration: Optional[str]
    maxRestitutionDuration: Optional[str]
    weekendRestitutionDuration: Optional[str]


class AvailabilityPowerSystemFunction(IdentifiedObject):
    # Class attributes
    kind: AvailabilityFunctionKind = AvailabilityFunctionKind.outOfService

    # References to objects inside profile
    AvailabilitySchedule: object


class BaseTimeSeries(IdentifiedObject):
    # Class attributes
    interpolationKind: TimeSeriesInterpolationKind = TimeSeriesInterpolationKind.previous
    kind


class BaseIrregularTimeSeries(BaseTimeSeries):
    pass


class EventSchedule(BaseIrregularTimeSeries):
    pass


class EvenTimePoint(BaseModel):
    # References to objects inside profile
    EventSchedule: object

    # Class attributes
    atTime: Optional[str | datetime]
    isActive: Optional[bool]


if __name__ == '__main__':
    # Test data
    pass