import json
import logging
import config
from typing import List
import pandas as pd
import triplets
from pathlib import Path
from lxml import etree
import uuid

# Start logger
logger = logging.getLogger(__name__)


def get_owl_metadata(data: pd.DataFrame):
    """Returns metadata about CIM profile defined in RDFS OWL Ontology"""
    return data.merge(data.query("KEY == 'type' and VALUE == 'http://www.w3.org/2002/07/owl#Ontology'").ID).set_index("KEY")["VALUE"]


def concrete_classes_list(data: pd.DataFrame):
    """Returns list of Concrete classes from Triplet"""
    return list(data.query("VALUE == 'http://iec.ch/TC57/NonStandard/UML#concrete'")["ID"])


def get_class_parameters(data: pd.DataFrame, class_name: str):
    """Returns parameters of the class and all the class names it extends"""
    # Get class data
    class_data = {"name": class_name,
                  "parameters": data.query("VALUE == @class_name & KEY == 'domain'"),
                  "extends": list(data.query("ID == @class_name and KEY == 'subClassOf'")["VALUE"].unique())}

    # Usually only one inheritance, warn if not
    if len(class_data["extends"]) > 1:
        logger.warning(f"{class_name} is inheriting form more than one class: {class_data['extends']}")

    return class_data


def get_all_class_parameters(data: pd.DataFrame, class_name: str):
    """Returns all parameters of the class including from classes it extends (inherits)"""

    all_class_parameters = pd.DataFrame()
    class_name_list = [class_name]

    for class_name in class_name_list:

        # Get current class parameters
        class_data = get_class_parameters(data, class_name)

        # Add parameters to others
        all_class_parameters = pd.concat([all_class_parameters, class_data["parameters"]])

        # Add classes that this class inherits
        class_name_list.extend(class_data["extends"])

    logger.info(f"Inheritance sequence: {' -> '.join(class_name_list)}")

    return all_class_parameters


def parameters_tableview_all(data: pd.DataFrame, class_name: str):
    """Provide class name to get table of all class parameters"""
    # Get all parameter names of class (natural and inherited)
    all_class_parameters = get_all_class_parameters(data, class_name)

    # Get parameters data
    type_data = all_class_parameters[["ID"]].merge(data, on="ID").drop_duplicates(["ID", "KEY"])

    # Pivot to table
    if not type_data.empty:
        data_view = type_data.pivot(index="ID", columns="KEY")["VALUE"]
    else:
        data_view = type_data

    return data_view


def parse_multiplicity(uri: str):
    """Converts multiplicity defined in extended RDFS to XSD minOccurs and maxOccurs"""
    multiplicity = str(uri).split("#M:")[1]
    min_occurs = multiplicity[-1].replace("n", "unbounded")
    max_occurs = multiplicity[0]

    return min_occurs, max_occurs


def convert(rdfs_paths: List[str], output_directory: str | None = None):

    # Load RDFS file
    data = triplets.rdf_parser.load_all_to_dataframe(rdfs_paths)

    # Append NamespaceMap table for each parsed file instance
    for instance_id, instance_data in data.groupby('INSTANCE_ID'):
        distribution_id = instance_data.query("VALUE == 'Distribution'").ID.item()
        label = instance_data.query("ID == @distribution_id and KEY == 'label'")

        # Parse XML
        parser = etree.XMLParser(remove_comments=True, collect_ids=False, remove_blank_text=True)
        parsed_xml = etree.parse(label.VALUE.item(), parser=parser).getroot()

        # Get namespace map
        nsmap = parsed_xml.nsmap
        nsmap_mrid = str(uuid.uuid4())

        # Add Type row of NamespaceMap
        nsmap['Type'] = 'NamespaceMap'

        # Append initial dataframe with NamespaceMap table
        nsmap_list = [{'ID': nsmap_mrid, 'KEY': k, 'VALUE': v, 'INSTANCE_ID': instance_id} for k, v in nsmap.items()]
        data = pd.concat([data, pd.DataFrame(nsmap_list)])

    # Dictionary to keep all configurations
    conf_dict = {}

    # Find all loaded profiles (RDFS)
    profiles = data["INSTANCE_ID"].unique()

    # Processing each loaded profile
    for profile in profiles:

        # Get current profile data and metadata
        profile_data = data.query(f"INSTANCE_ID == '{profile}'")
        metadata = get_owl_metadata(data=profile_data).to_dict()
        profile_name = metadata["keyword"]

        # Get namespace map
        namespace_map = data.merge(data.query("KEY == 'Type' and VALUE == 'NamespaceMap'").ID).set_index("KEY")["VALUE"].to_dict()
        namespace_map.pop("Type", None)

        # Dictionary to keep current profile schema
        conf_dict[profile_name] = {}
        conf_dict[profile_name]["NamespaceMap"] = namespace_map
        conf_dict[profile_name]["ProfileMetadata"] = metadata

        # Preserve cim and rdf namespaces
        cim_namespace = namespace_map["cim"]
        rdf_namespace = namespace_map["rdf"]

        # Get external classes (resource)
        classes_defined_externally = profile_data.query("KEY == 'stereotype' and VALUE == 'Description'").ID.to_list()

        # Add concrete classes
        for concrete_class in concrete_classes_list(data=profile_data):

            # Define class namespace, name and meta
            class_namespace, class_name = concrete_class.split("#")
            class_meta = profile_data.get_object_data(concrete_class).to_dict()
            if class_namespace == "":
                class_namespace = cim_namespace
            else:
                class_namespace = class_namespace + "#"

            # Define class ID attribute
            # TODO add conf for this, foreseen to change in CGMES 3.0, use rdf:about everywhere
            class_id_attribute = f"{{{rdf_namespace}}}ID"
            class_id_prefix = "_"
            if concrete_class in classes_defined_externally:
                class_id_attribute = f"{{{rdf_namespace}}}about"
                class_id_prefix = "#_"

            # Add class definition
            conf_dict[profile_name][class_name] = {
                                                    "attrib": {
                                                                "attribute": class_id_attribute,
                                                                "value_prefix": class_id_prefix
                                                             },
                                                    "namespace": class_namespace,
                                                    "description": class_meta.get("comment", ""),
                                                    "parameters": []
                                                    }

            # Add attributes
            for parameter, parameter_data in parameters_tableview_all(profile_data, concrete_class).iterrows():

                # Convert parameters data to dictionary
                parameter_dict = parameter_data.to_dict()

                # Get the association used
                association_used = parameter_dict.get("AssociationUsed", "NaN")

                # If it is association but not used, we don't export it
                if association_used == 'No':
                    continue

                # If it is used association or regular parameter, then we need the name and namespace
                parameter_namespace, parameter_name = parameter.split("#")

                if parameter_namespace == "":
                    parameter_namespace = cim_namespace
                else:
                    parameter_namespace = parameter_namespace + "#"

                # Declare parameter definition
                parameter_def = {"description": parameter_dict.get("comment", ""),
                                 "multiplicity": parameter_dict["multiplicity"].split("#M:")[1],
                                 "namespace": parameter_namespace,
                                 "xsd:minOccours": (parse_multiplicity(parameter_dict["multiplicity"]))[0],
                                 "xsd:maxOccours": (parse_multiplicity(parameter_dict["multiplicity"]))[1]}

                # If association
                if association_used == 'Yes':
                    parameter_def["attrib"] = {
                        "attribute": "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource",
                        "value_prefix": "#_"
                    }
                    parameter_def["type"] = "Association"
                    parameter_def["range"] = parameter_dict["range"]
                else:
                    # Get parameter data type
                    data_type = parameter_dict.get("dataType", "nan")

                    # If regular parameter
                    if str(data_type) != "nan":
                        data_type_namespace, data_type_name = data_type.split("#")
                        data_type_meta = data.get_object_data(data_type).to_dict()

                        if data_type_namespace == "":
                            data_type_namespace = cim_namespace

                        data_type_def = {
                            "description": data_type_meta.get("comment", ""),
                            "type": data_type_meta.get("stereotype", ""),
                            "namespace": data_type_namespace
                        }

                        parameter_def["type"] = data_type_name
                        conf_dict[profile_name][data_type_name] = data_type_def

                    # If enumeration
                    else:
                        parameter_def["attrib"] = {
                            "attribute": "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource",
                            "value_prefix": ""
                        }
                        parameter_def["type"] = "Enumeration"
                        parameter_def["range"] = parameter_dict["range"].replace("#", "")
                        parameter_def["values"] = []

                        # Add allowed values
                        values = profile_data.query(f"VALUE == '{parameter_dict['range']}' and KEY == 'type'").ID.tolist()

                        for value in values:
                            value_namespace, value_name = value.split("#")
                            value_meta = data.get_object_data(value).to_dict()

                            if value_namespace == "":
                                value_namespace = cim_namespace

                            value_def = {
                                "description": value_meta.get("comment", ""),
                                "namespace": value_namespace
                            }

                            parameter_def["values"].append(value_name)
                            conf_dict[profile_name][value_name] = value_def

                # Add parameter definition
                conf_dict[profile_name][parameter_name] = parameter_def

                # Add to class
                conf_dict[profile_name][class_name]["parameters"].append(parameter_name)

    # Save json to provided directory
    if output_directory:
        with open(output_directory, "w") as file_object:
            json.dump(conf_dict, file_object, indent=4)

    return conf_dict


if __name__ == '__main__':
    # Test conversion from rdfs to json
    input_path = r"C:\Users\martynas.karobcikas\Downloads\DocumentHeaderProfile_v2_3_RDFSv2030_19Oct2023.rdf"
    output_path = str(Path(__file__).parent.joinpath(r"profiles\rdfs\rdfs_DocumentHeader.json"))
    converted = convert(rdfs_paths=[input_path], output_directory=output_path)

    # TODO add FullModel definition if necessary (defined under rdfs_tools