
import xmltodict

with open('Untitled.xml') as fd:
    doc = xmltodict.parse(fd.read())


def get_sig(name):
    sigs = doc['alloy']['instance']['sig']
    result = set()
    for d in sigs:
        attr = d['@label']
        if attr == name:
            for t in d['atom']:
                result.add(tuple([t['@label']]))
    return result


def get_field(name):
    fields = doc['alloy']['instance']['field']
    result = set()
    for d in fields:
        attr = d['@label']
        if attr == name:
            for t in d['tuple']:
                result.add(tuple([x['@label'] for x in t['atom']]))
    return result


def dot(a, b):
    return set([x[:-1] + y[1:] for x in a for y in b if x[-1] == y[0]])


# take a string and return a set with tuple that contains it
def singleton(s):
    return set([(s,)])


# inverse of singleton
def atom(s):
    return next(iter(s))[0]


def unary(s):
    return {(x,) for x in s}


# curried shorthand form for end[x, y].s.a
def endf(x, y, s=None, a=None):
    temp = dot(singleton(y), dot(singleton(x), end))
    if s is not None:
        temp = dot(temp, singleton(s))
        if a is not None:
            temp = dot(temp, a)
    return temp


def init(s):
    return all([endf(x, y, s, m) == singleton('Moment$1') and
                endf(x, y, s, d) == singleton('False$0') and
                endf(x, y, s, c) == singleton('False$0')
                for x, y in edges])


def balanced(v, s):
    return all([endf(x, y, s, m) == singleton('Moment$0')
                for x, y in edges if x == v])


def pending(v, s):
    return pending_distribution(v, s).union(pending_carryover(v, s))


def pending_distribution(v, s):
    return {(x, y)
            for x, y in edges
            if v == x and endf(x, y, s, d) == singleton('True$0')}


def pending_carryover(v, s):
    return {(x, y)
            for x, y in edges
            if v == y and endf(x, y, s, c) == singleton('True$0')}


def release(v, s, s2):
    return not balanced(v, s) and len(pending(v, s)) == 0 and \
        all([(not v == x or
              (endf(x, y, s2, m) == singleton('Moment$1') and
               endf(x, y, s2, d) == singleton('True$0') and
               endf(x, y, s2, c) == endf(x, y, s, c))) and \
             (not v == y or
              (endf(x, y, s2, m) == endf(x, y, s, m) and
               endf(x, y, s2, d) == endf(x, y, s, d) and
               endf(x, y, s2, c) == singleton('True$0'))) and \
             ((v == x) or (v == y) or
              unchanged(endf(x, y, s), endf(x, y, s2)))
             for x, y in edges])


def mo_next(mo):
    return mo_incr(mo, 1)


def mo_prev(mo):
    return mo_incr(mo, -1)


def mo_incr(mo, by):
    return singleton('Moment$%s' % (int(atom(mo)[7]) + by))


def distribute(u, v, s, s2):
    return endf(u, v, s, d) == singleton('True$0') and \
        all([(not (x == u and y == v) or
              (endf(x, y, s2, m) == mo_prev(endf(x, y, s, m)) and
               endf(x, y, s2, d) == singleton('False$0') and
               endf(x, y, s2, c) == endf(x, y, s, c))) and \
             ((x == u and y == v) or
              unchanged(endf(x, y, s), endf(x, y, s2)))
             for x, y in edges])


def carryover(u, v, s, s2):
    return endf(u, v, s, c) == singleton('True$0') and \
        all([(not (x == u and y == v) or
              (endf(x, y, s2, m) == mo_next(endf(x, y, s, m)) and
               endf(x, y, s2, d) == endf(x, y, s, d) and
               endf(x, y, s2, c) == singleton('False$0'))) and \
             ((x == u and y == v) or
              unchanged(endf(x, y, s), endf(x, y, s2)))
             for x, y in edges])


def unchanged(e, e2):
    return \
        dot(e2, m) == dot(e, m) and \
        dot(e2, d) == dot(e, d) and \
        dot(e2, c) == dot(e, c)
        

# Global state ... retrieve signature atoms and relations
State = get_sig('this/State')
End = get_sig('this/End')
Moment = get_sig('this/Moment')

end = get_field('end')
m = get_field('m')
d = get_field('d')
c = get_field('c')

edges = set([(u, v) for u, v, e, s in end])

# easier to extract from edges than to look through sub-signatures in doc
Vertex = set([(x,) for x, y in edges])


def echo():
    print('State = %s\n' % State)
    print('End = %s\n' % End)
    print('Moment = %s\n' % Moment)
    print('Vertex = %s\n' % Vertex)
    print('end = %s\n' % end)
    print('m = %s\n' % m)
    print('d = %s\n' % d)
    print('c = %s\n' % c)
    print('edges = %s\n' % edges)


def main():
    xy_pairs = sorted(list(edges))
    states = sorted(list(State))
    print('    ', end='')
    for x, y in xy_pairs:
        print(x[0] + y[0], end='  ')
    print()
    n = len(states)
    for i in range(n):
        s = states[i][0]
        print(s[-1], end=': ')
        for x, y in xy_pairs:
            print(atom(endf(x, y, s, m))[-1], end='')
            print(atom(endf(x, y, s, d))[0], end='')
            print(atom(endf(x, y, s, c))[0], end=' ')
        print()
        if i + 1 < n:
            s2 = states[i + 1][0]
            for v in Vertex:
                if release(v[0], s, s2):
                    print('%srelease[%s, %s, %s]' %
                          (' '*20, v[0][0], s[-1], s2[-1]))
            for x, y in xy_pairs:
                if distribute(x, y, s, s2):
                    print('%sdistribute[%s, %s, %s, %s]' %
                          (' '*20, x[0], y[0], s[-1], s2[-1]))
                if carryover(x, y, s, s2):
                    print('%scarryover[%s, %s, %s, %s]' %
                          (' '*20, x[0], y[0], s[-1], s2[-1]))


if __name__=='__main__':
    # echo()
    main()
