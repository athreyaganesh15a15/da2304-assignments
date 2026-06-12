class SymbolTable:
    def __init__(self):
        self.class_scope = {}
        self.subroutine_scope = {}
        self.counts = {
            'static': 0,
            'field': 0,
            'arg': 0,
            'var': 0
        }
    
    def reset(self):
        self.subroutine_scope = {}
        self.counts['arg'] = 0
        self.counts['var'] = 0  

    def define(self, name, type, kind):
        if kind in ['static', 'field']:
            self.class_scope[name] = (type, kind, self.counts[kind])
        else:
            self.subroutine_scope[name] = (type, kind, self.counts[kind])
        
        self.counts[kind] += 1
    
    def var_count(self, kind):
        return self.counts[kind]

    def kind_of(self, name):
        if name in self.subroutine_scope:
            return self.subroutine_scope[name][1]
        elif name in self.class_scope:
            return self.class_scope[name][1]
        else:
            return None
    
    def type_of(self, name):
        if name in self.subroutine_scope:
            return self.subroutine_scope[name][0]
        elif name in self.class_scope:
            return self.class_scope[name][0]
        else:
            return None
    
    def index_of(self, name):
        if name in self.subroutine_scope:
            return self.subroutine_scope[name][2]
        elif name in self.class_scope:
            return self.class_scope[name][2]
        else:
            return None