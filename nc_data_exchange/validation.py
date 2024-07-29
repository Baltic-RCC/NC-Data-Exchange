import rdflib
import pyshacl
from pathlib import Path


def validate(xml_path: str, shacl_path: str):

    # Parse rdfxml profile
    data = rdflib.Graph().parse(data=xml_path, format='xml')

    # Parse SHACL file
    shapes = rdflib.Graph().parse(shacl_path)

    # Perform validation
    conforms, results_graph, results_text = pyshacl.validate(data_graph=data,
                                                             shacl_graph=shapes,
                                                             inference='rdfs')
    validation_report = results_graph.serialize(format='pretty-xml')

    return conforms, validation_report, results_text


if __name__ == '__main__':
    # Test
    xml_path = r"contingencies_TC1.xml"
    shacl_path = r"C:\Users\martynas.karobcikas\Downloads\Contingency-AP-Con-Simple-SHACL_v2-3-0.ttl"
    conforms, validation_report, results_text = validate(xml_path=xml_path, shacl_path=shacl_path)

    # Export validation report
    output_path = str(Path(__file__).parent.joinpath(r"validation_report.xml"))
    with open(output_path, 'w') as file:
        file.write(validation_report)
