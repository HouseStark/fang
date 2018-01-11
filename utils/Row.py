

class Row(dict):

    def __getattr__(self, key): 
        try:
            return self[key]
        except KeyError as k:
            raise AttributeError(k)
    
    def __setattr__(self, key, value): 
        self[key] = value
    
    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError as k:
            raise AttributeError(k)
    
    def __repr__(self):     
        return '<Row ' + dict.__repr__(self) + '>'

if __name__ == '__main__':
    a = Row({'id': '222', 'name': 'wang'})
    print(a.id)
    print(a.name)
    print(a)
    c = ['a', 'b']
    d = ['1', '2']
    print(Row(zip(c, d)))
    e = Row(zip(c, d)) 
    print(e.a)
