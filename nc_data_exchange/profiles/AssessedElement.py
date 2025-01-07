from pydantic import Field, field_serializer, BaseModel
from typing import Optional
from nc_data_exchange.profiles.Base import IdentifiedObject
from nc_data_exchange.config import Areas
from nc_data_exchange.profiles.Enumerations import ElementCombinationConstraintKind

"""
For simple AssessedElement instance creation workflow is as follows:
    AssessedElement
"""


class AssessedElement(IdentifiedObject):
    # Class attributes
    inBaseCase: bool
    isCrossBorderRelevant: Optional[bool] = None
    normalEnabled: Optional[bool] = None

    # References to reference data
    AssessedSystemOperator: str
    ScannedForRegion: Optional[str] = None
    SecuredForRegion: Optional[str] = None
    NativeRegion: Optional[str] = None

    # References to objects outside profile
    ConductingEquipment: Optional[str] = Field(default=None, max_length=36, min_length=36)
    OperationalLimit: Optional[str] = Field(default=None, max_length=36, min_length=36)

    @field_serializer('AssessedSystemOperator')
    def resource_eic_tso(self, value):
        return f"https://energy.referencedata.eu/EIC/{Areas().df.set_index('tso').loc[value].tso_eic}"

    @field_serializer('ScannedForRegion', 'SecuredForRegion', 'NativeRegion', when_used='unless-none')
    def resource_eic_area(self, value):
        return f"https://energy.referencedata.eu/EIC/{Areas().df.set_index('short_name').loc[value].area_eic}"


class AssessedElementWithContingency(BaseModel):
    # Class attributes
    combinationConstraintKind: ElementCombinationConstraintKind = ElementCombinationConstraintKind.included
    mRID: str = Field(max_length=36, min_length=36)
    normalEnabled: Optional[bool] = True

    # References to objects inside profile
    AssessedElement: str = Field(max_length=36, min_length=36)

    # References to objects outside profile
    Contingency: str = Field(max_length=36, min_length=36)


class AssessedElementWithRemedialAction(BaseModel):
    # Class attributes
    combinationConstraintKind: ElementCombinationConstraintKind = ElementCombinationConstraintKind.included
    mRID: str = Field(max_length=36, min_length=36)
    normalEnabled: Optional[bool] = True

    # References to objects inside profile
    AssessedElement: str = Field(max_length=36, min_length=36)

    # References to objects outside profile
    RemedialAction: str = Field(max_length=36, min_length=36)


if __name__ == '__main__':
    # Test data
    assessed_element = AssessedElement(
        name="Assessed element example of LN332",
        inBaseCase=True,
        isCrossBorderRelevant=True,
        SecuredForRegion="LT",
        AssessedSystemOperator="LITGRID",
        ConductingEquipment="336d98e6-79fe-11e6-a326-d89d67d10dc7",
    )

    from nc_data_exchange.profile_constructor import Profile

    # Building profile graph
    profile = Profile(profile_name='AssessedElement')
    profile.add_document_header(startDate="2023-06-20T22:30:00Z", endDate="2023-06-21T21:30:00Z")
    profile.add_element(element=assessed_element)

    # Print/save test data profile
    print(profile.rdf_pretty_xml)
    # profile.export_graph(output_path=r"../tests/samples/ex_AssessedElement(test_data).xml")
    profile.get_profile_xml(
        output_path=r"../../tests/samples/ex_AssessedElement(test_data).xml",
        fix_rdf_about=True,
        remove_rdf_datatype=True,
        save=True,
    )
