import xmltodict


class Atom:

    def __init__(self, label):

        self._label = label

    def __repr__(self):

        return self.label() + ' <Atom>'

    def __eq__(self, other):

        return isinstance(self, type(other)) and self.label() == other.label()

    def label(self):

        return self._label


class Vertex(Atom):

    def __init__(self, label):

        super().__init__(label)
        self._neighbors = set()

    def add_neighbor(self, neighbor):

        self._neighbors.add(neighbor)


class Instance:

    def __init__(self, file):

        try:

            with open(file) as f:

                self.data = xmltodict.parse(f.read())

        except IOError:

            print('Error opening file', file)
            exit()

        self._fields = self.data['alloy']['instance']['field']
        self._sigs = self.data['alloy']['instance']['sig']
        self._skolem = self.data['alloy']['instance']['skolem']

        self._vertices = None
        self._edges = None

    def atoms(self, sig_label):

        _sig = self.signature(sig_label)

        _atoms = _sig['atom'] if 'atom' in _sig else []
        _atoms = [_atoms] if type(_atoms) is not list else _atoms

        return list(map(lambda a: Atom(a['@label']), _atoms))

    def tuples(self, field_label):

        _field = self.field(field_label)
        _tuples = _field['tuple'] if 'tuple' in _field else []
        _tuples = [_tuples] if type(_tuples) is not list else _tuples
        for t in _tuples:
            atom = t['atom']
            for a in atom:
                print(a['@label'])
            # print(len(atom))

        return list(map(lambda t: tuple(Atom(a['@label']) for a in t), _tuples))

    def signature(self, name):

        for sig in self._sigs:
            if sig['@label'] == name:
                return sig

    def field(self, name):

        for field in self._fields:
            if field['@label'] == name:
                return field

    def set_connectivity_signatures(self, vertex_sig, edge_sig):

        # Attempt to find the vertices
        parent_sig = self.signature('this/' + vertex_sig)

        if '@ID' in parent_sig:
            parent_id = parent_sig['@ID']
            self._vertices = self._filter_sigs('@parentID', parent_id)
            # for v in self._vertices:
            #     print(Instance._atoms(v))

        # Attempt to find the edges (is this always skolem?)
        if self._skolem['@label'] == '$this/' + edge_sig:
            self._edges = Instance._atom_tuples(self._skolem)

        return self

    def _filter_sigs(self, key, value):
        # Returns only the signatures that have the matching key, value pair
        return list(filter(lambda sig: key in sig and sig[key] == value, self._sigs))

    @staticmethod
    def _atom_tuples(item):
        # Extracts all tuples of atoms from an item
        result = set()
        if 'tuple' in item:
            for t in item['tuple']:
                result.add(tuple(x['@label'] for x in t['atom']))
        return result

    # @staticmethod
    # def _atoms(item):
    #     result = set()
    #     atom_dict = item['atom']
    #     print(atom_dict)
    #     for key in atom_dict:
    #         print(key)
    #         result.add(atom_dict[key]['@label'])
    #     return result
    #     # print(item['atom'].keys())
    #     # for a in item['atom']:
    #     #     print(a['@label'])
    #     # return item['atom']['@label']


test = Instance('./data/ex1.xml')
test.set_connectivity_signatures('Vertex', 'edges')
# print('State:', test.atoms('this/State'))
# print('A:', test.atoms('this/A'))
print('pc:', test.tuples('pc'))

# for v in test._vertices:
#     print('Vertex:', v)
# for e in test._edges:
#     print('Edge:', e)
