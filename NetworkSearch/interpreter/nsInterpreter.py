'''

 Unfinished ..... Drop it

@author: Misbah Uddin
'''

import lex
import yacc

def nsExactMatch(data):
    # List of token names
    tokens = (
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
      'AND',
      'OR'
    )
    
    # Regular expression rules for simple tokens
    # 
    t_AND = r'\+'
    t_OR = r'\|'
    t_EQ   = r'[=]'
    t_GT   = r'>'
    t_LT   = r'<'    
    t_LPAREN  = r'\('
    t_RPAREN  = r'\)'
    t_KEYWORD = r'[a-zA-Z][a-zA-Z0-9\-\:\.]*'
    
    # simplified tokens
    eight_bit_number = r'(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)'
    port = r'\d+'
    dot = r'\.'
    colon = r'\:'
    ipv4 = dot.join([eight_bit_number]*4)
    flow = colon.join([ipv4,port]*2)

    # regex rules that require actions and special handling
    @lex.TOKEN(flow)   
    def t_FLOW(t):
        return t
    
    @lex.TOKEN(ipv4)
    def t_IP(t):
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
    
    def p_query_binary(p):
        ''' query : query OR query
                | query AND query
                '''
        if p[2]=='+':
            p[0]={'$and':[p[1],p[3]]} 
        else:
            p[0]={'$or':[p[1],p[3]]} 
     
        #print 'rule>> query : query OR query >> ' + str(p[0])
      
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
    
    parser = yacc.yacc()

    return parser.parse(data)

print nsExactMatch('(1.1+b+10.10.11.165:55896:10.10.10.211:7731)|c=10')
print nsExactMatch("2001:6b0:1:12b0:793c:7df:34b2:cccf")