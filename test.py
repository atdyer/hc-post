from alloy import Universe


inst = Universe('data/ex1.xml').instance()

edges = inst.find('$this/edges')
for edge in edges.tuples():
    print(edge[0], '->', edge[1])

# end = inst.find('B$0')
# vertex = inst.find_by_id('13')
# print(end)
# print(vertex)
# inst.print()

