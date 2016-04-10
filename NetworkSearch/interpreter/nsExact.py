import lex
import yacc
from sys import path

class nsExactClass():
    
    def __init__(self):
        self.parser = self.get_parser()
        
    def get_parser(self):
        reserved = {
                    'or' : 'OR' 
                   }
        # List of token names
        tokens = [
          'KEYWORD',    
          'IP',
          'FLOW', 
          'INT',
          'FLOAT',    
          'EQ',
          'GT',
          'LT',  
          'LPAREN',
          'RPAREN',
        ] + list(reserved.values())
        
        # Regular expression rules for simple tokens
        t_EQ   = r'[=]'
        t_GT   = r'>'
        t_LT   = r'<'    
        t_LPAREN  = r'\('
        t_RPAREN  = r'\)'
        
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
            t.value = round(t.value,2) 
            return t
        
        def t_INT(t):
            r'\d+'
            t.value = int(t.value)
            return t     
    
        def t_KEYWORD(t):
            r'[a-zA-Z][a-zA-Z0-9\-\:]*'
            t.type = reserved.get(t.value.lower(),'KEYWORD')
            return t
    
        # A string containing ignored characters (spaces and tabs)
        t_ignore  = ' \t'
        
        # Error handling rule
        def t_error(t):
            print "Illegal character '%s'" % t.value[0]
            t.lexer.skip(1)
        
        # Build the lexer from my environment and return it    
        
        lex.lex()
        
        def p_query_unary_paren(p):
            ' query : LPAREN query RPAREN '
            p[0]=p[2]
            #print 'rule>> query : LPAREN query RPAREN>> ' + str(p[0])
        
        def p_query_or(p):
            ''' query : query OR query
            '''
            
            operation = '$or'
            #flatten nested if possible
            temp_list = []
            if p[1].has_key(operation) : temp_list.extend(p[1][operation])
            else: temp_list.append(p[1])
            if p[3].has_key(operation) : temp_list.extend(p[3][operation])     
            else: temp_list.append(p[3])      
            
            p[0]={operation:temp_list} 
    
        def p_query_and(p):
            ''' query : query query 
            '''
            
            operation = '$and'        
            #flatten nested if possible
            temp_list = []
            if p[1].has_key(operation) : temp_list.extend(p[1][operation])
            else: temp_list.append(p[1])
            if p[2].has_key(operation) : temp_list.extend(p[2][operation])     
            else: temp_list.append(p[2])      
            
            p[0]={operation:temp_list}         
          
        def p_query_token(p):
            'query : token'
            p[0]=p[1]
            #print ' rule>> query : token >> ' + str(p[0])
            
        def p_token_id(p):
            'token : id'
            p[0]={'content':p[1]}
        
        
        def p_token_attr_val(p):
            'token : attr_val'
            p[0]=p[1]
                
        def p_attr_val(p):
            '''
            attr_val : id EQ id 
                    | id GT id   
                    | id LT id
            '''
            if p[2]=='>':
                p[0]={p[1]:{'$gt':p[3]}}
            elif p[2]=='<':
                p[0]={p[1]:{'$lt':p[3]}}
            else:
                p[0]={p[1]:p[3]}   
                    
        def p_id(p):
            ''' 
            id : INT
                  | IP 
                  | FLOW
                  | FLOAT 
            '''
            #print p[1]
            p[0] = p[1]
            #print p[0]
            
        def p_id_keyword(p):
            ''' 
            id : KEYWORD
            '''
            #print p[1]
            p[0] = p[1].lower()
            #print p[0]       
        # Error rule for syntax errors
        def p_error(p):
            print "Syntax error in input!"
            #print p
        
        parser = yacc.yacc(debugfile=str(path[0])+'/parser.out',tabmodule=str(path[0])+'/parsetab')
    
        return parser

    def translate(self,raw_query):
        """ string -> dict 
        
        parse raw query to a specific query according to the defined lex&yacc
        """
        return self.parser.parse(raw_query)
