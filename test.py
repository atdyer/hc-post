from alloy import Universe


inst = Universe('data/ex1.xml').instance()
end = inst.find_by_label('end')
vertex = inst.find_by_id('13')
print(end)
print(vertex)
inst.print()

