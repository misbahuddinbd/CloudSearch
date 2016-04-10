
from NetworkSearch2.interface.unifiedInterface import UnifiedInterface

import cherrypy
import os
import sys
import platform
import json
import psutil
import time
import treeApp
from datetime import datetime
from string import Template

SERVER = platform.uname()[1]
CLOUD_SEARCH_SYSTEM_PATH = os.path.abspath(os.path.dirname(__file__) + '..')
PATH = os.path.abspath(os.path.dirname(__file__)) + '/web'
JSON_DATE_HANDLER = lambda obj: obj.isoformat() if isinstance(obj, datetime) else obj


start = datetime.now()

# STATS functions
def getProcStat( proc, name="Process"):
	info = {'name': name,
		'proc':proc,
		'pid': '-', 
		'status': 'Not running', 
		'cpu_percent': 0, 
		'mem_percent':0
	}
	
	if proc:
		for p in psutil.process_iter():
			
			if proc in p.cmdline or str(proc) + '.py' in p.cmdline:
				info['pid']		= p.pid
				info['status']		= 'Running'
				info['cpu_percent']	= p.get_cpu_percent(interval=1)
				info['mem_percent']	= p.get_memory_percent()
				break

	return info

def getResponse(obj):
	"""Creates a JSON object from a Python object""" 
	return json.dumps(obj, default=JSON_DATE_HANDLER)

class GooglingData():
	"""Class which defines web interface server activity."""
	
	# Help page
	@cherrypy.expose
	def help(self, **kwargs):
		with open(PATH + '/help.html', 'r') as f:
			return f.read()

	# Settings page
	@cherrypy.expose
	def settings(self, **kwargs):
		with open(PATH + '/settings.html', 'r') as f:
			return f.read()

	# Graphical visualization application
	@cherrypy.expose
	def tree(self, ajax=False, tree='Custom', root='', treeType='hypertree', objType='vm', startQuery='server-name=' + SERVER + ' object-type=server', addImages=False, **kwargs):
		model = {'treeId': tree,
			'tree':'false',
			'treeType':treeType,
			'root':	root}

		if tree:
			model['treeId'] = tree
			if tree == 'Custom':
				model['tree'] = getResponse(getattr(treeApp, 'get' + tree + 'Tree')(root=root, objType=objType, addImages=addImages))
				print 111
			else:
				model['tree'] = getResponse(getattr(treeApp, 'get' + tree + 'Tree')(root=root))

# 		elif treeType == 'spacetree':
# 			if ajax:
# 				print "START QUERY - " + startQuery
# 				model['tree'] = getResponse(getDynamicTree(startQuery, linkOnly=True))
# 				return model['tree']
# 				#return model
# 			else:
# 				model['tree'] = getResponse(getDynamicTree(startQuery, numHopsLeft=0))
# 				#model['tree'] = getResponse(getDynamicTree(startQuery, numHopsLeft=1))

		with open(PATH + '/tree.html', 'r') as f:
			s = Template(f.read())
			return s.safe_substitute(model)

	# Interface to configure Cloud Search System
# 	@cherrypy.expose
# 	def stats(self, fun=None, query=None, param=None):
# 		# TODO: need to fix the way it collects information regarding process
# 		model = { 'procs': {	'Sensing Subsystem'	: getProcStat('sensormanager', 'Sensing Subsystem'),
# 					'Query Listener'	: getProcStat('queryListener', 'Query Listener'),},
# 			'server' : SERVER,
# 			}
# 		with open(PATH + '/stats.html', 'r') as f:
# 			s = Template(f.read())
# 			return s.safe_substitute(model)

	# Search Page
	@cherrypy.expose
	def search(self, **kwargs):
		
		return self.index(**kwargs)
	
	@cherrypy.expose
	def index(self, query='', **kwargs):
		
		model = {'query': query}
		with open(PATH + '/search.html', 'r') as f:
			s = Template(f.read())
			return s.safe_substitute(model)

	# For AJAX queries
	@cherrypy.expose
	def ajax(self, fun=None, query=None, param=None, limit=0, approximate=True,tf=5,nr=5,tr=5, **kwargs):

		if approximate == 'false':
			approximate = False
		else:
			approximate = True

		if query:
			t0 = time.time()
			response = {'query': query}
			paremeters = {'rank':None, 'returnRank':True, 'limit':limit , 'isApprox':approximate, 'tf':tf,'nr':nr,'tr':tr}
			
			cs = UnifiedInterface(query, paremeters)
			cs.search()
			response['time'] = cs.time			
			
			response['num_results'] = cs.numResults
			response['results'] = cs.results
			response['mongo'] = cs.dbQuery
			response['parameters'] = cs.parameters   
			
			
			print response
					
			return getResponse(response)


# # During testing
# class Testing:
# 	if len(sys.argv) > 2:
# 		html = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd"><html xmlns="http://www.w3.org/1999/xhtml"><head><meta http-equiv="Content-Type" content="text/html; CHARSET=utf-8"><title>Googling Data in Clouds: TESTING!!</title><link type="text/css" rel="stylesheet" href="/static/index.css"/></head><body><h1 class="error" align="center">Amy is testing &quot;' + sys.argv[2] + '&quot; on system size ' + sys.argv[1] + '<br />Test started at: ' + str(start) +' </h1></body></html>'
# 	else:
# 		html = 'Testing'
# 	# Index Page
# 	@cherrypy.expose
# 	def index(self):
# 		return self.html
# 
# 	# Search Page 
# 	@cherrypy.expose
# 	def search(self, fun=None, query=None, param=None):
# 		return self.index()

if __name__ == "__main__":
	# reference to the class
	page = GooglingData
	
	if len(sys.argv) > 1:
		if sys.argv[1] == 'stop':
			# get processes of web.py
			webps = []
			for p in psutil.process_iter():
				for cmd in p.cmdline:
					if cmd.endswith('web.py') and p.pid != os.getpid():
						webps.append(p)
			# If there is, terminate it
			if webps:
				for p in webps:
					print 'Killing: ' + str(p.pid) + '\t'  + ' '.join(p.cmdline)
					p.kill()
					
		elif sys.argv[1] == 'start':
			#cherrypy.process.servers.check_port('localhost', 80, timeout=1.0)
			print "PATH:\t" + PATH
			print "CLOUD SEARCH PATH:\t" + CLOUD_SEARCH_SYSTEM_PATH
			cherrypy.server.socket_host = '0.0.0.0'
			cherrypy.tree.mount(page(), '/static', config={
				'/': {
					'tools.staticdir.on': True,
					'tools.staticdir.dir': PATH,
				    },
			    })
			cherrypy.quickstart(page())
			
		else: 
			print "Usage: web.py {start,stop}"
			
	else: 
		print "Usage: web.py {start,stop}"
