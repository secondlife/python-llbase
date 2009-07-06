import random
import string
import time

from indra.base import llidl

def random_string():
    s = random.choice(string.ascii_uppercase)
    for i in xrange(1,random.randint(2,11)):
        s += random.choice(string.ascii_lowercase)
    return s

def time_llidl_match(n, k):
    value = llidl.parse_value("[ { name: [ string, string ], size: int }, ... ]")
    
    data_set = []
    for i in xrange(0,n):
        item = []
        for i in xrange(0,k/5):
            n1 = random_string()
            n2 = random_string()
            s = random.randint(100,10000)
            item.append({'name': [ n1, n2 ], 'size': s})
        data_set.append(item)
        
    t = - time.time()
    c = - time.clock()
    
    for item in data_set:
        value.match(item, raises=True)
    
    c += time.clock()
    t += time.time()
    
    return (c,t)


def simple_llidl_match():
    (c,t) = time_llidl_match(1000, 100)
    
    print ("matched 1000 items of 100 values each")
    print ("%f process clock, %f wall clock" % (c, t))


def grid():
    trial_range = xrange(100,1100,100)
    size_range = xrange(0,550,50)
    
    print "trials,%s" % (",".join(["%d items" % d for d in size_range]))
    for n in trial_range:
        cs = []
        for k in size_range:
            (c,t) = time_llidl_match(n,k)
            cs.append(c)
        print "%d,%s" % (n, ','.join(map(str, cs)))
    
if __name__ == '__main__':
    simple_llidl_match()
    #grid()
