function initHTML() {
	initProcs()
	document.getElementById('dumpColl').onclick = dumpColl
}

function initProcs() {
	
	for (var p in procs) {
		var row = document.createElement('tr')
		row.id = procs[p].proc
		row.innerHTML = getProcInnerHTML(procs[p])
		document.getElementById('procTable').appendChild(row)
	}

}

function getProcInnerHTML(p) {
	// Keep pretty name the same
	if (p.name == "Process") {
		p.name = getProcName(p)
	}

	// Name, Status, CPU%, MEM%
	var html = '<td>' + p.name + '</td>' +
		'<td id="status">' + p.status + '</td>' +
		'<td>' + p.cpu_percent + ' %</td>' +
		'<td>' + p.mem_percent + ' %</td>' 

	// Add start/stop button
	if (p.status == 'Running') {
		html += '<td><button onclick="updateProc(this,\'stopProc\')">stop</button></td>'
	} else {
		html += '<td><button onclick="updateProc(this,\'startProc\')">start</button></td>'
	}

	// Update button, since we don't push cpu/mem
	html +=	'<td><button onclick="updateProc(this,\'getProcStat\')">update</button></td>'

	return html
}

function updateProcResp(id, param, resp) {
	console.log(resp)
	var p = JSON.parse(resp)
	document.getElementById(id).innerHTML = getProcInnerHTML(p)
}

function updateProc(elem, func) {
	var row = elem.parentNode.parentNode
	ajaxRequest(row.id, ['fun', 'param'], [func ,row.id], updateProcResp)
}

function getProcName(pp) {
	for (var p in procs) {
		if (procs[p].proc == pp.proc) {
			return procs[p].name
		}
	}
}

function dumpColl() {
	ajaxRequest('dumpColl', 'fun', 'dumpColl', false)
}
