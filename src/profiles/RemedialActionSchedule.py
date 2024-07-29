from pydantic import BaseModel, Field, field_serializer
from typing import Optional
from nc_csa_profiles.profiles.Base import IdentifiedObject
from rcc_common_tools.configurations.areas import Areas
from nc_csa_profiles.profiles.Enumerations import RemedialActionScheduleStatusKind, TimeSeriesInterpolationKind

"""
For simple Remedial Action Schedule instance creation workflow is as follows:
    For GridStateAlterationRemedialAction's:
        RemedialActionSchedule -> GridStateIntensitySchedule -> GenericValueTimePoint
    For PowerRemedialAction's:
        RemedialActionSchedule -> PowerSchedule -> PowerScheduleAction (CountertradeScheduleAction, RedispatchScheduleAction) -> PowerTimePoint
"""


class RemedialActionSchedule(IdentifiedObject):
    # Class attributes
    statusKind: RemedialActionScheduleStatusKind = RemedialActionScheduleStatusKind.proposed
    statusReason: Optional[str] = None

    # References to reference data
    AssignedRegion: Optional[str] = None
    ProposingEntity: Optional[str] = "38X-BALTIC-RSC-H"

    # References to objects outside profile
    RemedialAction: str = Field(max_length=36, min_length=36)
    Contingency: Optional[str] = Field(max_length=36, min_length=36)

    @field_serializer('ProposingEntity', when_used='unless-none')
    def resource_eic(self, value):
        return f"https://energy.referencedata.eu/EIC/{value}"

    @field_serializer('AssignedRegion', when_used='unless-none')
    def resource_eic_region(self, value):
        return f"https://energy.referencedata.eu/EIC/{Areas().df.set_index('short_name').loc[value].area_eic}"


class BaseTimeSeries(IdentifiedObject):
    # Class attributes
    interpolationKind: TimeSeriesInterpolationKind = TimeSeriesInterpolationKind.next


class BaseIrregularTimeSeries(BaseTimeSeries):
    pass


class GenericValueSchedule(BaseIrregularTimeSeries):
    # References to objects inside profile
    RemedialActionSchedule: object


class GridStateIntensitySchedule(GenericValueSchedule):
    # References to objects outside profile
    GridStateAlteration: str = Field(max_length=36, min_length=36)


class PowerSchedule(BaseIrregularTimeSeries):
    pass


class PowerScheduleAction(IdentifiedObject):
    # Class attributes
    currency: Optional[str] = None
    energyPrice: Optional[float] = None

    # References to objects inside profile
    PowerSchedule: object
    RemedialActionSchedule: object


class CountertradeScheduleAction(PowerScheduleAction):
    pass


class RedispatchScheduleAction(PowerScheduleAction):
    pass


class GenericValueTimePoint(BaseModel):
    # References to objects inside profile
    GenericValueSchedule: object

    # Class attributes
    atTime: str  # ex 2022-06-16T12:30:00Z
    value: float


class PowerTimePoint(BaseModel):
    # References to objects inside profile
    PowerSchedule: object

    # Class attributes
    atTime: str  # ex 2022-06-16T12:30:00Z
    p: Optional[float] = None  # active power injection with load sign convention
    price: Optional[float] = None
    q: Optional[float] = None
    activatedP: Optional[float] = None
    activatedPrice: Optional[float] = None


if __name__ == '__main__':
    # Test data
    remedial_action_schedule = RemedialActionSchedule(
        name="Remedial Action Schedule instance",
        RemedialAction=f"7e258bc8-e18c-44a6-ad2d-da1dd4c6bf69",  # RA_LN360_OUT
        Contingency=f"70a66b7f-0051-4967-8bef-7521eba1fbd2",  # OCO_LN511
        AssignedRegion="EE"
    )

    grid_state_intensity_schedule = GridStateIntensitySchedule(
        name="Intensity schedule instance",
        RemedialActionSchedule=remedial_action_schedule,
        GridStateAlteration=f"e3f369d3-0b79-40ac-bb7d-23cce8dc6877"  # TopologyAction of RA_LN360_OUT
    )

    generic_value_time_point = GenericValueTimePoint(
        GenericValueSchedule=grid_state_intensity_schedule,
        atTime="2023-08-16T12:30:00Z",
        value=0.0
    )

    remedial_action_schedule_for_countertrade = RemedialActionSchedule(
        name="Remedial Action Schedule instance for countertrade",
        RemedialAction=f"87c806b5-fa24-4273-93bb-f86d9fb99a64",
        Contingency=f"70a66b7f-0051-4967-8bef-7521eba1fbd2",  # OCO_LN511
        AssignedRegion="BALTIC"
    )

    power_schedule = PowerSchedule(
        name="Power schedule instance",
    )

    power_schedule_action = CountertradeScheduleAction(
        name="Countertrade schedule action instance",
        PowerSchedule=power_schedule,
        RemedialActionSchedule=remedial_action_schedule_for_countertrade,
    )

    power_time_point = PowerTimePoint(
        PowerSchedule=power_schedule,
        atTime="2023-08-16T12:30:00Z",
        p=100,
    )

    from nc_csa_profiles.profile_constructor import Profile

    # Building profile graph
    profile = Profile(profile_name='RemedialActionSchedule')
    profile.add_document_header(start_date="2023-08-16T12:30:00Z", end_date="2023-08-16T12:30:00Z")

    profile.add_element(element=remedial_action_schedule)
    profile.add_element(element=grid_state_intensity_schedule)
    profile.add_element(element=generic_value_time_point)

    profile.add_element(element=remedial_action_schedule_for_countertrade)
    profile.add_element(element=power_schedule)
    profile.add_element(element=power_schedule_action)
    profile.add_element(element=power_time_point)

    # Print/save test data profile
    print(profile.rdf_pretty_xml)
    # profile.export_graph(output_path=r"../samples/ex_RemedialActionSchedule(test_data).xml")
    profile.get_profile_xml(
        output_path=r"../samples/ex_RemedialActionSchedule(test_data).xml",
        fix_rdf_about=True,
        remove_rdf_datatype=True,
        save=True,
    )
    # profile.export_to_excel(output_path=r"../samples/ex_RemedialActionSchedule(test_data).xlsx")
