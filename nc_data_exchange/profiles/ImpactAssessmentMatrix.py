from pydantic import BaseModel, Field, field_serializer, field_validator
import uuid
from typing import Optional
from nc_data_exchange.config import Areas
from nc_data_exchange.profiles.Base import IdentifiedObject
from nc_data_exchange.profiles.Enumerations import OutcomeImpactAssessmentKind, ImpactAgreementKind

"""
For simple ImpactAssessmentMatrix instance creation workflow is as follows:
    RemedialActionImpact (QuantitativeRemedialActionImpact, QualitativeRemedialActionImpact) -> OwnerRemedialActionAssessment
    ImpactAssessmentMatrix (CalculationBasedImpactAssessmentMatrix, ConnectingImpactAssessmentMatrix, ListBasedImpactAssessmentMatrix)
        -> OutcomeValue (RemedialActionScheduleOutcomeValue, RemedialActionOutcomeValue)
        
    ImpactAssessmentMatrix and RemedialActionImpact connecting through RemedialAction
"""


class ImpactAssessmentMatrix(IdentifiedObject):
    pass


class CalculationBasedImpactAssessmentMatrix(ImpactAssessmentMatrix):
    pass


class ConnectingImpactAssessmentMatrix(ImpactAssessmentMatrix):
    pass


class ListBasedImpactAssessmentMatrix(ImpactAssessmentMatrix):
    pass


class OutcomeValue(BaseModel):
    # Class attributes
    mRID: str = Field(default_factory=lambda: f"{uuid.uuid4()}", max_length=36, min_length=36)
    outcome: OutcomeImpactAssessmentKind

    # References to objects inside profile
    ImpactAssessmentMatrix: object

    # References to reference data
    ImpactedSystemOperator: str

    @field_validator('outcome', mode='before')
    @classmethod
    def convert_outcome_to_str(cls, value):
        return str(value).lower()

    @field_serializer('ImpactedSystemOperator')
    def resource_eic_tso(self, value):
        return f"https://energy.referencedata.eu/EIC/{Areas().df.set_index('tso').loc[value].tso_eic}"


class RemedialActionScheduleOutcomeValue(OutcomeValue):
    # References to objects outside profile
    RemedialActionSchedule: str = Field(max_length=36, min_length=36)


class RemedialActionOutcomeValue(OutcomeValue):
    # Class attributes
    impactQuantity: Optional[float] = None

    # References to objects outside profile
    RemedialAction: str = Field(max_length=36, min_length=36)


class RemedialActionImpact(BaseModel):
    # Class attributes
    mRID: str = Field(default_factory=lambda: f"{uuid.uuid4()}", max_length=36, min_length=36)
    kind: ImpactAgreementKind = ImpactAgreementKind.always
    impactQuantity: Optional[float] = None

    # References to reference data
    AssessingSystemOperator: str

    # References to objects outside profile
    RemedialAction: str = Field(max_length=36, min_length=36)

    @field_serializer('AssessingSystemOperator')
    def resource_eic_tso(self, value):
        return f"https://energy.referencedata.eu/EIC/{Areas().df.set_index('tso').loc[value].tso_eic}"


class QuantitativeRemedialActionImpact(RemedialActionImpact):
    # References to reference data
    SensitivityArea: object


class QualitativeRemedialActionImpact(RemedialActionImpact):
    pass


class OwnerRemedialActionAssessment(BaseModel):
    # Class attributes
    mRID: str = Field(default_factory=lambda: f"{uuid.uuid4()}", max_length=36, min_length=36)

    # References to reference data
    ImpactedSystemOperator: str

    # References to objects inside profile
    RemedialActionImpact: object

    @field_serializer('ImpactedSystemOperator')
    def resource_eic_tso(self, value):
        return f"https://energy.referencedata.eu/EIC/{Areas().df.set_index('tso').loc[value].tso_eic}"


if __name__ == '__main__':
    # Test data
    matrix = CalculationBasedImpactAssessmentMatrix(
        name="IAM",
        description="Calculation based IAM"
    )

    ras_outcome = RemedialActionScheduleOutcomeValue(
        ImpactAssessmentMatrix=matrix,
        outcome=True,
        RemedialActionSchedule="6804e0ba-ba01-44ce-8a8c-84f6fba20c79",
        ImpactedSystemOperator="LITGRID",
    )

    from nc_data_exchange.profile_constructor import Profile

    # Building profile graph
    profile = Profile(profile_name='ImpactAssessmentMatrix')
    profile.add_document_header(startDate="2024-10-07T10:30:00Z", endDate="2024-10-07T11:30:00Z")
    profile.add_element(element=matrix)
    profile.add_element(element=ras_outcome)

    # Print/save test data profile
    print(profile.rdf_pretty_xml)
    # profile.export_graph(output_path=r"../../tests/samples/ex_ImpactAssessmentMatrix(test_data).xml")
    profile.get_profile_xml(
        output_path=r"../../tests/samples/ex_ImpactAssessmentMatrix(test_data).xml",
        fix_rdf_about=True,
        remove_rdf_datatype=True,
        save=True,
    )
