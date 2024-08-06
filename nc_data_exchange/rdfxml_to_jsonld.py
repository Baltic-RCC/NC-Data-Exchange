import rdflib
import json


def rdfxml_to_json(rdfxml_path, json_path):

    g = rdflib.Graph()
    g.parse(rdfxml_path, format='xml')

    context = {
        '@vocab': ""
    }

    json_ld = g.serialize(format='json-ld', context=context)

    json_dict = json.loads(json_ld)

    with open(json_path, 'w') as f:
        json.dump(json_dict, f, indent=4)


if __name__ == '__main__':
    # Test
    pass