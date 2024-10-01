from pydantic import Field, field_serializer
from typing import Optional
from nc_data_exchange.profiles.Base import IdentifiedObject
from nc_data_exchange.profiles.Enumerations import ContingencyEquipmentStatusKind, ContingencyConditionKind
from nc_data_exchange.config import Areas

"""
For simple Contingency instance creation workflow is as follows:
    Contingency (Ordinary, Exceptional, OutOfRange) -> ContingencyEquipment
"""


class Contingency(IdentifiedObject):
    # Class attributes
    normalMustStudy: bool = True
    normalProbability: Optional[float] = None

    # References to reference data
    EquipmentOperator: Optional[str] = None

    @field_serializer('EquipmentOperator', when_used='unless-none')
    def resource_eic_tso(self, value):
        return f"https://energy.referencedata.eu/EIC/{Areas().df.set_index('tso').loc[value].tso_eic}"


class OrdinaryContingency(Contingency):
    pass


class ExceptionalContingency(Contingency):
    # Class attributes
    kind: ContingencyConditionKind = ContingencyConditionKind.geographicalLocation


class OutOfRangeContingency(Contingency):
    pass


class ContingencyElement(IdentifiedObject):
    # References to objects inside profile
    Contingency: object


class ContingencyEquipment(ContingencyElement):
    # Class attributes
    contingentStatus: ContingencyEquipmentStatusKind = ContingencyEquipmentStatusKind.outOfService

    # References to objects outside profile
    Equipment: str = Field(max_length=36, min_length=36)


if __name__ == '__main__':
    # Test data
    contingency_lt = OrdinaryContingency(
        name="CO1",
        description="OrdinaryContingency instance example",
        EquipmentOperator="LITGRID",
    )
    contingency_lv = OrdinaryContingency(
        name="CO2",
        description="OrdinaryContingency instance example",
        EquipmentOperator="AST",
    )

    contingency_eq_lt = ContingencyEquipment(
        name="VILNIUS-T1",
        description="Contingency equipment instance of autotransformer",
        Contingency=contingency_lt,
        Equipment="33e7139f-79fe-11e6-a326-d89d67d10dc7",
    )

    contingency_eq_lv = ContingencyEquipment(
        name="LN320",
        description="Contingency equipment instance of line",
        Contingency=contingency_lv,
        Equipment="c6c80dfb-ba01-4ba2-a429-994a35d4a1fc",
    )

    exceptional_contingency = ExceptionalContingency(
        name="EXCO1",
        description="ExceptionalContingency instance example of 300.358",
        EquipmentOperator="ELERING",
    )

    exceptional_contingency_eq_one = ContingencyEquipment(
        name="LN300",
        description="Contingency equipment instance of line 300",
        Contingency=exceptional_contingency,
        Equipment="43a66e1d-deba-430c-95ff-eefaff6843cd",
    )

    exceptional_contingency_eq_two = ContingencyEquipment(
        name="LN358",
        description="Contingency equipment instance of line 358",
        Contingency=exceptional_contingency,
        Equipment="44588688-1954-4fdc-a04b-7aa7ec9c86b1",
    )

    from nc_data_exchange.profile_constructor import Profile

    # Building profile graph
    profile = Profile(profile_name='Contingency')
    profile.add_document_header(startDate="2023-06-20T22:30:00Z", endDate="2023-06-21T21:30:00Z")
    profile.add_element(element=contingency_lt)
    profile.add_element(element=contingency_eq_lt)
    profile.add_element(element=contingency_lv)
    profile.add_element(element=contingency_eq_lv)
    profile.add_element(element=exceptional_contingency)
    profile.add_element(element=exceptional_contingency_eq_one)
    profile.add_element(element=exceptional_contingency_eq_two)

    # Print/save test data profile
    print(profile.rdf_pretty_xml)
    # profile.export_graph(output_path=r"../tests/samples/ex_Contingency(test_data).xml")
    profile.get_profile_xml(
        output_path=r"../../tests/samples/ex_Contingency(test_data).xml",
        fix_rdf_about=True,
        remove_rdf_datatype=True,
        save=True,
    )
    # profile.export_to_excel(output_path=r"../tests/samples/ex_Contingency(test_data).xlsx")

    # Run SHACL validation
    shacl_simple = r"C:\Users\martynas.karobcikas\Downloads\Contingency-AP-Con-Simple-SHACL_v2-3-0.ttl"
    shacl_complex = r"C:\Users\martynas.karobcikas\Downloads\Contingency-AP-Con-Complex-SHACL_v2-3-0.ttl"
    # conforms, validation_report, results_text = profile.validate(shacl_path=shacl_simple)
    # conforms, validation_report, results_text = profile.validate(shacl_path=shacl_complex)