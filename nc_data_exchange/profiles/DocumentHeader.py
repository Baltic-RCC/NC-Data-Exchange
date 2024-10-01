import uuid
from datetime import datetime
from pydantic import BaseModel, Field, field_serializer
from typing import Optional, List
from nc_data_exchange.profiles.Enumerations import ProfileKeywords

"""
Version 2.3.1

Header serialisation:
IEC 61970-552 defines following notation - {Class}.{Property}

New properties under namespaces dcat, dcterms and prov serialized without {Class} part

Attribute notes:
    conformsTo: for CGM process this should clarify what to use for validation
    spatial: should be included in all Boundary profiles (rdf:resource to reference data)
"""


class Model(BaseModel):
    profile_name: ProfileKeywords = Field(exclude=True)

    # ns:dcterms
    identifier: uuid.UUID = Field(default_factory=lambda: uuid.uuid4())
    description: Optional[str] = None
    title: Optional[str] = None
    conformsTo: Optional[str] = None  # possible not to be defined for Boundary profile
    publisher: Optional[str] = None
    accessRights: Optional[str] = "Confidential"
    spatial: Optional[str] = None
    references: Optional[List[str]] = None

    # ns:eumd
    applicationSoftware: Optional[str] = "BALTIC RCC CUSTOM"

    # ns:prov
    wasGeneratedBy: Optional[str] = None  # {PROCESS}-{TIMEFRAME}-{RUN}-{PROFILE_KEYWORD} ex. "CSA-1D-08-SAR"

    # ns:md
    scenarioTime: Optional[str] = None
    created: str = Field(default_factory=lambda: f"{datetime.utcnow().replace(microsecond=0).isoformat()}Z")

    # ns:dcat
    version: str = Field(default="1", max_length=3)
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    keyword: Optional[str] = None

    # ns:euvoc

    # ns:adms

    @field_serializer('identifier')
    def urn(self, value):
        return value.urn

    @field_serializer('wasGeneratedBy', when_used='unless-none')
    def resource(self, value):
        return f"https://energy.referencedata.eu/{value}"

    @field_serializer('publisher', when_used='unless-none')
    def resource_eic(self, value):
        return f"https://energy.referencedata.eu/EIC/{value}"

    @field_serializer('accessRights', when_used='unless-none')
    def resource_confidentiality(self, value):
        return f"https://energy.referencedata.eu/Confidentiality/{value}"

    def model_post_init(self, __context) -> None:

        if self.description is None:
            self.description = f"Instance of {self.profile_name.value} profile"

        if self.title is None:
            # self.title = f"{datetime.fromisoformat(self.startDate).date():%Y%m%d}_{self.publisher}_{getattr(self, 'wasGeneratedBy')}"  # TODO proposed by specification
            self.title = f"{self.created}_{self.profile_name.name}_{str(uuid.uuid4()).split('-')[0]}"

        if self.conformsTo is None:
            self.conformsTo = f"https://ap.cim4.eu/{self.profile_name.value}/2.3"

        if self.keyword is None:
            self.keyword = f"{self.profile_name.name}"


class FullModel(Model):
    pass


if __name__ == '__main__':
    from nc_data_exchange.profile_constructor import Profile

    # Test data
    header = FullModel(profile_name="RemedialAction",
                       scenarioTime="2023-04-14T09:30Z",
                       version="1",
                       startDate="2023-06-20T22:00:00Z",
                       endDate="2023-06-21T21:00:00Z",
                       references=[f"{uuid.uuid4().urn}", f"{uuid.uuid4().urn}"]
                       )

    profile = Profile(profile_name='RemedialAction')
    rdfs = profile.load_rdfs(profile_name='DocumentHeader')
    profile.add_element(element=header, rdfs=rdfs)
    print(profile.rdf_pretty_xml)

    # Building profile graph
    profile = Profile(profile_name='RemedialAction')
    profile.add_document_header(
        scenario_time="2023-04-14T09:30Z",
        start_date="2023-06-20T22:00:00Z",
        end_date="2023-06-21T21:00:00Z",
        version="1",
        publisher="38X-BALTIC-RSC-H",
    )

    # Print/save test data profile
    print(profile.rdf_pretty_xml)
    # profile.export_graph(output_path=r"../tests/samples/ex_DocumentHeader(test_data).xml")
    profile.get_profile_xml(
        output_path=r"../../tests/samples/ex_DocumentHeader(test_data).xml",
        fix_rdf_about=True,
        remove_rdf_datatype=True,
        save=True,
    )
