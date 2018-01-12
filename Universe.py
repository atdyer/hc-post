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

    def __init__(self, label, uid):

        super().__init__(label, uid)

    def __repr__(self):

        return '<Sig> ' + self.label()

    def fields(self):

        return [child for child in self.children() if isinstance(child, Field)]

    def signatures(self):

        return [child for child in self.children() if isinstance(child, Signature)]


class Field(Item):

    def __init__(self, label, uid, types):

        super().__init__(label, uid)
        self._types = types

    def __repr__(self):

        return '<Field> ' + self.label() + ': ' + ' -> '.join([str(t) for t in self.types()])

    def types(self):

        return self._types


def list_diff(a, b):
    return [item for item in a if item not in b]


def populate_signature(signature, signature_list):
    child_list = [sig for sig in signature_list if '@parentID' in sig and sig['@parentID'] == signature.id()]
    remaining_list = list_diff(signature_list, child_list)
    for child in child_list:
        sig = Signature(child['@label'], child['@ID']).parent(signature)
        signature.add_child(sig)
        remaining_list = populate_signature(sig, remaining_list)
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
        instance = data['alloy']['instance']
        signatures = instance['sig']
        fields = instance['field']

        # Find the univ signature
        self._univ = None
        for sig in signatures:
            if sig['@label'] == 'univ':
                self._univ = Signature('univ', sig['@ID'])

        # Build the signature tree recursively
        populate_signature(self._univ, signatures)

        # Parse and add all fields to universe
        for field in fields:
            parent = self._univ.find_by_id(field['@parentID'])
            types = list(map(lambda x: self._univ.find_by_id(x['@ID']), field['types']['type']))
            f = Field(field['@label'], field['@ID'], types).parent(parent)
            parent.add_child(f)

    def print(self):

        self._univ.print()

test = Universe('data/ex1.xml')
test.print()

