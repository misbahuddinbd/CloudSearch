import nsExact
#import nsApprox
import nsApprox
import re

# preload interpreter
nsApproxObject = nsApprox.nsApproxClass()
nsExactObject = nsExact.nsExactClass()

def nsInterface(sq,isUserExact):
    
    flags = {}
    match_query,project_query,aggr_query,group_list,pass_one_query,link_attributes,pass_two_query = None,None,None,None,None,None,None
    
    # LINK query interpreter and generator
    # takes queries of expression: link(query) or link_(attribute_list)(query) 
    # takes queries of expression: (query) + link(query) or (query) + link_(attribute_list)(query) 
    
    if 'link' in sq:
        # variable that holds flag for link queries
        link_all = 1
        flags['link']=1 
        
        link_segment = re.search('([\w\-\.\:\s=<>\(\)]*)link\s*\(([\w\-\s]*),([\w\-\.\:\s=<>\(\)]*)\)([\w\-\.\:\s=<>\(\)]*)',sq)
#         print link_segment.group(0) # all groups
#         print link_segment.group(1) # a query statement in front of link()
#         print link_segment.group(2) # attribute for linking
#         print link_segment.group(3) # a query statement inside link function
#         print link_segment.group(4) # a query statement in the back of link()  
                
        # Regex matched to this form '<q1> link( attribute , query statement) <q3>'
        if link_segment:
            
            link_attributes_segment = link_segment.group(2)
            pass_one_query_segment = link_segment.group(3)
            pass_two_query_segment = link_segment.group(1) + link_segment.group(4)
            
            # link attributes
            link_attributes = {}   
            for attr in link_attributes_segment.split():
                    link_attributes[attr]=1
                
            link_all = 0
        # link all attributes 
        else:
            link_segment = re.search('([\w\-\.\:\s=<>\(\)]*)link\s*\(([\w\-\.\:\s=<>\(\)]*)\)([\w\-\.\:\s=<>\(\)]*)',sq)
#             print link_segment.group(0) # all groups
#             print link_segment.group(1) # a query statement in front of link()
#             print link_segment.group(2) # a query statement inside link function
#             print link_segment.group(3) # a query statement in the back of link()  

            pass_one_query_segment = link_segment.group(2)
            pass_two_query_segment = link_segment.group(1) + link_segment.group(3)            

        # pass one query
        pass_one_query = nsExactObject.translate(pass_one_query_segment)
        
        pass_two_query = nsExactObject.translate(pass_two_query_segment)
        
        flags['link_all']=link_all
            
#         # dictionary of expression parsing rules for link queries
#         parsing_rules={}
#         parsing_rules['link_segment_with_attributes']='link_( \( \s* [\w\-]+ (,\s*[\w\-]+)* \s* \) ) ( \s* \( \s* [\w\:\-><=.+|\s]+ \s* \) )'
#         parsing_rules['link_segment_without_attributes']='link\s*(\(\s*[\w\:\-><=.+|\s]+\s*\))'
#         parsing_rules['link_attributes']='[\w]+[\w\-]+'
#         parsing_rules['pass_two_query']='\(\s*[\w\:\-><=.+|\s]+\s*\)'
#  
#  
#          
#         # interpret query that takes linking attributes
#          
#         if 'link_' in sq:
#                  
#                 link_segment = re.search(parsing_rules['link_segment_with_attributes'],sq)
#                 print 'link segment: '+str(link_segment.group(0))
#                  
#                 link_attributes_segment = link_segment.group(1)                
#                 link_attributes = {}   
#                  
#                 for p in link_attributes_segment.split(','):
#                     link_attributes[re.search(parsing_rules['link_attributes'],p).group(0)]=1
#                 #print 'link attributes: '+str(link_attributes)
#                 pass_one_query = nsExact.nsExactMatch(link_segment.group(3))  
#                 link_all = 0
#                 #print 'pass one query: '+str(pass_one_query)
#         else:        
#                 link_segment = re.search(parsing_rules['link_segment_without_attributes'],sq)
#                 #print 'pass_one_segment: '+str(link_segment.group(0))
#                  
#                 pass_one_query = nsExact.nsExactMatch(link_segment.group(1))  
#                 #print 'pass_one_query: '+str(pass_one_query)
#  
#              
#         if link_segment.start() == 0:
#             pass_two_segment = sq[link_segment.end()+1:len(sq)]
#         else:            
#             pass_two_segment = sq[0:link_segment.start()-1]
#         #print 'pass_two_segment: '+str(pass_two_segment)
#          
#          
#         if len(pass_two_segment) != 0:
#             pass_two_segment = re.search(parsing_rules['pass_two_query'],pass_two_segment).group(0)
#             #print 'pass_two_segment: '+str(pass_two_segment)
#          
#             pass_two_query = nsExact.nsExactMatch(pass_two_segment)
#             #print 'Pass Two Query: '+str(pass_two_query)


    # AGGREGATION query interpreter and generator
    # takes queries of expression: f1(attr1), ..., f(attrn) (query) or f1(attr1), ..., f(attrn) group(attr1, ..., attrm) (query) 
         
    elif 'sum' in sq or 'count' in sq or 'max' in sq or 'min' in sq or 'count' in sq:
            
        if 'group' in sq:
            
            # no longer supported
            pass
#             aggr_group_segment = re.search('(\s*(\w+\(\s*[\w\-]+\s*\)\s*,*\s*)+)\s*(group\s*\(\s*(\s*[\w\-]+\s*,*\s*)+\s*\))',sq)
#             #print 'aggr_group_segment: '+str(aggr_group_segment.group(0))
#             
#             aggr_segment = aggr_group_segment.group(1)
#             group_segment = aggr_group_segment.group(3)
#             #print aggr_segment
#             #print group_segment
#         
#             group_segment = re.search('(\s*group\s*)(\(\s*([\w\-]+(\s*,\s*[\w\-]+\s*)*)\s*\))',group_segment).group(3)
#             #print group_segment
#      
#             project_query={}
#             group_list = []
#             
#             for g in group_segment.split(','):
#                 group_item = re.search('[\w\-]+',g).group(0)
#                 group_list.append(group_item)
#                 project_query[group_item]=1
#             #print "Group Query: "+str(group_list)
#             
#             if aggr_group_segment.start() == 0:
#                 match_segment = sq[aggr_group_segment.end():len(sq)]
#             else:
#                 match_segment = sq[0:aggr_group_segment.start()]
#             #print 'match segment: '+str(match_segment)
#             # generate match query in MongoDB syntax
#             
#             match_query = nsExact.nsExactMatch(match_segment)
#             #print 'Match Query: '+str(match_query)
#  
#             aggr_segment = re.search('(\s*\w+\s*\(\s*[\w\-]+\s*\)\s*,*\s*)+\s*',aggr_segment).group(0)
#             function_list = []
#             argument_list = []
#      
#             for a in aggr_segment.split(','):
#                 aggr_items = re.search('(\w+)(\([\w\-]+\))',a)
#                 function_list.append(aggr_items.group(1))
#                 argument_item = re.search('[\w\-]+',aggr_items.group(2)).group(0)
#                 argument_list.append(argument_item)
#                 project_query[argument_item]=1
#             aggr_query = zip(function_list,argument_list)
#             #print 'Projection Query: '+str(project_query)
#             #print 'Aggregation Query: '+str(aggr_query)
#         
#             flags['aggregation']=1
#             flags['group']=1
        
        else:        
            aggr_segment = re.search('(\w*)\s*\(([\w\-\s]*),([\w\-\.\:\s=<>\(\)]*)\)',sq)
            
            # Regex matched to this form 'function( attribute , query statement)'
            if aggr_segment:
            
                # aggr_segment.group(1) is function name
                function_name_group = aggr_segment.group(1)
                # aggr_segment.group(2) is aggregation attributes
                aggr_attrbute_group = aggr_segment.group(2)
                # aggr_segment.group(3) is projection query
                aggr_query_group = aggr_segment.group(3)
            
            # synthetic sugar for special case without an attribute. add 'object-name' as an attribute
            else:
                aggr_segment = re.search('(\w*)\s*\(([\w\-\.\:\s=<>\(\)]*)\)',sq)
                
                # aggr_segment.group(1) is function name
                function_name_group = aggr_segment.group(1)
                # add 'object-name' to aggregation attributes
                aggr_attrbute_group = "object-name"
                # aggr_segment.group(2) is projection query
                aggr_query_group = aggr_segment.group(2)           
            
            project_query ={}
            function_list = []
            argument_list = []
            for attr in aggr_attrbute_group.split():
                function_list.append(function_name_group)
                argument_list.append(attr)
                project_query[attr]=1
                
            aggr_query = zip(function_list,argument_list)
            
            # generate match query in MongoDB syntax          
            match_query = nsExactObject.translate(aggr_query_group)

            
            flags['aggregation']=1
            
    # if the query is projection query
    
    elif 'project' in sq:
        
        # identify project segment in the search query
        project_segment = re.search('project\s*\(([\w\-\s]*),([\w\-\.\:\s=<>\(\)]*)\)',sq)
        

        # project_segment.group(1) is projection attributes
        project_attrbute_group = project_segment.group(1)
        # project_segment.group(2) is projection query
        project_query_group = project_segment.group(2)
        
        
        # project query (list of project attributes)
        project_query = {}
        for attr in project_attrbute_group.split():
            project_query[attr]=1
        
        # generate match query in MongoDB syntax
        match_query = nsExactObject.translate(project_query_group)
        
        flags['projection']=1
    
    elif '>' in sq or '<' in sq or isUserExact:
        # mongodb match query generation
        match_query = nsExactObject.translate(sq)
        #print 'Match Query: '+str(match_query)
        flags['exact']=1
    else:
        match_query = nsApproxObject.translate(sq)
        #print 'Match Query: '+str(match_query)
        flags['approximate']=1
        
        
    return match_query,project_query,aggr_query,group_list,pass_one_query,link_attributes,pass_two_query,flags


# from pprint import pformat
# 
# print pformat(nsInterface('vw link (a     b, ( c) (d=f or g>3)) or xy',True))
#print pformat(nsInterface('link (a     b, ( c) (d=f or g>3)) or xy',True))
#print pformat(nsInterface('vw link (a     b, ( c) (d=f or g>3))',True))


# from pprint import pformat
#   
# test_list = ["a",
#              "a + b + c + f  + d",
#              "a + b + c + f  | d",
#              "a + b + c | f  | d",
#              "a + b | c | f  | d",
#              "a | b | c | f  | d",
#              "(a + b) | c + f + d",
#              "(a + b) | (c + f ) + d",
#              "(a + b) + (c | f ) + d",
#              "(a + b) + (c + f ) | d",
#              "(a | b) | (c | f ) + d",
#              "(a + b) | (c + f ) | d",
#              "a + b>4 | c | f  | d",
#              "a | b | c<2 | f=wer  | d",
#              "(a + b=asd) | c + f=34 + d",
#              "(a + b) | (c=234 + f ) + d",
#              ]
# for item in test_list:
#     print item
#     print pformat(nsInterface(item,False)[0])
