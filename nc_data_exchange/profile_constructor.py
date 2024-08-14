from datetime import datetime
import pytz
import inspect
import uuid
import logging
import json
import os
import xmltodict
from lxml import etree
from enum import Enum
from pydantic import BaseModel
import pandas as pd
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF
import nc_data_exchange.config as conf

# Start logger
logger = logging.getLogger(__name__)

# Loading configuration
config = conf.NetworkCodeProfileConstructor()


class Profile:

    def __init__(self, profile_name):
        # TODO add validation for profile names
        self.profile_name = profile_name
        self.graph = Graph()
        self.nm = self.graph.namespace_manager

        # Bind custom local Baltic RCC namespace
        self.nm.bind(prefix=config.default_ns_prefix, namespace=config.default_ns_uri)

        logger.info(f"Constructing network code profile: {self.profile_name}")

        # Read profile RDF schema (RDFS)
        self.rdfs = self.load_rdfs(profile_name=self.profile_name)

    @property
    def rdf_pretty_xml(self) -> str:
        return self.graph.serialize(format='pretty-xml', max_depth=1)

    @property
    def xml_tree(self):
        return etree.fromstring(self.rdf_pretty_xml.encode('utf-8'))

    @staticmethod
    def generate_mrid() -> str:
        return f"{uuid.uuid4()}"

    @staticmethod
    def get_attrib_full_key_name(instance: object, attrib_name: str) -> str:
        """Method to identify class to which belongs attribute and return full key name. Ex:
        argument attrib_name: mRID
        return: 'IdentifiedObject.mRID'
        """
        instance_inheritance_tree = inspect.getmro(instance.__class__)
        for cls in instance_inheritance_tree[:-1]:  # last mro object is always generic 'object' class
            exists = cls.__annotations__.get(attrib_name, None)
            if exists:
                return f"{cls.__name__}.{attrib_name}"
        else:
            return attrib_name

    def load_rdfs(self, profile_name: str):
        rdfs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"rdfs/rdfs_{profile_name}.json")
        with open(rdfs_path, "r") as rdfs_file:
            rdfs = json.load(rdfs_file)
            rdfs = rdfs[next(iter(rdfs))]

        # Binding namespaces from RDF schema
        nsmap = rdfs.get('NamespaceMap', None)
        self.bind_namespaces(namespaces=nsmap)

        return rdfs

    def bind_namespaces(self, namespaces: dict):
        for nskey, nsval in namespaces.items():
            self.nm.bind(nskey, nsval, replace=True)

    def get_namespace_key(self, ns_value) -> str:
        for prefix, value in dict(self.nm.namespaces()).items():
            if ns_value == str(value):
                return prefix
        else:
            logger.warning(f"Prefix not found of namespace: {ns_value}")
            return str()

    def add_document_header(self,
                            start_date: str | datetime | None = None,
                            end_date: str | datetime | None = None,
                            scenario_time: str | datetime | None = None,
                            version: str = '1',
                            description: str | None = None,
                            was_generated_by: str | None = None,
                            ):
        """
        Adding FullModel header metadata to graph
        :return: nothing
        """
        from nc_data_exchange.profiles import DocumentHeader

        # Converting datetime objects if necessary
        if isinstance(start_date, datetime):
            start_date = start_date.astimezone(pytz.utc).replace(tzinfo=None).isoformat()
        if isinstance(end_date, datetime):
            end_date = end_date.astimezone(pytz.utc).replace(tzinfo=None).isoformat()
        if isinstance(scenario_time, datetime):
            scenario_time = scenario_time.astimezone(pytz.utc).replace(tzinfo=None).isoformat()

        # Read profile RDF schema (RDFS)
        rdfs = self.load_rdfs(profile_name='DocumentHeader')

        # Creating FullModel document header instances
        header = DocumentHeader.FullModel(profile_name=self.profile_name,
                                          startDate=start_date,
                                          endDate=end_date,
                                          scenarioTime=scenario_time,
                                          version=version,
                                          description=description,
                                          wasGeneratedBy=was_generated_by,
                                          )
        self.add_element(element=header, rdfs=rdfs)

    def add_element(self, element: object, rdfs: dict = None):
        """
        Method to add model instance to graph
        :param element: model instance
        :param rdfs: RDF schema in dict format. If None - uses rdfs from Profile class instance
        :return:
        """
        # Convert model to dictionary
        attributes = element.model_dump(exclude_none=True)

        # Check if given element has mRID or identifier attribute, if not - generate random
        for key in config.class_id_attributes:
            class_mrid = attributes.get(key, None)
            if class_mrid:
                break
        else:
            class_mrid = self.generate_mrid()

        # Define relevant rdfs
        if not rdfs:
            rdfs = self.rdfs  # getting from class instance

        # Add class to rdf graph
        class_name = element.__class__.__name__
        logger.debug(f"Adding class to graph: {class_name} [mrid: {class_mrid}]")
        class_config = rdfs.get(class_name, None)
        if not class_config:
            logger.debug(f"RDFS configuration not defined for class: {class_name}")

        class_ns = class_config.get('namespace', None)
        if not class_ns:
            class_ns = config.default_ns_uri
            logger.debug(f"For class {class_name} using default local namespace: {class_ns}")

        # add _ prefix if identifier is not an urn:uuid
        # TODO change to get prefix from rdfs
        class_subject = URIRef(f"_{class_mrid}") if not class_mrid.startswith('urn:') else URIRef(class_mrid)
        class_predicate = RDF.type
        class_object = URIRef(f"{class_ns}{class_name}")

        self.graph.add((class_subject, class_predicate, class_object))

        # Add attributes to class on rdf graph
        for attrib_key, attrib_val in attributes.items():

            # Ignore attribute which is empty string
            if isinstance(attrib_val, str) and not attrib_val:
                logger.debug(f"Ignoring attribute {attrib_key} with value: empty string")
                continue

            # Getting configuration from rdfs
            full_attrib_name = self.get_attrib_full_key_name(element, attrib_key)
            # trying to get rdfs config firstly by full attribute name (class_name.attribute_name), then only by attribute name
            for key in [full_attrib_name, attrib_key]:
                attrib_config = rdfs.get(key)
                if attrib_config:
                    break
            else:
                logger.debug(f"RDFS configuration not defined for attribute: {full_attrib_name}")
                attrib_config = {}

            attrib_ns = attrib_config.get('namespace', None)
            if not attrib_ns:
                attrib_ns = config.default_ns_uri
                logger.debug(f"For attribute {full_attrib_name} using default local namespace: {attrib_ns}")

            # Define whether to use {Class} notation in attribute tag
            # Some header attributes should be serialized without class notation
            attrib_ns_prefix = self.get_namespace_key(attrib_ns)
            if attrib_ns_prefix in config.ns_serialize_without_class_notation:
                attrib_name = attrib_key
            else:
                attrib_name = full_attrib_name

            attrib_predicate = URIRef(f"{attrib_ns}{attrib_name}")

            # Check whether attribute value is not a list - add it to list to be able to implement loop
            if not isinstance(attrib_val, list):
                attrib_val = [attrib_val]

            # Running loop to add attribute values
            for value in attrib_val:

                # From rdfs define what is attribute value prefix
                prefix = attrib_config.get('attrib', {'value_prefix': ''}).get('value_prefix')

                # Check whether attribute value is instance of pydantic BaseModel class
                if isinstance(getattr(element, attrib_key), BaseModel):
                    value = f"{value.get('mRID')}"

                # If it is Enum class object, applying conversion to string
                if isinstance(value, Enum):
                    value = f"{value}"

                if isinstance(value, str) and value.startswith(tuple(config.resource_prefixes)):
                    attrib_object = URIRef(value)
                elif prefix:
                    attrib_object = URIRef(f"{prefix}{value}")
                else:
                    attrib_object = Literal(value)

                # TODO backup solution
                # # Check whether attribute value is instance of pydantic BaseModel class
                # if isinstance(getattr(element, attrib_key), BaseModel):
                #     attrib_object = URIRef(f"#_{value.get('mRID')}")
                # else:
                #     # Check whether attribute object is resource or literal from string representation
                #     if isinstance(value, str) and value.startswith(tuple(config.resource_prefixes)):
                #         attrib_object = URIRef(value)
                #     # If it is Enum class object, applying conversion to string
                #     elif isinstance(value, Enum):
                #         attrib_object = URIRef(f"{value}")
                #     else:
                #         attrib_object = Literal(value)

                logger.debug(f"Adding class attribute: {(attrib_predicate.fragment, attrib_object.__str__())}")
                self.graph.add((class_subject, attrib_predicate, attrib_object))

    def validate(self, shacl_path: str, output_path: str | None = None):
        """
        Method to validate by SHACL shapes file in .ttl format
        :param shacl_path: path to SHACL file
        :param output_path: export validation report to given path
        :return: conformity flag, xml report and text report
        """
        import pyshacl

        logger.info(f"Running SHACL validation by: {shacl_path}")

        # Parse SHACL file
        shapes = Graph()
        shapes.parse(shacl_path)

        # Perform validation
        processed_rdfxml = self.get_profile_xml(fix_rdf_about=True, remove_rdf_datatype=True, return_xmlstr=True)
        data = Graph().parse(data=processed_rdfxml, format='xml')
        conforms, results_graph, results_text = pyshacl.validate(data_graph=data,
                                                                 shacl_graph=shapes,
                                                                 inference='rdfs')
        validation_report = results_graph.serialize(format='pretty-xml')

        # Export xml validation report
        if output_path:
            with open(output_path, 'w') as file:
                file.write(validation_report)

        return conforms, validation_report, results_text

    def get_profile_xml(self,
                        fix_rdf_about: bool = False,
                        remove_rdf_datatype: bool = False,
                        return_xmlstr: bool = True,
                        save: bool = False,
                        output_path: str | None = None,
                        ) -> str:
        """
        Method to export graph to RDF XML file with additional fixes
        :param fix_rdf_about: replaces rdf:about by rdf:ID and add leading underscore to mRID
        :param remove_rdf_datatype: removes rdf:datatype attributes from all elements
        :param return_xmlstr: flag to return modified xml in string format or xml tree. Default returns in string
        :param save: flag defined whether file will be saved or not
        :param output_path: exported file path
        :return: profile in xml string format
        """
        logger.info(f"Serializing graph to rdfxml")

        # Getting xml tree from graph
        tree = self.xml_tree

        if fix_rdf_about:
            logger.debug(f"Replacing rdf:about by rdf:ID")
            class_instances = tree.getchildren()
            for instance in class_instances:
                # Skip FullModel header instance
                if 'FullModel' in instance.tag:
                    continue
                for key, val in instance.attrib.items():
                    if 'about' in key:
                        instance.attrib.pop(key)
                        updated_key = key.replace('about', 'ID')
                        # updated_val = f"_{val}"  # adding leading underscore
                        instance.set(updated_key, val)

        if remove_rdf_datatype:
            logger.debug(f"Removing attributes datatype definitions")
            elements = tree.findall(".//*[@rdf:datatype]", tree.nsmap)
            for element in elements:
                element.attrib.clear()

        # Fixing xml order by bringing header to first position and sorting other classes
        tree[:] = sorted(tree, key=lambda x: x.tag)
        header = tree.find(".//md:FullModel", tree.nsmap)
        tree.remove(header)
        tree.insert(0, header)

        xmlstr = etree.tostring(tree, pretty_print=True, xml_declaration=True, encoding='UTF-8')

        if save:
            if not output_path:
                output_path = os.path.join(os.path.dirname(__file__), f"tests/samples/ex_{self.profile_name}.xml")
            with open(output_path, 'w') as file:
                file.write(xmlstr.decode())
                logger.info(f"Serialized rdfxml profile saved: {output_path}")

        if return_xmlstr:
            return xmlstr
        else:
            return tree

    def export_graph(self, output_path):
        rdf_pretty_xml = self.rdf_pretty_xml
        with open(output_path, 'w') as file:
            file.write(rdf_pretty_xml)

    def export_to_excel(self,
                        output_path: str | None = None,
                        ):

        tree = self.get_profile_xml(fix_rdf_about=True, remove_rdf_datatype=True)
        xmldict = xmltodict.parse(tree, xml_attribs=True)["rdf:RDF"]
        profile_classes = [key for key in xmldict.keys() if '@xmlns' not in key]

        if not output_path:
            output_path = os.path.join(os.path.dirname(__file__), f"samples/ex_{self.profile_name}.xlsx")

        with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:

            for class_key in profile_classes:
                class_instances = xmldict.get(class_key)
                if isinstance(class_instances, dict):
                    class_instances = [class_instances]
                class_df = pd.DataFrame.from_dict(class_instances)
                class_df = class_df.applymap(lambda x: x.get("@rdf:resource") if isinstance(x, dict) else x)
                class_df.columns = class_df.columns.map(lambda x: x.split(":")[-1])

                # Export to excel
                sheet_name = class_key.split(":")[-1]
                class_df.to_excel(writer, header=True, sheet_name=sheet_name, index=False)

    def get_from_excel(self, input_path: str | None = None):

        dict_of_dfs = pd.read_excel(input_path, sheet_name=None, index_col=0)

        for class_name, data in dict_of_dfs.items():

            if class_name == "FullModel":
                rdfs = self.load_rdfs(profile_name='DocumentHeader')
            else:
                rdfs = self.rdfs

            mask = data.applymap(type) != bool
            mapping = {True: 'true', False: 'false'}
            data = data.where(mask, data.replace(mapping))

            class_config = rdfs.get(class_name, None)
            if not class_config:
                logger.warning(f"RDFS configuration not defined for class: {class_name}")

            class_ns = class_config.get('namespace', None)
            if not class_ns:
                class_ns = config.default_ns_uri
                logger.warning(f"For class {class_name} using default namespace: {class_ns}")

            for class_mrid, attribs in data.iterrows():

                class_subject = URIRef(class_mrid)
                class_predicate = RDF.type
                class_object = URIRef(f"{class_ns}{class_name}")
                self.graph.add((class_subject, class_predicate, class_object))

                # Add attributes to class
                for attrib_key, attrib_val in attribs.items():

                    # Getting configuration from rdfs
                    for key in [attrib_key, attrib_key.split(".")[-1]]:  # trying to get rdfs config firstly by full attribute name (class_name.attribute_name), then only by attribute name
                        attrib_config = rdfs.get(key)
                        if attrib_config:
                            break
                    else:
                        logger.warning(f"RDFS configuration not defined for attribute: {attrib_key}")
                        attrib_config = {}

                    attrib_ns = attrib_config.get('namespace', None)
                    if not attrib_ns:
                        attrib_ns = config.default_ns_uri
                        logger.warning(f"For attribute {attrib_key} using default namespace: {attrib_ns}")

                    attrib_predicate = URIRef(f"{attrib_ns}{attrib_key}")

                    # Check whether attribute object is resource or literal from string representation
                    if isinstance(attrib_val, str) and attrib_val.startswith(tuple(config.resource_prefixes)):
                        attrib_object = URIRef(attrib_val)
                    else:
                        attrib_object = Literal(attrib_val)

                    self.graph.add((class_subject, attrib_predicate, attrib_object))


if __name__ == '__main__':
    # Test profile constructor
    profile = Profile('Contingency')

    # Test parsing from Excel to rdflib
    profile.get_from_excel(input_path="test.xlsx")
    # print(profile.rdf_pretty_xml)
    profile.get_profile_xml(
        output_path=r"test_xml.xml",
        fix_rdf_about=True,
        remove_rdf_datatype=True,
        save=True,
    )