import logging
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, BaseModel
from typing import List, Any, Dict, Literal
from typing_extensions import TypedDict
import pandas as pd

# Start logger
logger = logging.getLogger(__name__)


def _print_parameter_source(classobj: object, sanitize_mask: str = '****') -> None:
    model_env_prefix = classobj.model_config.get('env_prefix')
    for parameter_name, parameter_value in classobj.model_dump(exclude_none=True).items():
        sanitize_flag = 'password' in parameter_name
        if parameter_name in classobj.model_fields_set:
            if os.environ.get(f"{model_env_prefix.lower()}{parameter_name}" if model_env_prefix else parameter_name):
                parameter_source = 'ENVIRONMENT'
            else:
                parameter_source = 'DOTENV'
        else:
            parameter_source = 'CONFIGURATION'

        # Add prefix to parameter name if it was used in model
        parameter_name = f"{model_env_prefix.lower()}{parameter_name}" if model_env_prefix else parameter_name

        # Sanitize parameter value
        parameter_value = sanitize_mask if sanitize_flag else parameter_value

        # Log message
        logger.info(f"[{parameter_source}] Parameter {parameter_name}: {parameter_value}")


class CustomBaseSettings(BaseSettings):
    """
    Modified class of BaseSettings with automatically printing parameters source to logger
    """
    # suspends the output to stdout
    suspend_stdout: bool = Field(default=False, exclude=True, repr=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.suspend_stdout:
            _print_parameter_source(self)


class NetworkCodeProfileConstructor(CustomBaseSettings):
    default_ns_prefix: str = 'brcc'
    default_ns_uri: str = 'https://baltic-rcc.eu/ns/brcc-nc#'
    resource_prefixes: List[str] = ['http:', 'https:', '#_']
    class_id_attributes: List[str] = ['mRID', 'identifier']
    ns_serialize_without_class_notation: List[str] = ['dcat', 'dcterms', 'prov']


class Area(TypedDict):
    short_name: str
    area_eic: str
    tso: str
    tso_eic: str


class Border(TypedDict):
    name: str
    eic: str
    tso1: str
    tso2: str


class Areas(BaseModel):
    lithuania: Area = Area(short_name="LT", area_eic="10YLT-1001A0008Q", tso="LITGRID", tso_eic="10X1001A1001A55Y")
    latvia: Area = Area(short_name="LV", area_eic="10YLV-1001A00074", tso="AST", tso_eic="10X1001A1001B54W")
    estonia: Area = Area(short_name="EE", area_eic="10Y1001A1001A39I", tso="ELERING", tso_eic="10X1001A1001A39W")
    poland: Area = Area(short_name="PL", area_eic="10YPL-AREA-----S", tso="PSE", tso_eic="10XPL-TSO------P")
    belgium: Area = Area(short_name="BE", area_eic="10YBE----------2", tso="ELIA", tso_eic="10X1001A1001A094")
    netherlands: Area = Area(short_name="NL", area_eic="10YNL----------L", tso="TENNET", tso_eic="10X1001A1001A361")

    baltic: Area = Area(short_name="BALTIC", area_eic="10Y1001C--00120B")
    core: Area = Area(short_name="CORE", area_eic="10Y1001C--00059P")

    @property
    def df(self):
        return pd.DataFrame(self.model_dump()).T


class Borders(BaseModel):
    belgium_netherlands: Border = Border(name="BE-NL", eic="10YDOM--BE-NL--8", tso1="ELIA", tso2="TENNET")
    lithuania_latvia: Border = Border(name="LV-LT", eic="10YDOM-1001A055O", tso1="AST", tso2="LITGRID")

    @property
    def df(self):
        return pd.DataFrame(self.model_dump()).T
