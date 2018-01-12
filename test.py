import xmltodict


class Item(object):

    def __init__(self, label):

        self._label = label

    def __eq__(self, other):
        return isinstance(self, type(other)) and self.label() == other.label()

    def label(self):

        return self._label


class Signature(Item):

    def __init__(self, label, uid):

        super().__init__(label)
        self._uid = uid
        self._parent = None
        self._children = set()

    def __repr__(self):

        return '<Sig> ' + self.label()

    def id(self):

        return self._uid

    def parent(self, *parent):

        if len(parent) == 0:
            return self._parent
        else:
            self._parent = parent[0]
            return self

    def add_child(self, child):

        self._children.add(child)

    def remove_child(self, child):

        self._children.discard(child)

    def children(self):

        return self._children


class Atom(Item):

    def __init__(self, label, signature):

        super().__init__(label)
        self._signature = signature

    def __repr__(self):

        return '<Atom> ' + self.label()


with open('data/ex1.xml') as f:
    doc = xmltodict.parse(f.read())

# Extract all signatures and fields from the data
signatures = doc['alloy']['instance']['sig']
fields = doc['alloy']['instance']['field']


# Find a signature with a specific label
def get_signature(label):
    for sig in signatures:
        if sig['@label'] == label:
            return Signature(label, sig['@ID'])


# Populate signature
def populate(signature):
    for sig in signatures:
        if '@parentID' in sig and sig['@parentID'] == signature.id():
            child = Signature(sig['@label'], sig['@ID']).parent(signature)
            signature.add_child(child)

def populate_atoms(sig, signature):
    if 'atom' in sig:
        atoms = sig['atom']
        for atom in atoms:
            signature.add_child(Atom(atom['@label']))


# Find the univ signature
univ = get_signature('univ')
populate(univ)
print(univ)
for kid in univ.children():
    print('  ', kid)
