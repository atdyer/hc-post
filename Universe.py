import xmltodict


class Item(object):

    def __init__(self, label, uid):

        self._label = label
        self._uid = uid
        self._parent = None
        self._children = []

    def __eq__(self, other):

        return isinstance(self, type(other)) and self.label() == other.label()

    def add_child(self, child):

        self._children.append(child)
        return self

    def children(self):

        return self._children

    def each_child(self, func, typecheck=object):

        for child in self.children():
            if isinstance(child, typecheck):
                func(child)
            child.each_child(func, typecheck)

    def find_by_id(self, uid):

        if self.id() == uid:
            return self
        for child in self.children():
            item = child.find_by_id(uid)
            if item is not None:
                return item
        return None

    def id(self):

        return self._uid

    def label(self):

        return self._label

    def parent(self, *parent):

        if len(parent) == 0:
            return self._parent
        else:
            self._parent = parent[0]
            return self

    def print(self, depth=0):

        print(' '*depth, self)
        for child in self.children():
            child.print(depth+2)


class Signature(Item):

    def __init__(self, data):

        super().__init__(data['@label'], data['@ID'])

        # Extract properties
        self._abstract = True if '@abstract' in data and data['@abstract'] == 'yes' else False
        self._builtin = True if '@builtin' in data and data['@builtin'] == 'yes' else False
        self._lone = True if '@lone' in data and data['@lone'] == 'yes' else False
        self._one = True if '@one' in data and data['@one'] == 'yes' else False
        self._private = True if '@private' in data and data['@private'] == 'yes' else False

        # Extract atoms
        self._atoms = []
        if 'atom' in data:
            atoms = data['atom']
            if self._lone or self._one:
                self._atoms.append(Atom(self, atoms['@label']))
            else:
                for atom in atoms:
                    self._atoms.append(Atom(self, atom['@label']))

    def __repr__(self):

        return '<Sig> ' + self.label()

    def atoms(self):

        atoms = self._atoms
        for sig in self.signatures():
            atoms += sig.atoms()
        return atoms

    def fields(self):

        return [child for child in self.children() if isinstance(child, Field)]

    def find_atom(self, label):

        for atom in self.atoms():
            if atom.label() == label:
                return atom
        return None

    def signatures(self):

        return [child for child in self.children() if isinstance(child, Signature)]


class Atom:

    def __init__(self, sig, label):

        self._sig = sig
        self._label = label

    def __repr__(self):

        return '<Atom> ' + self.label()

    def signature(self):

        return self._sig

    def label(self):

        return self._label


class Field(Item):

    def __init__(self, data, sig_tree):

        super().__init__(data['@label'], data['@ID'])

        # Extract field types
        types = data['types']['type']
        self._types = list(map(lambda t: sig_tree.find_by_id(t['@ID']), types))

        # Extract tuples
        self._tuples = []
        if 'tuple' in data:
            tuples = data['tuple']
            if not isinstance(tuples, list):
                tuples = [tuples]
            for tup in tuples:
                labels = [atom['@label'] for atom in tup['atom']]
                labels_and_types = zip(labels, self.types())
                tup = tuple([sig.find_atom(label) for label, sig in labels_and_types])
                self._tuples.append(tup)

    def __repr__(self):

        return '<Field> ' + self.label() + ': ' + ' -> '.join([str(t) for t in self.types()])

    def tuples(self):

        return self._tuples

    def types(self):

        return self._types


# Creates list of items that are in a but not in b
def list_diff(a, b):
    return [item for item in a if item not in b]


# Builds a signature tree from the given list of signatures
def populate_signature_tree(signature, signature_list):
    child_list = [sig for sig in signature_list if '@parentID' in sig and sig['@parentID'] == signature.id()]
    remaining_list = list_diff(signature_list, child_list)
    for child in child_list:
        sig = Signature(child).parent(signature)
        signature.add_child(sig)
        remaining_list = populate_signature_tree(sig, remaining_list)
    return remaining_list


class Universe:

    def __init__(self, xml):

        data = None

        try:

            with open(xml) as f:
                data = xmltodict.parse(f.read())

        except IOError:

            print('Error opening file', xml)
            exit()

        # Extract the lists of signatures and fields
        self._instance = data['alloy']['instance']
        signatures = self._instance['sig']
        fields = self._instance['field']

        # Find the univ signature
        self._univ = None
        for sig in signatures:
            if sig['@label'] == 'univ':
                self._univ = Signature(sig)

        # Build the signature tree recursively
        populate_signature_tree(self._univ, signatures)

        # Parse and add all fields to universe
        for field in fields:
            parent = self._univ.find_by_id(field['@parentID'])
            f = Field(field, self._univ).parent(parent)
            parent.add_child(f)

    def command(self):

        return self._instance['@command']

    def filename(self):

        return self._instance['@filename']

    def print(self):

        self._univ.print()


test = Universe('data/ex1.xml')
print(test.filename())
print(test.command())
test.print()

