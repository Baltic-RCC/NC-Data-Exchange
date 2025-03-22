import rdflib
import json
import xmltodict


def rdfxml_to_jsonld(rdfxml_path, json_path):

    g = rdflib.Graph()
    g.parse(rdfxml_path, format='xml')

    context = {
        '@vocab': ""
    }

    json_ld = g.serialize(format='json-ld', context=context)

    json_dict = json.loads(json_ld)

    with open(json_path, 'w') as f:
        json.dump(json_dict, f, indent=4)


def rdfxml_to_json(rdfxml_path, json_path):

    with open(rdfxml_path, 'r') as f:
        xml_content = f.read()

    json_dict = xmltodict.parse(xml_content)

    with open(json_path, 'w') as f:
        json.dump(json_dict, f, indent=4)


if __name__ == '__main__':
    # Test
    CONTINGENCY_FILE_PATH = r"C:\Users\martynas.karobcikas\Documents\python_projects\nc-data-exchange\tests\test-data\TC1_contingencies.xml"
    OUTPUT_PATH = r"C:\Users\martynas.karobcikas\Documents\python_projects\nc-data-exchange\tests\test-data\TC1_contingencies.json"
    rdfxml_to_jsonld(rdfxml_path=CONTINGENCY_FILE_PATH, json_path=OUTPUT_PATH)
    rdfxml_to_json(rdfxml_path=CONTINGENCY_FILE_PATH, json_path=OUTPUT_PATH)