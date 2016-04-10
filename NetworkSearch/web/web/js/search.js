var showStructuredSearch = window.location.search.indexOf('showSearch') > 0 
var DEBUG = window.location.search.indexOf('DEBUG') > 0
var showMongo = DEBUG || window.location.search.indexOf('showMongo') > 0
var showRank = DEBUG || window.location.search.indexOf('showRank') > 0 || getCookie('showRank')!= 'false'
var showStructuredSearch = window.location.search.indexOf('showStructure') > 0
var useBox = window.location.search.indexOf('useBox') > 0
var numProjRows = 0
var numMatchRows = 1
var numLinkRows	= 1
var attrSelects = [
	'sort',	
	'aggAttr',
	'by'
]
var adsEnable = false


var isProject = false

// Attributes that should not be displayed with the object
var HIDE_ATTRS = ['object-type', 'result-score']

// Minimum number of letters to type before giving suggestions
var MIN_SUGGESTION_LENGTH = 2

// Maximum number of chars displayed in a value
var MAX_VAL_LENGTH = 100 

// Maximum number of chars in an object name
var MAX_NAME_LENGTH = 94 

// Recent searches: constants and an obj to hold current rather than
//	checking cookie all the time
var COOKIE_EXP	= 30
var RECENT	= 'netwsearch_recent'
//var NUM_SEARCHES= 10
var NUM_SEARCHES= 5
var searches	= {}

// Places name and type at the top of an object result table
//var DO_TYPE_NAME_TOP = false
var DO_TYPE_NAME_TOP = true

// Keeps track of default result list size
var k = 20

// Whether or not to rank
var rank = true

String.prototype.toDHHMMSS = function () {
    var sec_num = parseInt(this, 10); // don't forget the second parm
    var days    = Math.floor(sec_num / 86400)
    var hours   = Math.floor((sec_num - (days * 86400)) / 3600);
    var minutes = Math.floor((sec_num - (days * 86400)  - (hours * 3600)) / 60);
    var seconds = sec_num - (days * 86400) - (hours * 3600) - (minutes * 60);

    //if (hours   < 10) {hours   = "0"+hours;}
    if (minutes < 10) {minutes = "0"+minutes;}
    if (seconds < 10) {seconds = "0"+seconds;}
    var time    = "" 
    
    if (days)
    	time = days+' days, '+hours+' hrs, '+minutes+' mins, '+seconds+' secs';
    else if (hours)
     	time = hours+' hrs, '+minutes+' mins, '+seconds+' secs';
    else 
    	time = minutes+' mins, '+seconds+' secs'; 
    	 	
    return time;
}
function loading() {
	document.getElementById('loading').className = 'box'
	document.getElementById('backdrop').className = 'box'
}
function initHTML() {
	//initAttrList()
	if (showStructuredSearch) {
		addStructuredSearch()
			
	} else {
		//document.getElementById('structuredSearch').className = 'hidden'
		document.getElementById('freeSearchTitle').className = 'hidden'
        //        document.getElementById('attributes').className = 'hidden'
		document.getElementById('totalObjs').className = 'hidden'
		document.getElementById('searchTitle').className = 'bigSearch'
                document.getElementById('freeSearch').style.width = '60%'
		document.getElementById('totalObjs').className = 'hidden'

		var queryBox = document.getElementById('freeQueryBox')
		queryBox.className = 'bigQuery'
		queryBox.innerHTML  = '<input id="match" class="match"/><button class="freeSearchButton" onclick="freeSearch()"></button>'
		document.getElementById('savedSearches').className = 'right'
		document.getElementById('loading').className = 'hidden'
		document.getElementById('backdrop').className = 'hidden'
	}

	// Add functions to DOM
	document.getElementById('match').onkeyup = function(e) { enterSubmit(this, e, freeSearch)}
	document.getElementById('totalObjs').onclick = totalNumObjs

	var topK = document.getElementById('topK')
	if (topK) {
		for (i in topK.childNodes) {
			topK.childNodes[i].onclick = function() { changeK(this) }
		}
	}

	// window.setTimeout(totalNumObjs, 500)

	initSearches('recentSearches')	
	
	if (query) sendQuery(query)
}

// Function to specify limit on the result set w/o adding it to the query
function changeK(elem) {
	k = elem.innerHTML == 'All' ? -1 : parseInt(elem.innerHTML)
	parent = elem.parentNode	
	for (i in elem.parentNode.childNodes) {
		if (elem == elem.parentNode.childNodes[i]) {
			elem.className = 'selected'
		} else {
			elem.parentNode.childNodes[i].className = ''
		}
	}
	freeSearch()
}

function addStructuredSearch() {
	initTypes()
	// Fill in attribute option lists	
	for (i in attrSelects) {
		document.getElementById(attrSelects[i]).innerHTML = setOpts(true)
	}
	document.getElementById('matchSelect0').innerHTML = setOpts(true)
	document.getElementById('linkSelect0').innerHTML = setOpts(true)
	document.getElementById('objectTypes').onchange = switchAttrs
	document.getElementById('selectSearchButton').onclick = selectSearch
	//document.getElementById('projection').onkeyup = function(e) { enterSubmit(e, freeSearch) }
	document.getElementById('matchValue0').onkeyup = function(e) { enterSubmit(e, selectSearch) } 
	document.getElementById('limit').onkeyup = function(e) { enterSubmit(e, selectSearch) }
	document.getElementById('matchLink0').onclick = function() { matchRowHandler(this) }
	document.getElementById('linkLink0').onclick = function() { matchRowHandler(this) }
	document.getElementById('projSelect').onchange = function() { attributeSelector(this) }
	//document.getElementById('addLink').onclick = addLink
}

function totalNumObjs() {
	ajaxRequest('totalObjs', 'fun','getNumObjs', totalNumObjsHoverResp)
}
function totalNumObjsHoverResp(id, param, resp) {
	document.getElementById(id).innerHTML = "(" + resp.match(/\d+/) + " total objects in the system)"
}

function initTypes() {
	html = '<option>all objects</option>'
	for (i in typesAttrs) {
		html += '<option value="' + i + '">' + i + '</option>'
	}
	document.getElementById('objectTypes').innerHTML = html  
}

function initAttrList(id) {
	list = ''
	for (i in currAttrs) {
		list += '<li>' + currAttrs[i] + '</li>'
	}
	document.getElementById('attrList').innerHTML = list
}

function setOpts(useAll) {
	html = '<option />'
	if (useAll) {
		for (i in attrs) {
			html += '<option value="' + attrs[i] + '">' + attrs[i] + '</option>'
		}		
	} else {
		for (i in currAttrs) {
			html += '<option value="' + currAttrs[i] + '">' + currAttrs[i] + '</option>'
		}
	}

	return html
} 

function switchAttrs() {
	var type = document.getElementById('objectTypes').options[document.getElementById('objectTypes').selectedIndex].value
	if (type === 'all objects') {
		currAttrs = attrs
		document.getElementById('attrType').innerHTML = 'Attributes:'
	} else {
		currAttrs = typesAttrs[type]
		document.getElementById('attrType').innerHTML = 'Attributes - '+ type + ':'
	}
	initAttrList()
	
	// Adjust the free text search
	var matchBox = document.getElementById('match')
	var newMatch = matchBox.value
	if (newMatch.indexOf('object-type') > -1) {
		if (type === 'all objects') {
			newMatch = matchBox.value.replace(/object-type=\w+/, '')
		} else {
			newMatch = matchBox.value.replace(/object-type=\w+/, 'object-type=' + type)
		}
	} else if (type != 'all objects') {
		if (newMatch.length != 0) newMatch += ' '
		newMatch += 'object-type=' + type
	}
	matchBox.value = newMatch.replace(/^\s\s*/, '').replace(/\s\s*$/, '')

	// This will reinitialize the option lists (NOT LINK) - which will be weird if they are already filled out
	for (var i=0; i<numMatchRows; i++) {
		document.getElementById('matchSelect' + i).innerHTML = setOpts(false)
	}
	for (var i=0; i<numProjRows; i++) {
		document.getElementById('projSelect' + i).innerHTML = setOpts(false)
	}
	for (i in attrSelects) {
		document.getElementById(attrSelects[i]).innerHTML = setOpts(false)
	}
}

function rowHandler(elem) {	
	if (elem.innerHTML == '-') {
		elem.parentNode.parentNode.parentNode.removeChild(elem.parentNode.parentNode)
		numProjRows--
	} else {
		var row = document.createElement('tr')
		row.id	= 'projRow' + numProjRows
		row.className = 'filter'
		row.innerHTML = '<td class="label"></td><td><select id="projSelect' 
			+ numProjRows + '">' + setOpts(false) + '</select><a onclick="javascript:rowHandler(this)" id="projLink' + numProjRows + '">'
			+ (numProjRows > 0 ? '-': '+') + '</a></td>'
		elem.parentNode.parentNode.parentNode.appendChild(row)
		numProjRows++	
	}
}


function matchRowHandler(elem) {
	rowType = elem.id.match(/(\w+)Link/)[1]
 	numRows = rowType == 'match' ? numMatchRows : numLinkRows
	if (elem.innerHTML == '-') {
		elem.parentNode.parentNode.parentNode.removeChild(elem.parentNode.parentNode)
		rowType == 'match' ? numMatchRows-- : numLinkRows--
	} else {

		var row = document.createElement('tr')
		row.innerHTML = '<td><select id="' + rowType + 'Select' + numRows + '">' 
			+ setOpts(rowType == 'match' ? false : true) + '</select>'
			+ '<select id="' + rowType + 'Op' + numRows 
			+ '"><option>=</option><option>&gt;</option><option>&lt;</option>'
                        + '<option>&gt;=</option><option>&lt;=</option><option>!=</option></select>'
			+ '<input id="' + rowType + 'Value' + numRows + '"/>'
			+ '<a onclick="javascript:matchRowHandler(this)" id="' + rowType + 'Link' + numRows + '">-</a></td>'
		elem.parentNode.parentNode.parentNode.appendChild(row)
		
		rowType == 'match' ? numMatchRows++ : numLinkRows++
	}
}

function attributeSelector(select) {
	if (select.value == 'objects') {
		for (i=0; i<numProjRows; i++) {
			document.getElementById('projSelect' + i).disabled = true
			document.getElementById('projLink' + i).className = 'nonresponsive'
		}
	} else if (numProjRows == 0) {
		rowHandler(select)
	} else {
		for (i=0; i<numProjRows; i++) {
			document.getElementById('projSelect' + i).disabled = false
			document.getElementById('projLink' + i).className = ''
		}
	}
}

// Search using free text in the right-hand column
function freeSearch() {
	var matchQuery = []
	var cmdline = document.getElementById('match').value.replace(/\r?\n|\r|\n/g, ' ').replace(/\s+/g, ' ').trim();
	if (cmdline) {
		// Break strings
		if (cmdline.indexOf('"') < 0 && cmdline.indexOf("'") < 0) {
			matchQuery.push(cmdline)
		} else {
			var regex = /["']\s*([^'"]*)\s*['"]/g
			var str = regex.exec(cmdline)
			while (str != null) {
				matchQuery.push(str[1])
				str = regex.exec(cmdline)
			}
		}

		sendQuery(matchQuery)
	}
}

// Search using the structure supplied in left-hand column
function selectSearch() {
	var matchQuery = []
	var projQuery = []

	// Check object_type
	type = document.getElementById('objectTypes').options[document.getElementById('objectTypes').selectedIndex].value
	if (type != 'all objects') {
		matchQuery.push('object-type=' + type)
	}

	// Find match querys
	for (i=0; i<numMatchRows; i++) {
		match_i = document.getElementById('matchSelect' + i)
		if (match_i.options[match_i.selectedIndex].value != '') {
			op_i	= document.getElementById('matchOp' + i)
			val_i	= document.getElementById('matchValue' + i)

			matchQuery.push(match_i.options[match_i.selectedIndex].value 
				+ op_i.options[op_i.selectedIndex].value + val_i.value)
		}
	}

	// Find projections
	for (i=0; i<numProjRows; i++) {
		proj_i = document.getElementById('projSelect' + i)
		val_i = proj_i.options[proj_i.selectedIndex].value
		if (!proj_i.disabled && val_i) projQuery.push(val_i)
	}	

	// Add additional projection values
	var sortAttr = document.getElementById('sort').options[document.getElementById('sort').selectedIndex].value
	if (sortAttr != '') {
		projQuery.push('-s', sortAttr)
	}
	var limit = document.getElementById('limit').value
	if (Number(limit)) {
		projQuery.push('-l', limit)
	}

	// Check for aggregation
	var agg = document.getElementById('aggAttr').options[document.getElementById('aggAttr').selectedIndex].value
	if (agg != '') {
		var aggFun = document.getElementById('aggFun').options[document.getElementById('aggFun').selectedIndex].value
		var by = document.getElementById('by').options[document.getElementById('by').selectedIndex].value
		projQuery.push('-g', agg + "^" + aggFun)
		
		if (by != '') {
			projQuery.push('-b', by)
		}
	}

	// Add leading "-p" to projection
	if (projQuery.length > 0) {
		projQuery.splice(0,0,'-p')
	}

	// Convert back to space-delimited string	
	projQuery = projQuery.join(" ").trim()
	matchQuery = matchQuery.join(" ").trim()

	// Check for link
	linkQuery = []
	for (i=0; i<numLinkRows; i++) {	
		link_i = document.getElementById('linkSelect' + i)
		if (link_i.options[link_i.selectedIndex].value != '') {
			op_i	= document.getElementById('linkOp' + i)
			val_i	= document.getElementById('linkValue' + i)

			linkQuery.push(link_i.options[link_i.selectedIndex].value 
				+ op_i.options[op_i.selectedIndex].value + val_i.value)
		}
	}
	linkQuery = linkQuery.join(" ")
	if (linkQuery) { matchQuery = [matchQuery,linkQuery] }

		
	// Prepare for new results
	preSearch([projQuery, matchQuery])

	// Send query to server
	ajaxRequest(['projection','match'], 'query', [projQuery, matchQuery], sendQueryResp)
}

// Prepare for the search results
function preSearch(query) {
	// Get the syntactically correct form of the query
	//query = getCorrectQuery(query)

	// Add to recent searches
	populateSearch('recentSearches', query)

	// Display final query
	document.getElementById('match').value = query

	// Clear autosuggest
	var as = document.getElementById('freeQueryBoxAuto')
	if (as) as.innerHTML = ''

	// Clear results field
	document.getElementById('queryMeta').innerHTML = ''
	document.getElementById('queryResults').innerHTML = 'Searching...'
	
	// Fake ads
	if (document.getElementById('ad1')) document.getElementById('ad1').style.display = 'block'
	if (document.getElementById('ad2')) document.getElementById('ad2').style.display = 'block'
}
// Function to allow submission on whichever search function using CTRL + ENTER
function enterSubmit(elem, e, fun) {
	e = e || event;
	if (e.keyCode === 13) {//&& e.ctrlKey) {
		fun(elem)
  	} else if (elem.id.indexOf('Root') < 0) {
		findAttrs(elem)
	}
}

function findAttrs(elem) {
	var term = elem.value	
	if (term.indexOf(' ') > -1) {
 		term = term.split(' ').pop().replace('"', '')
	}
	var html = ''
	if (term.length >= MIN_SUGGESTION_LENGTH) {
		for (i in attrs) {
			if (attrs[i].indexOf(term) > -1) {
				html += '<span class="terms">' + attrs[i] + '</span>'
			}
		}
	}
	setSuggestionDiv(elem.parentNode, html)
}

function setSuggestionDiv(parentNode, html) {
	var divId = parentNode.id + 'Auto'
	var div = document.getElementById(divId)
	if (div) {
		div.innerHTML = html
	} else {
		div = document.createElement('div')
		div.id = (divId)
		div.innerHTML = html
		div.className = 'match'
		parentNode.appendChild(div)
	}
}

// Send a query on the system via AJAX
function sendQuery(query) {
	preSearch(query)

	// Check for settings cookie
	var approximate = getCookie('Approximate')
	var k = getCookie('TopK')
	var tf = getCookie('tf')
	var nr = getCookie('nr')
	var tr = getCookie('tr')
	//if (cookieRank != null) rank = cookieRank
	//if (cookieK != null) k = cookieK
	
	// Add limit and rank
	ajaxRequest('match', ['query', 'limit','approximate','tf','nr','tr'], [query, k, approximate,tf,nr,tr], sendQueryResp)
}
/*
function sendQuery(query) {
	preSearch(query)

	// Check for settings cookie
	var cookieRank = getCookie('rank')
	var cookieK = getCookie('numResults')
	if (cookieRank != null) rank = cookieRank
	if (cookieK != null) k = cookieK

	// Add limit and rank
	ajaxRequest('match', ['query', 'limit','rank'], [query, k, rank], sendQueryResp)
}
*/

// Send a query on the system via AJAX
function sendRefinedQuery(param) {
	var query = document.getElementById('match').value.split('"')
	var match = [] 
	for (q in query) {
		if (query[q].length > 0) {
			if (query[q].indexOf('"-') < 0)
				match.push(param + ' ' +  query[q])
			else 
				match.push(query[q])
		}
	}
	sendQuery(match)
}

// Ajax response function to display query results
function sendQueryResp(id, query, resp) {
	var r = JSON.parse(resp)
	isProject = r.parameters['isProject']
	var items = r.results
	if (items) {
		var metaInfo = ' ' + items.length + ' results (' + r.time.toFixed(3) + ' seconds)' 
		if (showRank && 'rank_time' in r) 
			metaInfo += ' <label class="rank">Rank time ' + r.rank_time.toFixed(0) + ' milliseconds.</label>'
		document.getElementById('queryMeta').innerHTML = metaInfo
		objectResp(items, 'queryResults', getDisplayAttrs(r.query))
	} else {
		document.getElementById('queryResults').innerHTML = 'No matches'
	}
	
	if (showMongo) {
		document.getElementById('mongo').innerHTML = 'MONGO: ' + r.mongo
		document.getElementById('mongo').style.display = 'block'
	}
	document.getElementById('currentSettingLabel').innerHTML =''
	if (r.parameters['isApprox'] != false) {
		document.getElementById('currentSettingLabel').innerHTML  += " Approximate matching <p>"
		document.getElementById('currentSettingLabel').innerHTML  += " Ranking weights : <br>" 
		document.getElementById('currentSettingLabel').innerHTML  +="EPR : " + r.parameters['tf']
		document.getElementById('currentSettingLabel').innerHTML  +=" NR : " + r.parameters['nr']
		document.getElementById('currentSettingLabel').innerHTML  +=" TR : " + r.parameters['tr']
		
		if (r.parameters['limit']) 
			document.getElementById('currentSettingLabel').innerHTML  += "<p>  Max "+r.parameters['limit']+" results" 
		else
			document.getElementById('currentSettingLabel').innerHTML  += "" // unlimited return
			
		if (showRank) document.getElementById('currentSettingLabel').innerHTML += "" //" Show rank scores"
	}else{
		document.getElementById('currentSettingLabel').innerHTML  += " Exact matching <br>"	
	}
	
	if(adsEnable){
		if(Math.random() > 0.4)
			document.getElementById('ads').className += 'hidden'
		else
			document.getElementById('ads').className = '' 
	}
}

// Creates a list of all keywords and attributes specified in the query
function getDisplayAttrs(query) {
	var queryStrs = query.split(',')
	for (i in queryStrs) if (queryStrs[i][0] == '-') return false

	var attrs = []
	var tokens = query.split(' ')
	for (i in tokens) {
		var t = tokens[i]
		if (t.length > 1  && (t.indexOf('(') >= 0 || t.indexOf(')') >= 0)) t = t.match(/\(?\s*(\w+)\s*\)?/)[1]
		// Remove syntax chars
		if (t == '+' || t == '(' || t == ')') {
			if (t.length > 0 && t[1] == 'l') {
				i++
			}
			continue
		} else {
			if ((n=t.search(/[><!=]+/)) > 0) attrs.push(t.substr(0,n))
			else	attrs.push(t)
		}
	}
	return  attrs
}

// Corrects the user inputted query as far as spaces, quotations go
function getCorrectQuery(matchQuery) {
	var query = ''
	if (matchQuery)	{
		if(Object.prototype.toString.call(matchQuery) === '[object Array]' ) {
			query = '"' + matchQuery.join('" "') + '"'
		} else {
			query = '"' + matchQuery + '"'
		}
	}
	
	return query
}


// Fill the search div with saved, recent, link queries etc.
function populateSearch(id, query) {
	var name = id.substring(0, id.indexOf('Search'))	
	addSearch(name,query)
	initSearches(id)
}

// Creates search divs on page load
function initSearches(id) {
	var name = id.substring(0, id.indexOf('Search'))	
	var searches = getCookie(name)
	if (searches) {
		if (name == 'recent') {
			document.getElementById(id + 'Title'). innerHTML = 'Sample Search Queries:'
		}

		var html = ''
		for (i=0;i<searches.length;i++) {
			html += '<li><a id="'+ name + i +'" href="javascript:runRecent(\'' + escape(searches[i]) + '\')">' + shorten(searches[i],100) + '</a></li>'
		}
		document.getElementById(id).innerHTML = html
	}
}

// Executes a recent search
function runRecent(query) {
	document.getElementById('match').value = unescape(query).replace('&gt;', '>').replace('&lt;','<')
	freeSearch()
}

// Add a query of a given type to the list of searches
function addSearch(type,query) {
	// If no searches in memory, pull from cookie
	if (!searches[type]) {
		searches[type] = getCookie(type)
	}

	// If still no searches, start the list
	if (!searches[type]) {
		searches[type] = [query]
	}
	else {
		for (i=0; i < searches[type].length; i++) {
			if (searches[type][i].toString() == query.toString()) {
				searches[type].splice(i,1)
				break
			}
		}
		searches[type].splice(0,0,query)
		if (searches[type].length > NUM_SEARCHES) {
			searches[type] = searches[type].slice(0, NUM_SEARCHES)
		}
	}

	setSearches(type, searches[type])
}

// Set the searches cookie
function setSearches(name, searches)
{
	var exdate = new Date()
	exdate.setDate(exdate.getDate() + COOKIE_EXP)
	var c = name + "=" + escape(searches.join("&")) + "; expires=" + exdate.toUTCString() 
	document.cookie = c
}

// Get searches from cookie
function getCookie(name)
{
	var queries
	var cs = document.cookie.split("; ")
	for (c=0; c<cs.length; c++) {
		var attrval = cs[c].split("=")
		if (attrval[0] == name) {
			queries = unescape(attrval[1]).split("&")
			break
		}
 	}
	return queries
}

// Function to switch the limited display of an object with the full display
function switchObjectDisplay(id, showFull) {
	if (id) {
		if (showFull == null) showFull = document.getElementById(id).className != 'hidden' 
		var link = document.getElementById(id + 'SwitchLink')
		if (showFull) {
			showElem = document.getElementById(id + 'Full')
			hideElem = document.getElementById(id)
			if (link) link.innerHTML = 'Show less'
		} else {
			showElem = document.getElementById(id)
			hideElem = document.getElementById(id + 'Full')
			if (link) link.innerHTML = 'See more Information'
		}

		if (hideElem) hideElem.className = 'hidden'
		if (showElem) showElem.className = 'content left'
	}
}

// Function to create result list from an AJAX response
function objectResp(items, displayElemId, displayAttrs) {
        var l = 0
        var list = document.createElement('ul')
	document.getElementById(displayElemId).innerHTML = ''
        document.getElementById(displayElemId).appendChild(list)
        for (i in items) {
                // Create a list item for every object in the result set
                var listitem = document.createElement('li')
                if (items.length > 1) listitem.innerHTML =  '<div class="resultNum">' + ++l + '</div>'
                listitem.appendChild(objectResult(l, items[i], false, displayAttrs))
                list.appendChild(listitem)
        }
}

// Create a new string from a long string given a length, a set of attrs to highlight
function shorten(str, maxLen, displayAttrs) {
	var minLen = maxLen / 2	

	// Return if this string is already short
	if (str.length <= maxLen) return str

	// Then find any displayAttrs in the 2nd half of string and record their location
	var attrs = []
	for (i in displayAttrs) {
		var attr = displayAttrs[i]
		var idx = str.indexOf(attr, minLen -1)
		if (idx > -1) {
			attrs[idx] = attr
		}
	}

	// Create a new string with ellipses
	var attrStr = ''
	var lastIndex = minLen
	for (var i in attrs) {
		var attr = attrs[i]
		if (attr && attrStr.indexOf(attr) < 0) {
			if (parseInt(i) > lastIndex + 1) attrStr += '...'
			attrStr += attr
			lastIndex = parseInt(i)
		}
	}
	

	// Shorten the string, and add ellipses if needed
	var newLen = maxLen - attrStr.length
	if (str.length > newLen) {
		str = str.substr(0, maxLen - attrStr.length)
		str += attrStr
		str += '...'
	}

	return str
}

// Creates the HTML for each object in the result set
function objectResult(resultNum, object, isHidden, displayAttrs) {
	var score = 0
	if (object instanceof Array) {
		score = object[0]
		object = object[1]
	}
	// use box appearance
	if (useBox) {

		// Creates table of the object to be displayed (limited or full)
		var origTable = createObjectTable(resultNum, object, false, displayAttrs)
	
		// Creates the wrapper for each object result
		var result = document.createElement('div')
		result.id = origTable.id + 'Box'
		result.className = 'box left objectBox'
	
		// Adds a title if object type and name
		var objType = object['object-type']
		if (objType ) {
			var nameAttr = 'object-name'
			if (object[nameAttr]) {
				var name = shorten(object[nameAttr], MAX_NAME_LENGTH, displayAttrs)
				var title = document.createElement('h4')
				title.innerHTML =  name + '<label class="object_type">' + objType + '</label>'
				if (showRank && score) {
					title.innerHTML += '<label class="rank">' + score.toFixed(5) + '</label>'
				}
				title.onclick = function() { switchObjectDisplay(origTable.id) }
				result.appendChild(title)
			}
		}
	
		// Appends the original object result table
		result.appendChild(origTable)
		
		// If only displaying some attrs - go ahead and create a hidden table
		//      with the full object as well
		if (displayAttrs) {
			var fullTable = createObjectTable(resultNum, object , true)
			result.appendChild(fullTable)
			result.appendChild(createObjectLinks('', origTable.id, object))
		} else if(isHidden) {
			result.appendChild(createObjectLinks('full', origTable.id, object))
		}
	} else {
	
		// Uses new appearance
		
		// Creates the wrapper for each object result
		var result = document.createElement('div')
		result.id = 'object' + resultNum + 'Box'
		result.className = 'box left objectBox'
		
		// Adds a title if object type and name
		var objType = object['object-type']
		if (objType ) {
			var nameAttr = 'object-name'
			if (object[nameAttr]) {
				var name = shorten(object[nameAttr], MAX_NAME_LENGTH, displayAttrs)
				var title = document.createElement('h4')
				title.innerHTML =  '<label class="object_name">' + name + '</label>'+ '<label class="object_type">' + objType + '</label>'
				if (showRank && score) {
					title.innerHTML += '<label class="rank">' + score.toFixed(5) + '</label>'
				}
				title.onclick = function() { switchObjectDisplay('object'+resultNum) }
				result.appendChild(title)
			}
		}
		
		// Appends content section
		result.appendChild(createObjectContent(resultNum,object,false))
		result.appendChild(createObjectContent(resultNum,object,true))
		
		// Appends link section
		//result.appendChild(createObjectLinks('', 'object'+resultNum, object))
		
		//result.innerHTML = 'test'
	}
	
	return result
}

// create content of an object 
function createObjectContent(id,object,isFull){

	var content = document.createElement('label')
	content.id = 'object'+id
	content.className = 'content left'

	// Create a table using all attrs and vals , then hide it
	if (isFull) {  
		content.id += 'Full'
		content.className = 'hidden'
	}
	
	// create a content infomation based on predefine format
	var objType = object['object-type']
	var contentText = ''
	var SEP = ' '
	
	if(isProject){
		for (var i in object){
			if (i !='object-name' && i != 'object-type')
				contentText += i+': <code>' + object[i] + '</code><br> ' 
		}
		
	}
	else if (objType == 'server'){
		contentText += createContentSentence('Hostname', object['hostname'], isFull)
		contentText += createContentToken('<br>', isFull)
		
		contentText += createContentSentence('CPU cores', object['cpu-cores'], true)
		if(object['memory']) contentText += createContentSentence( SEP+'Memory', (object['memory']/1073741824).toFixed(2) +' GB', true)
		if(object['disk'])   contentText += createContentSentence( SEP+'Disk', (object['disk']/1073741824).toFixed(2) +' GB', isFull)
		contentText += createContentToken('<br>', true)		
				
		// special case for array result 
		if(object['ip-address']){
			if (object['ip-address'].length > 1  && !(isFull)){
				contentText += createContentSentence('IP address', object['ip-address'].sort().reverse().slice(0,1).join(', ') + ', ...' , true)
			}else{
				contentText += createContentSentence('IP address', object['ip-address'].sort().reverse().join(', '), true)
			}
			contentText += '</code><br>'
		}
		contentText += createContentSentence('OS', object['linux-distribution'], isFull)		
		contentText += createContentSentence(SEP+'Architecture', object['architecture'], isFull)	
		contentText += createContentToken('<br>', isFull)
		
		contentText += createContentSentence('kernel', object['kernel-version'], isFull)		
		contentText += createContentToken('<br>', isFull)
						
		if(typeof object['cpu-load'] == 'number') contentText += createContentSentence('CPU load', object['cpu-load'].toFixed(2) + '%', true)
		if(typeof object['memory-load'] == 'number') contentText += createContentSentence(SEP+'Memory load', object['memory-load'].toFixed(2) + '%', true)
		if(typeof object['disk-load'] == 'number') contentText += createContentSentence(SEP+'Disk load', object['disk-load'] + '%', isFull)
		contentText += createContentToken('<br>', true)

		if(object['uptime'])contentText += createContentSentence('Uptime', object['uptime'].toString().toDHHMMSS(), isFull)
		contentText += createContentToken('<br>', isFull)
		if(object['last-updated'])contentText += createContentSentence('Last updated', object['last-updated'].replace('T',' ').slice(0,object['last-updated'].lastIndexOf('.')), isFull)	
		if(!(isFull)) {contentText += '...'}
		
	}else if (objType == 'flow') {
		contentText += createContentSentence('Source IP', object['src-ip'], isFull)
		contentText += createContentSentence(SEP+'Destination IP', object['dst-ip'], isFull)
		contentText += createContentToken('<br>', isFull)
		
		contentText += createContentSentence('Source port', object['src-port'], isFull)
		contentText += createContentSentence(SEP+'Destination port', object['dst-port'], isFull)
		contentText += createContentToken('<br>', isFull)		
		
		contentText += createContentSentence('Server', object['server'], true)
		contentText += createContentToken('<br>', true)		
				
		contentText += createContentSentence('Packets', object['packets'], isFull)
		contentText += createContentSentence(SEP+ 'Bytes', object['bytes'], isFull)
		contentText += createContentToken('<br>', isFull)	
			
		if (typeof object['bandwidth'] == 'number') contentText += createContentSentence(SEP+ 'Bandwidth', (object['bandwidth']*8/1024).toFixed(2)+ ' kbps', true)
		if (typeof object['bytes'] == 'number' && typeof object['packets'] == 'number') contentText += createContentSentence(SEP+ 'Packet size (avg.)', (object['bytes']/object['packets']).toFixed(2) + ' bytes', true)
		contentText += createContentToken('<br>', true)
		
		if(object['start-time']) contentText += createContentSentence('Start time', object['start-time'].replace('T',' ').slice(0,object['start-time'].lastIndexOf('.')), isFull)
		if(object['last-updated']) contentText += createContentSentence(SEP+ 'Last updated', object['last-updated'].replace('T',' ').slice(0,object['last-updated'].lastIndexOf('.')), isFull)
		if(!(isFull)) {contentText += '...'}	
	}else if (objType == 'file') {
		contentText += createContentSentence('Location', object['object-name'], isFull)	
		contentText += createContentSentence(SEP+ 'Extension', object['extension'], isFull)	
		contentText += createContentToken('<br>', isFull)
		
		contentText += createContentSentence('User', object['user'], true)
		contentText += createContentSentence(SEP+'Group', object['group'], true)	
		contentText += createContentToken('<br>', true)

		contentText += createContentSentence('Server', object['server'], true)		
		contentText += createContentToken('<br>', true)	
		
		contentText += createContentSentence('Size', object['size-bytes']+' bytes', isFull)
		contentText += createContentToken('<br>', isFull)
				
		if(object['file-modify-date']) contentText += createContentSentence('Last modified', object['file-modify-date'].replace('T',' ').slice(0,object['file-modify-date'].lastIndexOf('.')), isFull)
		contentText += createContentToken('<br>', isFull)
		
		if(object['file-access-date']) contentText += createContentSentence('Last accessed', object['file-access-date'].replace('T',' ').slice(0,object['file-access-date'].lastIndexOf('.')), true)
		contentText += createContentToken('<br>', true)
		if(!(isFull)) {contentText += '...'}		
	}else if (objType == 'network-interface') {
		contentText += createContentSentence('IP address', object['ip'], true)
		contentText += createContentSentence(SEP+'IPv6 address', object['ipv6'], true)
		contentText += createContentToken('<br>', true)

		contentText += createContentSentence('MAC address', object['mac-address'], isFull)
		contentText += createContentToken('<br>', isFull)
		
		contentText += createContentSentence('Server', object['server'], true)
		contentText += createContentSentence(SEP+'VM', object['vm'], true)
		contentText += createContentToken('<br>', true)
		if(!(isFull)) {contentText += '...'}
	}else if (objType == 'user') {
		contentText += createContentSentence('User id', object['user-id'], isFull)
		contentText += createContentSentence(SEP+'Description', object['comment'], isFull)
		contentText += createContentToken('<br>', isFull)
				
		contentText += createContentSentence('Group', object['group'], true)
		contentText += createContentSentence(SEP+'Server', object['server'], true)			
		contentText += createContentToken('<br>', true)
		
		contentText += createContentSentence('Directory', object['directory'], isFull)
		contentText += createContentToken('<br>', isFull)		
		
		contentText += createContentSentence('Shell', object['shell'], true)
		contentText += createContentToken('<br>', true)	
		if(!(isFull)) {contentText += '...'}					
	}else if (objType == 'process') {
		contentText += createContentSentence('Process id', object['process-id'], isFull)
		contentText += createContentSentence(SEP+'Process type', object['process-type'], isFull)
		contentText += createContentToken('<br>', isFull)
		
		contentText += createContentSentence('Username', object['user'], true)
		contentText += createContentSentence(SEP+'Server', object['server'], true)			
		contentText += createContentToken('<br>', true)
		
		contentText += createContentSentence('Threads', object['num-threads'], true)			
		contentText += createContentToken('<br>', true)	
		
		contentText += createContentSentence('Command line', object['command-line'], isFull)
		contentText += createContentToken('<br>', isFull)
		
		if(typeof object['cpu-load'] == 'number') contentText += createContentSentence('CPU load', object['cpu-load'].toFixed(2) + '%', true)
		if(typeof object['memory-load'] == 'number') contentText += createContentSentence(SEP+'Memory load', object['memory-load'].toFixed(2) + '%', true)
		contentText += createContentToken('<br>', true)
		
		if(object['start-time']) contentText += createContentSentence('Start time', object['start-time'].replace('T',' ').slice(0,object['start-time'].lastIndexOf('.')), isFull)
		contentText += createContentToken('<br>', isFull)

		if(object['last-updated']) contentText += createContentSentence('Last updated', object['last-updated'].replace('T',' ').slice(0,object['last-updated'].lastIndexOf('.')), isFull)
		contentText += createContentToken('<br>', isFull)		
		if(!(isFull)) {contentText += '...'}
	}else if (objType == 'customer') {
		contentText += createContentSentence('Username', object['email'], true)			
		contentText += createContentToken('<br>', true)
		
		contentText += createContentSentence('Application', object['application'], true)			
		contentText += createContentToken('<br>', true)	
			
		contentText += createContentSentence('Account type', object['account-type'], true)			
		contentText += createContentToken('<br>', true)		
		
	}else if (objType == 'image') {
		contentText += createContentSentence('Image id', object['image-id'], isFull)
		contentText += createContentToken('<br>', isFull)
		
		if(object['size']) contentText += createContentSentence('Size', (object['size']/1048576).toFixed(2) + ' MB', true)
		contentText += createContentSentence(SEP+'Disk format', object['disk-format'], true)
		contentText += createContentSentence(SEP+'Container format', object['container-format'], true)
		contentText += createContentToken('<br>', true)
		
		contentText += createContentSentence('Min RAM', object['min-ram'], isFull)
		contentText += createContentSentence(SEP+'Min disk', object['min-disk'], isFull)
		contentText += createContentToken('<br>', isFull)

		contentText += createContentSentence('Customer', object['customer'], isFull)
		contentText += createContentToken('<br>', isFull)		
		
		contentText += createContentSentence('Location', object['location'], true)
		contentText += createContentToken('<br>', true)
		
		contentText += createContentSentence('Server', object['server'], true)
		contentText += createContentToken('<br>', true)
		
		contentText += createContentSentence('Public access', object['is-public'], isFull)
		contentText += createContentSentence(SEP+'Protected', object['protected'], isFull)
		contentText += createContentToken('<br>', isFull)
		
		contentText += createContentSentence('Checksum', object['check-sum'], isFull)
		contentText += createContentToken('<br>', isFull)	
		
		contentText += createContentSentence('Status', object['status'], isFull)
		contentText += createContentToken('<br>', isFull)
		
		// special case for array result 
		if (object['vm']){
			if (object['vm'].length > 1  && !(isFull)){
				contentText += createContentSentence('VM', object['vm'].sort().reverse().slice(0,1).join(', ') + ', ...' , true)
				contentText += '</code><br>'
			}else{
				contentText += createContentSentence('VM', object['vm'].sort().reverse().join(', '), true)
				contentText += '</code><br>'
			}
		}
		if(object['created-at']) contentText += createContentSentence('Create time', object['created-at'].replace('T',' ').slice(0,object['created-at'].lastIndexOf('.')), isFull)
		contentText += createContentToken('<br>', isFull)

		if( object['updated-at']) contentText += createContentSentence('Last updated', object['updated-at'].replace('T',' ').slice(0,object['updated-at'].lastIndexOf('.')), isFull)
		contentText += createContentToken('<br>', isFull)
		if(!(isFull)) {contentText += '...'}
		
	}else if (objType == 'vm') {
		contentText += createContentSentence('Libvirt id', object['libvirt-id'], isFull)
		contentText += createContentToken('<br>', isFull)

		contentText += createContentSentence('UUID', object['uuid'], isFull)
		contentText += createContentToken('<br>', isFull)
		
		contentText += createContentSentence('CPU cores', object['cpu-cores'], true)
		if(object['memory']) contentText += createContentSentence( SEP+'Memory', (object['memory']/1073741824).toFixed(2) +' GB', true)
		contentText += createContentToken('<br>', true)	
		
		// special case for array result 
		if(object['ip-address']){
			if (object['ip-address'].length > 1  && !(isFull)){
				contentText += createContentSentence('IP address', object['ip-address'].sort().reverse().slice(0,1).join(', ') + ', ...' , true)
			}else{
				contentText += createContentSentence('IP address', object['ip-address'].sort().reverse().join(', '), true)
			}
			contentText += '</code><br>'
		}
		contentText += createContentSentence('Server', object['server'], true)
		contentText += createContentSentence(SEP+'Customer', object['customer'], true)
		contentText += createContentToken('<br>', true)
		
		if(typeof object['cpu-load'] == 'number') contentText += createContentSentence('CPU load', object['cpu-load'].toFixed(2) + '%', isFull)
		if(typeof object['memory-load'] == 'number') contentText += createContentSentence(SEP+'Memory load', object['memory-load'].toFixed(2) + '%', isFull)
		contentText += createContentToken('<br>', isFull)
		
		if(object['cpu-time']) contentText += createContentSentence(SEP+'CPU time', object['cpu-time'].toString().toDHHMMSS(), isFull)
		contentText += createContentToken('<br>', isFull)
				
		contentText += createContentSentence('Status', object['status'], true)
		if(object['uptime']) contentText += createContentSentence(SEP+'Uptime', object['uptime'].toString().toDHHMMSS(), true)
		contentText += createContentToken('<br>', true)		
		
		if(object['date-started']) contentText += createContentSentence('Start time', object['date-started'].replace('T',' ').slice(0,object['date-started'].lastIndexOf('.')), isFull)
		contentText += createContentToken('<br>', isFull)

		//if(object['date-modified']) contentText += createContentSentence('update time', object['date-modified'].replace('T',' ').slice(0,object['date-modified'].lastIndexOf('.')), isFull)
		//contentText += createContentToken('<br>', isFull)
		
	}else{
		for (var i in object){
                        if (typeof object[i] == 'number')
				contentText += i+': <code>' + object[i].toFixed(2) + '</code><br> ' 
			else
				contentText += i+': <code>' + object[i] + '</code><br> '
		}
	}
	
	content.innerHTML = contentText
	
	
	return content
}

// Creates content sentences in this form attr_name:attr_value
function createContentSentence(name,value,isShow){
	var SEP_ATTR = ' : '
	if (isShow)
		if (value == null)
			return '' 
		else 
			return name + SEP_ATTR +'<code>' + value +'</code>'
	else
		return ''	
}

function createContentToken(name,isShow){
	if (isShow)
		return name
	else
		return ''	
}

// Creates links that reside under the object
function createObjectLinks(type, id, object) {
	var linkDiv = document.createElement('div')
	linkDiv.className = 'linkDiv'

	var link = document.createElement('a')
	link.id = id + 'SwitchLink'
	link.className = 'box left'
	link.title = 'Choose display style'
	link.innerHTML = ((type == 'full') ? 'Show less' : 'See more information')
	link.onclick = function() {switchObjectDisplay(id)}
	linkDiv.appendChild(link)
	
	if (useBox){
		var linkQuery = createLinkQuery(object)
		if (linkQuery) {
			var llink = document.createElement('a')
			llink.className = 'right box'
			llink.title = 'See all objects linked to this object'
			llink.innerHTML = 'See all linked objects'
			/*var objType = object['object_type']
			var href = 'object-type=' +objType + ' ' + objType + '-name=' + object[objType + '-name']
			if (object['server-name']) href += ' server-name='+ object['server-name']
			llink.href = '/tree?treeType=spacetree&startQuery=' + URLencode('"' + href + '"')
			llink.target = '_blank'*/
			llink.onclick = function() {sendQuery(linkQuery)}
			linkDiv.appendChild(llink)
		}
	} else {
	
	}

	return linkDiv
}


/** To create a linked query from a given object
 *	As a separate function in case we want to change what clicking
 *	the link button does.
 */
function createLinkQuery(object, attrVal) {
	var linkQuery = ''
	var objType = object['object-type']
	if (objType) {
		var uattr = objType + '-name'
		if (object[uattr]) {
			linkQuery = 'LINK ' + uattr + '=' + object[uattr] + ' ' + 'object-type=' + objType		
		}
	}
	
	// Adding thru
	if (attrVal) {
		linkQuery = attrVal //+ ' ' + linkQuery
	}
	
	return linkQuery
}


// Creates object output in table form with one column for attrs and corresponding column of vals
function createObjectTable(resultNum, object, isHidden, displayAttrs) {

        // Increment used to color alternating rows
        var k = 0
        var table = document.createElement('table')
        table.id = 'object' + resultNum

	// Create a table using all attrs and vals
        if (isHidden) {  
                table.id += 'Full'
                table.className = 'hidden'
        }

        // Add object name and type if there are display attributes specified (if doing name and type at the top)
	var objType = object['object-type']
	var nameAttr = objType + '-name'
        if (objType && DO_TYPE_NAME_TOP) {
                var row = createAttrRow(k++, object, 'object-type', objType, ['object-type'], isHidden)
                if (row) table.appendChild(row)
                else k--

		if (object[nameAttr]) {
	                var row = createAttrRow(k++, object, nameAttr, object[nameAttr], [nameAttr], isHidden)
        	        if (row) table.appendChild(row)
                	else k--
		}
        } else if (DO_TYPE_NAME_TOP) {
                displayAttrs = false
        }

        // Add all attr-val pairs as rows in the object table
        for (var j in object) {
                // Don't double print name and type (or print other hidden attrs)
                if (!DO_TYPE_NAME_TOP || (HIDE_ATTRS.indexOf(j) < 0  && j!= nameAttr)) {
                	var val = object[j]
                        if (val instanceof Array) {
                                // If the value is a list, display each as attr-val pair on its own line
                                for (v in val) {
                                        var row = createAttrRow(k++, object, j, val[v], displayAttrs)
                                        if (row) table.appendChild(row)
                                        else k--
                                }
                        } else {
                                var row = createAttrRow(k++, object, j, val, displayAttrs)
                                if (row) table.appendChild(row)
                                else k--
                        }
                }
        }

        return table
}

// Determine display/links of each attr-val row in an object table
function createAttrRow(rowNum, object, attr, val, displayAttrs, isHidden) {
        // If only specific attrs should be displayed, skip this one if it isn't included
        if (displayAttrs && displayAttrs.indexOf(attr.toLowerCase()) < 0 && displayAttrs.indexOf(val) < 0 && attr.indexOf('-count') < 0)  {
                // Now check if maybe the attr-val pair was matched because one of the displayAttrs
                //      is somewhere in the val string
                var valHasDisplayAttr = false
                var valTest = '' + val
                for (a in displayAttrs) {
			if (valTest.toLowerCase().indexOf(displayAttrs[a]) > -1) {
                                valHasDisplayAttr = true
                                break
                        }
                }
                if (!valHasDisplayAttr) return false
        }

        // If we have made it this far, this attr-val pair should be displayed by default
        var displayVal = val
        if (typeof val === 'number') {
                if(parseInt(val) != parseFloat(val)) {
                        displayVal = displayVal.toFixed(5)
                }
                if (attr.indexOf('util') > 0) {
                        displayVal = displayVal + '%'
                }
        } else if (typeof val === 'string' && val.length > MAX_VAL_LENGTH) {
                displayVal = isHidden ? val : shorten(val, MAX_VAL_LENGTH, displayAttrs)
        } else if (attr.indexOf('date') > -1) {
		displayVal = displayVal.replace('T', ' ')
	}

        var tr = document.createElement('tr')
        tr.className = 'r' + rowNum % 2
	var term = attr + '=' + val
//	if (attr.indexOf('-name') > 0) {
//		//var linkTerm = createLinkQuery(object, term) 
//		var linkTerm = term
//		tr.innerHTML = '<td class="attr"><a title="Link through ' + term + 
//			'" onclick="sendQuery(\'' + linkTerm + '\')">' + attr +
//			'</a></td><td><a title="Link through '+ term +
//			'" onclick="sendQuery(\'' + linkTerm + '\')">' + displayVal + '</a></td>'
//	} else 	{		
        	tr.innerHTML = '<td class="attr"><a title="Refine search with ' + attr + 
			'" onclick="sendRefinedQuery(\'' + term + '\')">' + attr +
                        '</a></td><td><a title="Refine search with '+ val +
			'" onclick="sendRefinedQuery(\'' + term + '\')">' + displayVal + '</a></td>'
//	}

	return tr
}

function addSettingsCookie(name , value) {
        var exdate = new Date()
        exdate.setDate(exdate.getDate() + COOKIE_EXP)

        var c = name +"=" + value + "; expires=" + exdate.toUTCString()
        document.cookie = c

        document.location = '/'
}
/*
function addSettingsCookie(numResults, rank) {
        var exdate = new Date()
        exdate.setDate(exdate.getDate() + COOKIE_EXP)

        var c = "numResults=" + numResults + "; expires=" + exdate.toUTCString()
        document.cookie = c

        var c = "rank=" + rank + "; expires=" + exdate.toUTCString()
        document.cookie = c

        document.location = '/'
}
*/
