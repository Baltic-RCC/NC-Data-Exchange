import logging
from datetime import datetime
import pytz
import pandas as pd
import numpy as np
from nc_data_exchange.profiles import AssessedElement, Contingency, RemedialAction
from nc_data_exchange.profile_constructor import Profile

# Start logger
logger = logging.getLogger(__name__)


class InputStructuralDataProfile:

    def __init__(self,
                 # if timezone is not defined in datetime object, then UTC is needed (in case of string - isoformat)
                 start_time: datetime | str,
                 end_time: datetime | str,
                 publisher: str,  # party EIC code
                 version: str | int = "1",
                 ):

        # Converting datetime/str arguments to UTC time
        if isinstance(start_time, str) and isinstance(end_time, str):
            self.start_time = datetime.fromisoformat(start_time)
            self.end_time = datetime.fromisoformat(end_time)
        else:
            self.start_time = start_time.astimezone(pytz.utc)
            self.end_time = end_time.astimezone(pytz.utc)
        self.publisher = publisher
        self.version = version

        logger.info(f"Initiating common input profile for: {start_time}/{end_time} [{start_time.tzinfo.zone}]")

    def load_static_dataset(self, path: str):
        # Reading dataset from static file
        logger.info(f"Loading static input data from: {path}")
        df = pd.read_excel(path)

        # Filtering dataset according start and end times
        df['start_time'] = pd.to_datetime(df['start_time']).dt.tz_localize('CET').dt.tz_convert('UTC')
        df['end_time'] = pd.to_datetime(df['end_time']).dt.tz_localize('CET').dt.tz_convert('UTC')
        mask = (df.start_time <= self.start_time) & (df.end_time >= self.end_time)
        df = df[mask]

        return df

    def generate_contingency_elements_profile(self, elements: pd.DataFrame | str):
        """
        Method to generate Contingency profile from dataframe object or path of Excel file
        :param elements: Dataframe or string path to Excel file
        :return: xml object
        """
        # Check if contingency elements data provided as dataframe or file path
        if isinstance(elements, str):
            df = self.load_static_dataset(path=elements)
        else:
            df = elements

        # Replacing np.nan to None
        df = df.replace({np.nan: None})

        # Remove contingencies where equipment mrid is missing
        df = df.dropna(subset='grid_element_id')

        # Removing leading underscores from mrids
        columns_to_modify = ['registered_resource', 'grid_element_id', 'coeq_mrid']
        df[columns_to_modify] = df[columns_to_modify].apply(lambda x: x.str.replace("_", ""))

        # Initiating constructor of Contingency profile
        profile = Profile(profile_name='Contingency')
        profile.add_document_header(startDate=self.start_time,
                                    endDate=self.end_time,
                                    publisher=self.publisher,
                                    version=str(self.version),
                                    )

        for index, data in df.groupby('registered_resource'):

            # Define Contingency type
            if data.type.unique().item() == "Exceptional":
                ReferencedContingencyType = Contingency.ExceptionalContingency
            elif data.type.unique().item() == "Ordinary":
                ReferencedContingencyType = Contingency.OrdinaryContingency
            elif data.type.unique().item() == "OutOfRange":
                ReferencedContingencyType = Contingency.OutOfRangeContingency
            else:
                raise Exception(f"Contingency type {data.type.unique().item()} unsupported")

            # Creating instances of exceptional/ordinary contingencies
            co = ReferencedContingencyType(
                mRID=data.registered_resource.unique().item(),
                name=data.co_name.unique().item(),
                description=data.co_description.unique().item(),
                normalMustStudy=data.normal_must_study.unique().item(),
                # TODO figure out how to fix it that Ordinary contingency has two different SystemOperators
                EquipmentOperator=data.operator.unique().item() if len(data.operator.unique()) <= 1 else data.operator.unique()[0],
                kind=data.condition_kind.unique().item(),
            )
            # Adding objects to profile graph
            profile.add_element(element=co)

            # Creating instances of contingency equipment
            for _, rowdata in data.iterrows():
                coeq = Contingency.ContingencyEquipment(
                    mRID=rowdata.coeq_mrid,
                    name=rowdata.coeq_name,
                    description=rowdata.coeq_description,
                    Contingency=co,
                    Equipment=rowdata.grid_element_id,
                )
                # Add consistency check status if attribute exists in given dataset
                consistency_status = rowdata.get('consistency_status', None)
                if consistency_status:
                    coeq.ConsistencyStatus = consistency_status

                # Adding objects to profile graph
                profile.add_element(element=coeq)

        # Serialize to rdfxml string in bytes object
        rdfxml = profile.get_profile_xml(
            fix_rdf_about=True,
            remove_rdf_datatype=True,
        )

        return rdfxml

    def generate_assessed_elements_profile(self, elements: pd.DataFrame | str):
        """
        Method to generate AssessdElement profile from dataframe object or path of Excel file
        :param elements: Dataframe or string path to Excel file
        :return: xml object
        """
        # Check if assessed elements data provided as dataframe or file path
        if isinstance(elements, str):
            df = self.load_static_dataset(path=elements)
        else:
            df = elements

        # Replacing np.nan to None
        df = df.replace({np.nan: None})

        # Remove assessed elements where equipment mrid is missing
        df = df.dropna(subset='grid_element_id')

        # Removing leading underscores from mrids
        columns_to_modify = ['registered_resource', 'grid_element_id']
        df[columns_to_modify] = df[columns_to_modify].apply(lambda x: x.str.replace("_", ""))

        # Initiating constructor of AssessedElement profile
        profile = Profile(profile_name='AssessedElement')
        profile.add_document_header(startDate=self.start_time,
                                    endDate=self.end_time,
                                    publisher=self.publisher,
                                    version=str(self.version),
                                    )

        for index, data in df.iterrows():
            # Creating AssessedElement instances
            ae = AssessedElement.AssessedElement(
                mRID=data.registered_resource,
                name=data['name'],
                description=data.get('description', None),
                inBaseCase=data.base_case,
                isCrossBorderRelevant=data.cross_border_relevant,
                normalEnabled=data.normal_enabled,
                SecuredForRegion=data.get('secured_for_region', None),
                ScannedForRegion=data.get('scanned_for_region', None),
                AssessedSystemOperator=data.operator,
                ConductingEquipment=data.grid_element_id,
            )
            # Add consistency check status if attribute exists in given dataset
            consistency_status = data.get('consistency_status', None)
            if consistency_status:
                ae.ConsistencyStatus = consistency_status

            # Adding objects to profile graph
            profile.add_element(element=ae)

        # Serialize to rdfxml string in bytes object
        rdfxml = profile.get_profile_xml(
            fix_rdf_about=True,
            remove_rdf_datatype=True,
        )

        return rdfxml

    def generate_remedial_actions_profile(self, elements: pd.DataFrame | str):
        """
        Method to generate RemedialAction profile from dataframe object or path of Excel file
        :param elements: Dataframe or string path to Excel file
        :return: xml object
        """
        # Check if remedial actions data provided as dataframe or file path
        if isinstance(elements, str):
            df = self.load_static_dataset(path=elements)
        else:
            df = elements

        # Replacing np.nan to None
        df = df.replace({np.nan: None})

        # Removing leading underscores from mrids
        columns_to_modify = ['registered_resource', 'alt_mrid', 'equipment', 'rc_mrid']
        df[columns_to_modify] = df[columns_to_modify].apply(lambda x: x.str.replace("_", ""))

        # Initiating constructor of RemedialAction profile
        profile = Profile(profile_name='RemedialAction')
        profile.add_document_header(startDate=self.start_time,
                                    endDate=self.end_time,
                                    publisher=self.publisher,
                                    version=str(self.version),
                                    )

        for index, data in df.iterrows():

            # Define Remedial action type
            ReferencedRemedialAction = getattr(RemedialAction, data.type)

            # Creating general Remedial action class instance
            ra = ReferencedRemedialAction(
                mRID=data.registered_resource,
                name=data.ra_name,
                AppointedToRegion=data.region,
                RemedialActionSystemOperator=data.operator,
                isCrossBorderRelevant=data.cross_border_relevant,
                kind=data.kind,
                normalAvailable=data.normal_available,
                BiddingZoneBorder=data.get('bidding_zone_border', None),
                BiddingZone=data.get('bidding_zone', None),
            )
            profile.add_element(element=ra)

            # Creating Remedial action alteration class instances
            if data.alt_mrid:

                # Define Remedial action alteration type
                ReferencedAlteration = getattr(RemedialAction, data.alt_type)

                # Creating Remedial action alteration class instances
                # Depending on alteration type it has different attributes, so all available are given
                alteration = ReferencedAlteration(
                    mRID=data.alt_mrid,
                    name=data.alt_name,
                    GridStateAlterationRemedialAction=ra,
                    PropertyReference=data.property,
                    normalEnabled=data.normal_enabled,
                    Equipment=data.equipment,
                    Switch=data.equipment,
                    ShuntCompensator=data.equipment,
                    RotatingMachine=data.equipment,
                    EnergyConsumer=data.equipment,
                    RegulatingControl=data.equipment,
                    TapChanger=data.equipment,
                )
                # Add consistency check status if attribute exists in given dataset
                consistency_status = data.get('consistency_status', None)
                if consistency_status:
                    alteration.ConsistencyStatus = consistency_status

                profile.add_element(element=alteration)

            else:
                logger.info(f"Alteration not defined for remedial action: {data.ra_name}")
                continue

            # Creating StaticPropertyRange class instances
            if data.rc_mrid:
                property_range = RemedialAction.StaticPropertyRange(
                    mRID=data.rc_mrid,
                    normalValue=data.normal_value,
                    direction=data.direction,
                    valueKind=data.value_kind,
                    GridStateAlteration=alteration,
                    PropertyReference=data.property
                )
                profile.add_element(element=property_range)
            else:
                logger.info(f"Range constraint not defined for alteration: {data.alt_name}")

        # Serialize to rdfxml string in bytes object
        rdfxml = profile.get_profile_xml(
            fix_rdf_about=True,
            remove_rdf_datatype=True,
        )

        return rdfxml


if __name__ == '__main__':
    # Testing
    START_TIME = pytz.timezone('CET').localize(datetime(2024, 10, 1, 0, 0))
    END_TIME = pytz.timezone('CET').localize(datetime(2024, 10, 2, 0, 0))
    VERSION = "1"

    # Get input data
    ELEMENTS_PATH = r"C:\Users\martynas.karobcikas\Documents\python_projects\nc-data-exchange\tests\test-data\TC1_remedial_actions.xlsx"
    elements = pd.read_excel(ELEMENTS_PATH)

    # Run service
    service = InputStructuralDataProfile(start_time=START_TIME, end_time=END_TIME, publisher="38X-BALTIC-RSC-H", version=VERSION)
    # co_rdfxml = service.generate_contingency_elements_profile(elements=elements)
    # ae_rdfxml = service.generate_assessed_elements_profile(elements=elements)
    ra_rdfxml = service.generate_remedial_actions_profile(elements=elements)

    # Export generated file
    from pathlib import Path
    # path = Path(__file__).parent.parent.joinpath("tests/exported_contingency_profile.xml")
    # path = Path(__file__).parent.parent.joinpath("tests/exported_assessed_element_profile.xml")
    path = Path(__file__).parent.parent.joinpath("tests/exported_remedial_action_profile.xml")
    with open(path, 'w') as file:
        file.write(ra_rdfxml.decode())
        logger.info(f"Serialized rdfxml profile saved: {ra_rdfxml}")

    # Upload to BMS
    # from rcc_common_tools import bms_api
    # BMS_SERVER = r"https://test-rcc-bht.elering.sise/"
    # logger.info(f"Uploading file to BMS: {BMS_SERVER}")
    # bms_api.upload_file(url=BMS_SERVER, xml=co_rdfxml)
