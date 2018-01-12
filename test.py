import xmltodict


class Item(object):

    def __init__(self, label, uid):

        self._label = label
        self._uid = uid
        self._parent = None
        self._children = []

    def __eq__(self, other):
        return isinstance(self, type(other)) and self.label() == other.label()

    def label(self):

        return self._label

    def id(self):

        return self._uid

    def parent(self, *parent):

        if len(parent) == 0:
            return self._parent
        else:
            self._parent = parent[0]
            return self

    def add_child(self, child):

        self._children.append(child)

    def each_child(self, func, typecheck=object):
        for child in self.children():
            if isinstance(child, typecheck):
                func(child)
            child.each_child(func, typecheck)

    def children(self):

        return self._children

    def find_by_id(self, uid):

        if self.id() == uid:
            return self
        for child in self.children():
            found = child.find_by_id()
            if found is not None:
                return found
        return None


class Signature(Item):

    def __init__(self, label, uid):

        super().__init__(label, uid)

    def __repr__(self):

        return '<Sig> ' + self.label()

    def fields(self):

        return [child for child in self._children if isinstance(child, Field)]

    def signatures(self):

        return [child for child in self._children if isinstance(child, Signature)]


class Field(Item):

    def __init__(self, label, uid, *types):

        super().__init__(label, uid)
        self._types = types

    def __repr__(self):

        return '<Field> ' + self.label() + ': ' + ' -> '.join(self._types)

    @staticmethod
    def from_ordered_dict(od):
        types = []
        for t in od['types']['type']:
            types.append(t['@ID'])
        return Field(od['@label'], od['@ID'], *types)

    def convert_ids_to_types(self, tree):
        self._types = map(lambda uid: tree.find_by_id(uid), self._types)


with open('data/ex1.xml') as f:
    doc = xmltodict.parse(f.read())

# Extract all signatures and fields from the data
signatures = doc['alloy']['instance']['sig']
fields = doc['alloy']['instance']['field']


# Return the difference between two lists (returns a-b)
def list_diff(a, b):
    return [item for item in a if item not in b]


# Find a signature with a specific label
def get_signature(label):
    for sig in signatures:
        if sig['@label'] == label:
            return Signature(label, sig['@ID'])


# Populate signature
def populate_signature(signature, signature_list):
    child_list = [sig for sig in signature_list if '@parentID' in sig and sig['@parentID'] == signature.id()]
    remaining_list = list_diff(signature_list, child_list)
    for child in child_list:
        sig = Signature(child['@label'], child['@ID']).parent(signature)
        signature.add_child(sig)
        remaining_list = populate_signature(sig, remaining_list)
    return remaining_list


def populate_fields(signature, field_list):
    contained_list = [field for field in field_list if '@parentID' in field and field['@parentID'] == signature.id()]
    remaining_list = list_diff(field_list, contained_list)
    for contained in contained_list:
        field = Field.from_ordered_dict(contained)
        signature.add_child(field)
    for child in signature.children():
        remaining_list = populate_fields(child, remaining_list)
    return remaining_list


def recursive_print(signature, depth=0):
    print(' '*depth, signature)
    for field in signature.fields():
        print(' '*(2+depth), field)
    for child in signature.children():
        recursive_print(child, depth+2)


# Find the univ signature
univ = get_signature('univ')
populate_signature(univ, signatures)
populate_fields(univ, fields)
recursive_print(univ)
# print(univ)
# for kid in univ.children():
#     print('  ', kid)
