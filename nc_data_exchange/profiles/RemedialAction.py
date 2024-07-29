from pydantic import Field, field_serializer
from typing import Optional
from nc_csa_profiles.profiles.Base import IdentifiedObject
from nc_csa_profiles.profiles.Enumerations import RemedialActionKind, ValueOffsetKind, RelativeDirectionKind
from rcc_common_tools.configurations.areas import Areas, Borders

"""
For simple Remedial Action instance creation workflow is as follows:
    RemedialAction (
        GridStateAlterationRemedialAction,
        PowerRemedialAction,
        SchemeRemedialAction,
        AvailabilityRemedialAction
    )
    -> GridStateAlteration (TopologyAction, RegulatingControlAction, TapPositionAction)
    -> RangeConstraint (StaticPropertyRange, IntertemporalPropertyRange)
"""


class RemedialAction(IdentifiedObject):
    # Class attributes
    isCrossBorderRelevant: bool = False
    kind: RemedialActionKind = RemedialActionKind.curative
    normalAvailable: bool = True
    impactThresholdMargin: Optional[float] = None
    isManual: Optional[bool] = None
    penaltyFactor: Optional[float] = None
    timeToImplement: Optional[str] = None  # ex. PT15M

    # References to reference data
    AppointedToRegion: str
    RemedialActionSystemOperator: Optional[str] = None

    @field_serializer('RemedialActionSystemOperator', when_used='unless-none')
    def resource_eic_tso(self, value):
        return f"https://energy.referencedata.eu/EIC/{Areas().df.set_index('tso').loc[value].tso_eic}"

    @field_serializer('AppointedToRegion')
    def resource_eic_region(self, value):
        return f"https://energy.referencedata.eu/EIC/{Areas().df.set_index('short_name').loc[value].area_eic}"


class GridStateAlterationRemedialAction(RemedialAction):
    pass


class PowerRemedialAction(RemedialAction):
    # References to reference data (or ER profile)
    BiddingZone: Optional[str] = None
    BiddingZoneBorder: Optional[str] = None

    @field_serializer('BiddingZone', when_used='unless-none')
    def resource_eic_area(self, value):
        return f"https://energy.referencedata.eu/EIC/{Areas().df.set_index('short_name').loc[value].area_eic}"

    @field_serializer('BiddingZoneBorder', when_used='unless-none')
    def resource_eic_border(self, value):
        return f"https://energy.referencedata.eu/EIC/{Borders().df.set_index('name').loc[value].eic}"


class AvailabilityRemedialAction(RemedialAction):
    pass


class CountertradeRemedialAction(PowerRemedialAction):
    # Class attributes
    maxEconomicPMargin: Optional[float] = None
    minEconomicPMargin: Optional[float] = None
    # gLSKStrategy: GLSKStrategyKind = GLSKStrategyKind.generatorPmax  # TODO deprecated in v2.3
    # shiftMethod: ShiftMethodKind = ShiftMethodKind.shared  # TODO deprecated in v2.3


class RedispatchRemedialAction(PowerRemedialAction):
    pass


class GridStateAlteration(IdentifiedObject):
    # Class attributes
    normalEnabled: bool = True
    maximumPerDay: Optional[int] = None
    minimumActivation: Optional[str] = None
    timePerStage: Optional[str] = None

    # References to objects inside profile
    GridStateAlterationRemedialAction: object

    # References to reference data
    PropertyReference: str  # class attributes which going to be changed

    @field_serializer('PropertyReference')
    def resource_property(self, value):
        return f"https://energy.referencedata.eu/PropertyReference/{value}"


class TopologyAction(GridStateAlteration):
    # References to objects outside profile
    Switch: Optional[str] = Field(default=None, max_length=36, min_length=36)  # TODO should be mandatory
    Equipment: Optional[str] = Field(default=None, max_length=36, min_length=36)  # profile specification refers to cim:Switch

    @field_serializer('Equipment', when_used='unless-none')  # TODO custom attribute serializer
    def resource_mrid(self, value):
        return f"#_{value}"


class SetPointAction(GridStateAlteration):
    pass


class ShuntCompensatorModification(SetPointAction):
    # References to objects outside profile
    ShuntCompensator: str = Field(max_length=36, min_length=36)


class RotatingMachineAction(SetPointAction):
    # References to objects outside profile
    RotatingMachine: str = Field(max_length=36, min_length=36)


class LoadAction(SetPointAction):
    # References to objects outside profile
    EnergyConsumer: str = Field(max_length=36, min_length=36)


class RegulatingControlAction(SetPointAction):
    # References to objects outside profile
    RegulatingControl: str = Field(max_length=36, min_length=36)


class TapPositionAction(SetPointAction):
    # References to objects outside profile
    TapChanger: str = Field(max_length=36, min_length=36)


class RangeConstraint(IdentifiedObject):
    # Class attributes
    normalValue: float  # initial (normal) value of attribute to be changed
    direction: RelativeDirectionKind = RelativeDirectionKind.none
    valueKind: ValueOffsetKind = ValueOffsetKind.absolute

    # References to objects inside profile
    GridStateAlteration: object


class StaticPropertyRange(RangeConstraint):
    # References to reference data
    PropertyReference: str

    @field_serializer('PropertyReference')
    def resource_property(self, value):
        return f"https://energy.referencedata.eu/PropertyReference/{value}"


if __name__ == '__main__':
    # Test data
    remedial_action_lt = GridStateAlterationRemedialAction(
        name="RA1",
        description="Example of Preventive RA: TopologyAction",
        AppointedToRegion="LT",
        RemedialActionSystemOperator="LITGRID",
        isCrossBorderRelevant=False,
        kind="preventive",
        timeToImplement='PT15M',
    )

    remedial_action_lv = GridStateAlterationRemedialAction(
        name="RA2",
        description="Example of Curative RA: TopologyAction",
        AppointedToRegion="LV",
        RemedialActionSystemOperator="AST",
        isCrossBorderRelevant=True,

    )

    countertrade_action = CountertradeRemedialAction(
        name="CT_LV-LT",
        description="Example of Countertrade RA for LT-LV border",
        AppointedToRegion="BALTIC",
        isCrossBorderRelevant=True,
        kind="curative",
        BiddingZoneBorder="LV-LT",
    )

    redispatch_action = RedispatchRemedialAction(
        name="REDISPATCH_LV",
        description="Example of redispatching RA for LV area",
        AppointedToRegion="BALTIC",
        isCrossBorderRelevant=True,
        kind="curative",
        BiddingZone="LV",
        RemedialActionSystemOperator="AST",
    )

    grid_state_alteration_lt = TopologyAction(
        Equipment=f"fa870de0-85a0-11e8-811a-00505691de36",
        GridStateAlterationRemedialAction=remedial_action_lt,
        description="Preventive RA: TopologyAction (LN366 in-service due to high voltages)",
        PropertyReference="ACDCTerminal.connected",
    )

    grid_state_alteration_lv = TopologyAction(
        Equipment=f"e88dfc25-ba01-4c20-8baf-fc95c45cc6f8",
        GridStateAlterationRemedialAction=remedial_action_lv,
        description="Curative RA: TopologyAction (LN311 disconnection)",
        PropertyReference="ACDCTerminal.connected",
    )

    static_property_range_lt = StaticPropertyRange(
        name="Static property range for RA1",
        normalValue=True,
        GridStateAlteration=grid_state_alteration_lt,
        PropertyReference="ACDCTerminal.connected",
    )

    static_property_range_lv = StaticPropertyRange(
        name="Static property range for RA2",
        normalValue=True,
        GridStateAlteration=grid_state_alteration_lv,
        PropertyReference="ACDCTerminal.connected",
    )

    from nc_csa_profiles.profile_constructor import Profile

    # Building profile graph
    profile = Profile(profile_name='RemedialAction')
    profile.add_document_header(start_date="2023-06-20T22:30:00Z", end_date="2023-06-21T21:30:00Z")
    profile.add_element(element=remedial_action_lt)
    profile.add_element(element=remedial_action_lv)
    profile.add_element(element=countertrade_action)
    profile.add_element(element=redispatch_action)
    profile.add_element(element=grid_state_alteration_lt)
    profile.add_element(element=grid_state_alteration_lv)
    profile.add_element(element=static_property_range_lt)
    profile.add_element(element=static_property_range_lv)

    # Print/save test data profile
    print(profile.rdf_pretty_xml)
    # profile.export_graph(output_path=r"../samples/ex_RemedialAction(test_data).xml")
    profile.get_profile_xml(
        output_path=r"../samples/ex_RemedialAction(test_data).xml",
        fix_rdf_about=True,
        remove_rdf_datatype=True,
        save=True,
    )
