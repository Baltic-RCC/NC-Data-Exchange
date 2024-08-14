## Profile construction approaches
- Class attribute refers to class defined in same profile:
  - Attribute value given as a dataclass instance
  - Type hint used - object
- Class attribute refers to class defined in other profile:
  - Attribute value gives as mRID without leading '#' notation which is automatically added in __post_init()

## UML Datatypes
- URI - string following the rules defined by thw W3C/IETF 
- IRI - serialized as rdf:resource in RDFXML
- StringIRI - serialized as literal without language support
- String
- Datetime - expressed as string in UTC time zone ('Z' at the end)