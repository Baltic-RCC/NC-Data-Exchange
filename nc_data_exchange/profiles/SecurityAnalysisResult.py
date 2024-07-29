from pydantic import BaseModel, Field, field_serializer
from typing import Optional
from rcc_common_tools.configurations.areas import Areas


class PowerFlowResult(BaseModel):
    atTime: str
    isViolation: bool
    value: float
    absoluteValue: Optional[float] = None
    valueA: Optional[float] = None
    valueV: Optional[float] = None
    valueAngle: Optional[float] = None
    valueVA: Optional[float] = None
    valueVAR: Optional[float] = None
    valueW: Optional[float] = None
    ACDCTerminal: str = Field(max_length=36, min_length=36)
    OperationalLimit: Optional[float] = None  # by specification should be referred OperationalLimit class in EQ profile
    ReportedByRegion: Optional[str] = None

    # Custom local attributes which is not in profile specification
    EquipmentName: Optional[str] = None
    Substation: Optional[str] = None

    @field_serializer('ReportedByRegion', when_used='unless-none')
    def resource_eic_area(self, value):
        try:
            area_eic = Areas().df.set_index('short_name').loc[value].area_eic
        except KeyError:
            area_eic = "UNDEFINED"

        return f"https://energy.referencedata.eu/EIC/{area_eic}"


class ContingencyPowerFlowResult(PowerFlowResult):
    Contingency: str = Field(max_length=36, min_length=36)


class BaseCasePowerFlowResult(PowerFlowResult):
    pass


if __name__ == '__main__':
    # Test data
    cont_pf_result = ContingencyPowerFlowResult(
        atTime='2023-11-30T12:30:00Z',
        isViolation=True,
        value=115,
        valueA=1150,
        ACDCTerminal="6804e0ba-ba01-44ce-8a8c-84f6fba20c79",
        OperationalLimit=1000,
        ReportedByRegion="LT",
        EquipmentName='KHAE_T1',
        Substation='KHAE',
        Contingency="ef8a6b81-6235-445e-aaf1-c61685b16ffe",
    )

    bc_pf_result = BaseCasePowerFlowResult(
        atTime='2023-11-30T12:30:00Z',
        isViolation=False,
        value=98,
        valueA=980,
        ACDCTerminal="6804e0ba-ba01-44ce-8a8c-84f6fba20c79",
        OperationalLimit=1000,
        ReportedByRegion="LT",
        EquipmentName='KHAE_T1',
        Substation='KHAE',
    )

    from nc_csa_profiles.profile_constructor import Profile

    # Building profile graph
    profile = Profile(profile_name='SecurityAnalysisResult')
    profile.add_document_header(start_date="2023-11-30T12:30:00Z", end_date="2023-11-30T12:30:00Z")
    profile.add_element(element=cont_pf_result)
    profile.add_element(element=bc_pf_result)

    # Print/save test data profile
    print(profile.rdf_pretty_xml)
    # profile.export_graph(output_path=r"../samples/ex_SecurityAnalysisResult(test_data).xml")
    profile.get_profile_xml(
        output_path=r"../samples/ex_SecurityAnalysisResult(test_data).xml",
        fix_rdf_about=True,
        remove_rdf_datatype=True,
        save=True,
    )


