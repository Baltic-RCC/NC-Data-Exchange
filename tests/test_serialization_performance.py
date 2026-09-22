import time
from rdflib import Graph

g = Graph()
g.parse("your_test_output.xml")  # or build a representative graph

t0 = time.perf_counter()
g.serialize(format='pretty-xml')
t1 = time.perf_counter()
g.serialize(format='xml')
t2 = time.perf_counter()

print(f"pretty-xml: {t1 - t0:.4f}s")
print(f"xml:        {t2 - t1:.4f}s")