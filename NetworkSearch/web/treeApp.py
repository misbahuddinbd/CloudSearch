import itertools
import copy
from NetworkSearch2.interface import unifiedInterface


# Application trees
DEFAULT_TREE = {'id'	: 'root',
		'name'	: 'LCN Cloud',
		'data'	: {'object-type':''},
		'children':[],
	}
APP_ATTRS = {
	'customer'	: ['object-type', 'object-name', 'application', 'email'],
	'image'	 	: ['object-type', 'object-name', 'status', 'created-at', 'disk-format', 'vm'],
	'server'	: ['object-type', 'object-name', 'linux-distribution', 'cpu-cores', 'memory', 'uptime'],
	'vm'		: ['object-type', 'object-name', 'cpu-cores', 'memory', 'uptime', 'server','ip-address'],
	'flow'		: ['object-type', 'object-name', 'src-ip','src-port','dst-ip','dst-port','start-time','bytes','packets']
	}
# 
# def getServerVMCustTree(root=''):
# 	"""Creates the Jit Hypertree with Servers, VMs and Customer."""
# 	return getCustomTree(root=root, objType='server')
# 
# def getServerVMImageTree(root=''):
# 	"""Creates the Jit Hypertree with Servers, VMs, Customers and Images."""
# 	return getCustomTree(root=root, objType='server', addImages=True)
# 
# def getCustVMServerTree(root=''):
# 	"""Creates the Jit Hypertree with Customers, VMs and Servers."""
# 	return getCustomTree(root=root, objType='customer')
# 
# def getCustVMImageTree(root=''):
# 	"""Creates the Jit Hypertree with Customers, VMs, Servers and Images."""
# 	return getCustomTree(root=root, objType='customer', addImages=True)

def getCustomTree(root='', objType='vm', addImages=False):
	"""Creates a Jit Hypertree with specified object type, focus and Servers, VMs, Customers, and optionally Images."""
	objsByName = dict((o['object-name'], o) for o in unifiedInterface.query('project (' + ' '.join(set(itertools.chain(*APP_ATTRS.values()))) + ', object-type=server or object-type=customer)'))
	print 1

	# If images should be included as well
	if (addImages):
		images = unifiedInterface.query('project (' + ' '.join(APP_ATTRS['image'])+' , object-type=image)')
		imagesByName = dict((i['object-name'], i) for i in images)
		imageNamesByVM = dict((v, i['object-name']) for i in images for v in i['vm'])

	tree = copy.deepcopy(DEFAULT_TREE)
	if root != '':
		objs = unifiedInterface.query('project (' + ' '.join(APP_ATTRS[objType])+ ' , object-type=' + objType + ' ' + root + ")")
	else:
		objs = unifiedInterface.query('project (' + ' '.join(APP_ATTRS[objType])+ ' , object-type=' + objType + ')')
	for o in objs:
		oneTree = createBranch(o)
		if objType == 'vm':
# 			oneTree['children'] = [createBranch(objsByName[o[nameAttr]]) for nameAttr in o.keys() if '-name' in nameAttr and nameAttr !='object-name'] 
# 			if (addImages):
# 				try: oneTree['children'].append(createBranch(imagesByName[imageNamesByVM[o['vm-name']]]))
# 				except KeyError: pass
			
# 			flows = unifiedInterface.query("-project (" + ",".join(APP_ATTRS['flow']) +  ") (" + '+'.join(o['ip-address']) + ")")
# 			for flow in flows:
# 				fTree = createBranch(flow)
# 				oneTree['children'].append(fTree)
			print " ".join(APP_ATTRS['server'])+ o['server']
			servers = unifiedInterface.query("project (" + " ".join(APP_ATTRS['server']) +  " , object-type=server object-name=" + o['server'] + ")")
			for server in servers:
				sTree = createBranch(server)
				oneTree['children'].append(sTree)
				
			try:
				cus = unifiedInterface.query("(object-type=customer) link(customer , image "+ o['object-name'] +")")[0]
				oneTree['children'].append(createBranch(cus))
			except IndexError:
				pass 		
						
		elif objType == 'customer':
# 			vms = unifiedInterface.query("-project (" + ",".join(APP_ATTRS['vm']) +") (object-type=vm + object-name=" + o['object-name'] + ")")
# 			for v in vms:
# 				vTree = createBranch(v)
# 				vTree['children'].append(createBranch(objsByName[v['server-name']]))
# 				if (addImages):
# 					try: vTree['children'].append(createBranch(imagesByName[imageNamesByVM[v['vm-name']]]))
# 					except KeyError: pass
# 				oneTree['children'].append(vTree)
			pass
		elif objType == 'server':
			vms = unifiedInterface.query("project (" + " ".join(APP_ATTRS['vm']) +  ", object-type=vm server=" + o['object-name'] + ")")
			for v in vms:
				vTree = createBranch(v)
				try:
					cus = unifiedInterface.query("(object-type=customer) link(customer , image "+ v['object-name'] +")")[0]
					vTree['children'].append(createBranch(cus))
				except IndexError:
					pass 

#  				if (addImages):
#  					try: vTree['children'].append(createBranch(imagesByName[imageNamesByVM[v['vm-name']]]))
#  					except KeyError: pass
				
# 			( object-type=customer) link_(customer) (image + ns:instance-00027a28)
				oneTree['children'].append(vTree)
			pass
	
		if len(objs) == 1:
			return oneTree
		else:
			tree['children'].append(oneTree)

	return tree

def createBranch(obj):
	"""Creates an object tree branch for JIT tree animations."""
	u_attr = 'object-name'
	tree = {	'id'	: obj[u_attr] ,# + '_' + str(random.randint(0, sys.maxint)),
			'name'	: obj[u_attr],
			'data'	: obj,
			'children': []
		}
	return tree
