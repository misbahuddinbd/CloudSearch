// Classes to use for indicating a bad response
var xClasses = ['error','nonresponsive']

// Add a CSS class
function addClass(id, clazz) {
	if(Object.prototype.toString.call(id) === '[object Array]' ) {
	   for (i in id)
		addClass(id[i], clazz)
		
	}
	else if (document.getElementById(id).className.indexOf(clazz) < 0) {
		if (document.getElementById(id)) document.getElementById(id).className += ' ' + clazz
	}
}

// Remove a CSS class
function removeClass(id, clazz) {
	if(Object.prototype.toString.call(id) === '[object Array]' ) {
	   for (i in id)
		removeClass(id[i], clazz)
		
	}
	else if (Object.prototype.toString.call(clazz) === '[object Array]' ) {
	   for (i in clazz)
		removeClass(id, clazz[i])
		
	}
	else if (document.getElementById(id)) {
		var re = new RegExp('\s*' + clazz, 'g')
		document.getElementById(id).className = document.getElementById(id).className.replace(re,'')	
	}
}

// Updates on the numbers table
function updateNumList(id, functionName) {
	ajaxRequest([id,id + 'Count'], 'fun', functionName, updateNumListResp)	
}
function updateNumListResp(id, functionName, text) {
	if (text) {
		obj = eval(text)
		if (functionName == 'getAvgVMCount') {
			if (document.getElementById(id)) document.getElementById(id).innerHTML = obj
		} else {
			idc = id + 'Count'
			if (document.getElementById(id)) document.getElementById(id).innerHTML = obj.join(", ");
			if (document.getElementById(idc)) document.getElementById(idc).innerHTML = obj.length;
		}	
	}	
}

// Broad AJAX function
function ajaxRequest(id, queryFun, param, resp) {
	var ajax = new XMLHttpRequest();
	ajax.onreadystatechange = function() {
		if (ajax.readyState == 4) {
			// Remove any error classes
			removeClass(id, xClasses)

			// Update text / CSS
			if (ajax.status == 200) {
				if (Object.prototype.toString.call(id) === '[object Array]' ) {
					id = id[0]
				}
				if (resp && param)	resp(id, param, ajax.responseText)
				else if (resp)		resp(id, ajax.responseText)
			} else {
			
				if (ajax.status == 500) {
					clazz = 'error'
				} else {
					clazz = 'nonresponsive'
				}

				addClass(id, clazz)
			}
		}
	}

	paramStr = ''
	if (Object.prototype.toString.call(queryFun) === '[object Array]' ) {
		for (i in queryFun){
			paramStr += queryFun[i] + '=' + URLencode(param[i]) + '&'
		}
	} else if (param) {
		paramStr = queryFun + '=' + URLencode(param)
	} else {
		paramStr = 'fun=' + queryFun
	}
	console.log(paramStr)
	ajax.open('GET', '/ajax?' + paramStr,true);
	ajax.send();
}
function URLencode(param) {
	var safe = encodeURI(param)
	safe = safe.replace(/\+/g,'%2B')
	return safe
}

// Get a snapshot of an object via AJAX
function snapshot() {
	type = document.getElementById('typeSelect').options[typeSelect.selectedIndex].value
	id = document.getElementById('idSelect').options[document.getElementById('idSelect').selectedIndex].value
	console.log(type + ', ' + id)
	if (type == 'vm') { 
		ajaxRequest(['snapshotResults'], ['query','rank'], ['vm-name=' + id, ''], snapshotResp)
	} else {
		ajaxRequest(['snapshotResults', type + 'Select'], ['query', 'rank'], 
			['object-type=' + type + ' ' + type + '-name=' + id, ''], snapshotResp)
	}
}
function snapshotResp(id, fun, resp) {
	var items = JSON.parse(resp)
	if (items) {	
		html = objectResp(items.results, id)
	}
}

// Update the options of the idSelect box to show IDs of a given type
function switchIds(typeSelect) {
	html = ''
	ids = names[typeSelect.options[typeSelect.selectedIndex].value]
	for (i in ids) {
		html += '<option>' + ids[i] + '</option>'
	}
	document.getElementById('idSelect').innerHTML = html

	// Update the snapshot to reflect the new type
	snapshot()
}

// Initial the id and type select boxes and show a sample snapshot
function initSnapshot() {
	typeSelect = document.getElementById('typeSelect')
	html = ''
	for (n in names) {
		html += '<option>' + n + '</option>'
	}
	typeSelect.innerHTML = html

	switchIds(typeSelect)
}

// Create the server section
function initServers() {
	html = '<h2>VMs per Server</h2><table>'
	for (i in names['server']) {
		j = names['server'][i]
		html += '<tr><td>' + j + '</td><td id="' + i + 'Count">' + serverVMs[j].length + '</td><td id="' 
			+ j  + '">' + serverVMs[j].join(", ") + '</td><td><button onclick="javascript:updateServer(\''
			+ j + '\')">update</button></td></tr>'
	}
	html += '</table>'
	document.getElementById('servers').innerHTML = html
	document.getElementById('servers').style.display = 'block'
	
}

// Update information about a given server
function updateServer(server) {
	ajaxRequest([server,server + 'Count'] , ['fun', 'param'], ['getServerVMNameList',server], updateNumListResp)	
}


// Fill out all of the dynamic information and set reload
function initCloudView() {
	initSnapshot()
	initServers()

	setTimeout("document.location.reload()", 60000)
}
