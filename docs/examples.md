## Example 1: Generate NC profile from MS Excel file
```
import logging
from datetime import datetime
import pytz
import pandas as pd
import numpy as np
from nc_data_exchange.profiles import AssessedElement, Contingency, RemedialAction
from nc_data_exchange.profile_constructor import Profile

logger = logging.getLogger(__name__)

START_TIME = pytz.timezone('CET').localize(datetime(2024, 6, 7, 0, 0))
END_TIME = pytz.timezone('CET').localize(datetime(2024, 6, 8, 0, 0))
VERSION = "1"

# Parse input data
FILE_PATH = r"file-path.xlsx"

# Run service
service = InputStructuralDataProfile(start_time=START_TIME, end_time=END_TIME, version=VERSION)
co_rdfxml = service.generate_contingency_elements_profile(elements=FILE_PATH)

# Export generated file
EXPORT_PATH = r"export-file.xml"
with open(EXPORT_PATH, 'w') as file:
    file.write(co_rdfxml.decode())
    logger.info(f"Serialized rdfxml profile saved: {co_rdfxml}")
```

## Example 2: Upload file to EDX
```
import EDX
import uuid
import logging

logger = logging.getLogger(__name__)

SERVER = 'test-server'
USERNAME = 'test-username'
PASSWORD = 'test-password'

FILE_PATH = 'file-path'
RECEIVER = 'test-receiver'
BUSINESS_TYPE = 'test-business-type'

# Read the file
with open(FILE_PATH, "rb") as loaded_file:
    content = loaded_file.read()

try:
    # Create service
    service = EDX.create_client(SERVER, USERNAME, PASSWORD)
    message_id = service.send_message(receiver_EIC=RECEIVER,
                                      business_type=BUSINESS_TYPE,
                                      content=content,
                                      ba_message_id=f"{str(uuid.uuid4())}",
                                      )
    time.sleep(10)  # waiting until message is processed
    response = service.check_message_status(message_id)
    if response['state'] == 'DELIVERED':
        logger.info(f"Analysis results published to {response['receiverCode']} with message id: {response['messageID']}")
    else:
        logger.error(f"Analysis results publication to {RECEIVER} unsuccessful with message state: {response['state']}")
        logger.error(f"Message {response['messageID']} details: {response['trace']['trace'][-1]['details']}")
except Exception as e:
    logger.error(f"Unable to publish results to {RECEIVER} via PDN network")
    logger.error(f"Error returned: {e}")
```
