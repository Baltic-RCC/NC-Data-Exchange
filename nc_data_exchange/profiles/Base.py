from pydantic import BaseModel, Field
from typing import Optional
import uuid


class IdentifiedObject(BaseModel):
    mRID: str = Field(default_factory=lambda: f"{uuid.uuid4()}", max_length=36, min_length=36)
    name: Optional[str] = None
    description: Optional[str] = None

    # Custom internal attributes
    ConsistencyStatus: Optional[str] = Field(default=None, repr=False)


class PowerSystemResource(IdentifiedObject):
    pass


if __name__ == '__main__':
    # Test data
    data = {'mRID': "c60d365a-b008-48ef-a83d-c73b25bdf060", 'name': 'testname'}
    instance = IdentifiedObject(**data)

