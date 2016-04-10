import lex
import yacc
from sys import path

class nsApproxClass():
    
    def __init__(self):
        self.parser = self.get_parser()
        
    def get_parser(self):
        tokens = (
              'KEYWORD',
              'IP',
              'FLOW',
              'INT',
              'FLOAT',
              'EQ',
              'LPAREN',
              'RPAREN',
        )
            
        # Regular expression rules for simple tokens
        t_EQ = r'=' 
        t_LPAREN = r'\('
        t_RPAREN = r'\)'
        t_KEYWORD = r'[\*a-zA-Z][\*a-zA-Z0-9_\-\:]*'
            
        # regex rules that require actions and special handling
            
        def t_FLOW(t):
            r'ns\:(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\:\d+\:(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\:\d+'
            return t
        
        def t_IP(t):
            r'(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)'
            return t
            
        def t_FLOAT(t):
            r'(\d+)\.(\d*)'
            t.value = float(t.value)
            t.value = round(t.value, 2) 
            return t
            
        def t_INT(t):
            r'\d+'
            t.value = int(t.value)
            return t     
            
        # A string containing ignored characters (spaces and tabs)
        t_ignore = ' \t'
            
        # Error handling rule
        def t_error(t):
            print "Illegal character '%s'" % t.value[0]
            t.lexer.skip(1)
            
        # Build the lexer from my environment and return it    
        lex.lex()
        
        def p_query_bin(p):
            '''query : query query
                    | LPAREN query query RPAREN
            '''
            
            if p[1]=='(':
                a,b = p[2], p[3]
            else:
                a,b = p[1], p[2]
            # merge a keywords
            temp_list = []
            if a.has_key('$or') : temp_list.extend(a['$or'])
            else: temp_list.append(a)
            if b.has_key('$or') : temp_list.extend(b['$or'])
            else: temp_list.append(b)
            
            p[0] = {'$or':temp_list}
        
              
        def p_query_token(p):
            ''' query : token
                | LPAREN token RPAREN    
            '''
            if p[1]=='(':
                p[0] = p[2]
            else:
                p[0] = p[1]
                
            if not p[0].has_key('$or'): p[0]={'$or':[p[0]]}
            
        def p_token(p):
            ''' token : id 
                    | val
                    | attr_val '''
            p[0] = {'keyword':p[1]}
            
        def p_attr_val(p):
            '''attr_val : id EQ val 
                    | id EQ id'''
            p[0] = p[1]+':'+str(p[3])   
            
        def p_val(p):
            ''' val : IP 
                    | FLOW    
                    | FLOAT 
                    | INT'''    
            p[0] = p[1]
             
        def p_id(p):
            ' id : KEYWORD '
            p[0] = p[1].lower()
           
        # Error rule for syntax errors
        def p_error(p):
            print "Syntax error in input!"
            
        parser = yacc.yacc(debugfile=str(path[0])+'/parser.out',tabmodule=str(path[0])+'/parsetab')
    
        return parser

    def translate(self,raw_query):
        """ string -> dict 
        
        parse raw query to a specific query according to the defined lex&yacc
        """
        return self.parser.parse(raw_query)


