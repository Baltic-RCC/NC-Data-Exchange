import logging
from datetime import datetime
import pytz
from nc_data_exchange.generate_csa_input_data import InputStructuralDataProfile
import pandas as pd


# Start logger
logger = logging.getLogger(__name__)

# Testing
START_TIME = pytz.timezone('CET').localize(datetime(2024, 6, 13, 0, 0))
END_TIME = pytz.timezone('CET').localize(datetime(2024, 6, 14, 0, 0))
VERSION = "1"
service = InputStructuralDataProfile(start_time=START_TIME,
                                     end_time=END_TIME,
                                     publisher="38X-BALTIC-RSC-H",
                                     version=VERSION)

# Export contingencies dataset
CONTINGENCIES_INPUT_PATH = "test-data/TC1_contingencies.xlsx"
CONTINGENCIES_OUTPUT_PATH = "test-data/TC1_contingencies.xml"
contingencies = pd.read_excel(CONTINGENCIES_INPUT_PATH)
co_rdfxml = service.generate_contingency_elements_profile(elements=contingencies)
with open(CONTINGENCIES_OUTPUT_PATH, 'w') as file:
    file.write(co_rdfxml.decode())
    logger.info(f"Serialized rdfxml profile saved: {co_rdfxml}")
# rdfxml_to_json(CONTINGENCIES_OUTPUT_PATH, r"contingencies_json.json")

# Export assessed elements dataset
ASSESSED_ELEMENTS_INPUT_PATH = "test-data/TC1_assessed_elements.xlsx"
ASSESSED_ELEMENTS_OUTPUT_PATH = "test-data/TC1_assessed_elements.xml"
assessed_elements = pd.read_excel(ASSESSED_ELEMENTS_INPUT_PATH)
ae_rdfxml = service.generate_assessed_elements_profile(elements=assessed_elements)
with open(ASSESSED_ELEMENTS_OUTPUT_PATH, 'w') as file:
    file.write(ae_rdfxml.decode())
    logger.info(f"Serialized rdfxml profile saved: {ae_rdfxml}")

# Export remedial actions dataset
REMEDIAL_ACTIONS_INPUT_PATH = "test-data/TC1_remedial_actions.xlsx"
REMEDIAL_ACTIONS_OUTPUT_PATH = "test-data/TC1_remedial_actions.xml"
remedial_actions = pd.read_excel(REMEDIAL_ACTIONS_INPUT_PATH)
ra_rdfxml = service.generate_remedial_actions_profile(elements=remedial_actions)
with open(REMEDIAL_ACTIONS_OUTPUT_PATH, 'w') as file:
    file.write(ra_rdfxml.decode())
    logger.info(f"Serialized rdfxml profile saved: {ra_rdfxml}")
