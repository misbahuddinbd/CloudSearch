var labelType, useGradients, nativeTextSupport, animate;
var PLOT_INTERVAL = 1000;	// milliseconds
var PLOT_TOTAL_TIME = 60000;	// milliseconds
var MAX_PLOT_POINTS = PLOT_TOTAL_TIME/PLOT_INTERVAL + 1;
var B_TO_GB = Math.pow(1024, 3);
var B_TO_MB = Math.pow(1024, 2);
var objType = window.location.search.match(/objType=(\w+)&*/); objType = objType ? objType[1] : '';
var addImages = window.location.search.indexOf('addImages') > 0;

(function() {
  var ua = navigator.userAgent,
      iStuff = ua.match(/iPhone/i) || ua.match(/iPad/i),
      typeOfCanvas = typeof HTMLCanvasElement,
      nativeCanvasSupport = (typeOfCanvas == 'object' || typeOfCanvas == 'function'),
      textSupport = nativeCanvasSupport 
        && (typeof document.createElement('canvas').getContext('2d').fillText == 'function');
  //I'm setting this based on the fact that ExCanvas provides text support for IE
  //and that as of today iPhone/iPad current text support is lame
  labelType = (!nativeCanvasSupport || (textSupport && !iStuff))? 'Native' : 'HTML';
  nativeTextSupport = labelType == 'Native';
  useGradients = nativeCanvasSupport;
  animate = !(iStuff || !nativeCanvasSupport);
})();

var Log = {
  elem: false,
  write: function(text){
    if (!this.elem) 
      this.elem = document.getElementById('log');
    this.elem.innerHTML = text;
    this.elem.style.left = (500 - this.elem.offsetWidth / 2) + 'px';
  }
};

function addText() {
	//var treeDesc = "This animation shows the links between different objects in the cloud. " +
	//	" Interesting related object sets are located in the left column.  Click to display.<br /><br />" +
	//	" The properties and links of the centered object are displayed in a relations list in the right column. " + 
	//	" Clicking on an object moves the tree and centers that object." +
	//	" Refresh the page to see the current objects and links. "
	//$('#tree-description').append(treeDesc)
	$('.appLink').show()
}

function reload(elem) {
 	var url = '/tree?tree=' + elem.id.substr(0,elem.id.indexOf('Root')) + '&root=' + encodeURIComponent(elem.value) 
	if (document.getElementById('selectCustom')) {
		url += '&objType=' + $('#selectCustom').children('option').filter(':selected').text()
	}
	if ($('#addImages').is(':checked')) url += '&addImages=true'
	document.location = url 
}


/* Created HTML string for an attr-val pair that will be displayed in a list */
function displayAttrVal(attr, val) {
	if (attr != 'uptime') {
		if(val >= B_TO_GB) val = (val/B_TO_GB).toFixed(0) + " GB"
		else if (val >= B_TO_MB) val = (val/B_TO_MB).toFixed(0) + " MB"
	}

	html = "<li>"
	html +="<label>" + attr.replace(/-name/,'').replace(/-/g,' ') + "</label>"
	html += val 
	html += "</li>"
	
	return html
}

var timeoutVariable ; 

/* Initializes all text, form field, and draws graph */
function init(){
	//addText()
	// For any tree
	if (treeId && document.getElementById(treeId + 'Root'))  {
		$('#' + treeId + 'Root').val(root)
		$('#' + treeId + 'Root').keypress(function (e) {enterSubmit(this, e, reload)})
	}
	if (addImages) $('#addImages').prop('checked', true)
	if (!json) return
	if (treeId) {
		// If non-custom trees
		//$('#animationTitle').text($('#' + treeId).text() + " Link Graph")
		//document.getElementById('ServerVMCustRoot').onkeyup = function (e) {enterSubmit(this, e, reload)}
		//document.getElementById('CustVMServerRoot').onkeyup = function (e) {enterSubmit(this, e, reload)}

		// For custom tree
		if (objType) $('#selectCustom').val(objType) 

	}
	var infovis = document.getElementById('infovis');
	var w = infovis.offsetWidth - 50, h = infovis.offsetHeight - 50;
   
    //init Hypertree
    var ht = new $jit.Hypertree({
      //id of the visualization container
      injectInto: 'infovis',
      //canvas width and height
      width: w,
      height: h,
      //Change node and edge styles such as
      //color, width and dimensions.
      Node: {
          dim: 9,
          color: "#f00"
      },
      Edge: {
          lineWidth: 2,
          color: "#088"
      },
      onBeforeCompute: function(node){
          Log.write("centering");
      },
      //Attach event handlers and add text to the
      //labels. This method is only triggered on label
      //creation
      onCreateLabel: function(domElement, node){
          domElement.innerHTML = node.name;
          $jit.util.addEvent(domElement, 'click', function () {
              ht.onClick(node.id, {
                  onComplete: function() {
                      ht.controller.onComplete();
                  }
              });
          });
      },
      //Change node styles when labels are placed
      //or moved.
      onPlaceLabel: function(domElement, node){
          var style = domElement.style;
          style.display = '';
          style.cursor = 'pointer';
          if (node._depth <= 1) {
              style.fontSize = "0.8em";
              style.color = "#ddd";

          } else if(node._depth == 2){
              style.fontSize = "0.7em";
              style.color = "#555";

          } else {
              style.display = 'none';
          }

          var left = parseInt(style.left);
          var w = domElement.offsetWidth;
          style.left = (left - w / 2) + 'px';
      },
      
	onComplete: function(){
		Log.write("done");
		window.clearTimeout(timeoutVariable)

		//Build the right column relations list.
		//This is done by collecting the information (stored in the data property) 
		//for all the nodes adjacent to the centered node.
		var node = ht.graph.getClosestNodeToOrigin("current");
		var html = "<h4>" + node.name + (node.data['object-type']?' <span class="type">' + node.data['object-type'] + '</span>' : '' )+"</h4>"
		if (node.data) {
			html += "<ul>";
			// Display attributes which link first
			for (d in node.data) {
				if (d.indexOf('name') > 0 && d.indexOf(node.data['object-type']) < 0 && d !='vm-name') {
					html += displayAttrVal(d, node.data[d])
				}
			}

			// Then all other configuration attributes
			for (d in node.data) {
				// Never display these fields
				if (d != 'object-type' && node.data[d] != node.id && d.toString().indexOf('$') != 0 ) {

					// Display these above (i.e. not here)
					if (d.indexOf('name') < 0 && d.indexOf('uptime') < 0 )
						html += displayAttrVal(d, node.data[d])
				}
			}

			// Then uptime
			if (node.data.uptime) html += displayAttrVal('uptime', node.data.uptime)

			html += "</ul>";
		}

		html += "<br />"
		$jit.id('inner-details').innerHTML = html;

		var numLinks = 0
		var ul = document.createElement('ul')
		ul.id = "link-list"
		node.eachAdjacency(function(adj){
			var child = adj.nodeTo;
			if (child.data) {
				var li = document.createElement('li')
				li.innerHTML = '<label class="link">' + child.name + '</label>'
				//li.innerHTML += '<span class="type">' + child.data['object-type'] + '</span>
          			$jit.util.addEvent(li, 'click', function () {
					ht.onClick(child.id, {
						onComplete: function() {
							ht.controller.onComplete();
						}
					})
				})
				ul.appendChild(li)
				numLinks++
			}
		});
		if (numLinks > 0) {
			$jit.id('inner-details').innerHTML += "<b>Links:</b><br />"
			$jit.id('inner-details').appendChild(ul)
		}

		// Static charts
		//if (node.data['object-type'] == 'vm' || node.data['object-type'] == 'server') renderChart(node.data['object-type'],node.name)

		// Live Update charts
		if (node.data['object-type'] == 'vm' || node.data['object-type'] == 'server' || node.data['object-type'] == 'flow') 
			buildNewLiveUtilGraph(node.data['object-type'],node.name)
		else 
			$('#util-chart-container').html('')
	}
    });
    //load JSON data.
    ht.loadJSON(json);
    //compute positions and plot.
    ht.refresh();
    //ends
    ht.controller.onComplete();
}


/*
*	Right-hand figures - CPU/Mem Util Plots
*/
function renderChart(objType, objName) {
	$.ajax({
		url: "ajax?fun=getAppData&param=" + URLencode(objType + '=' + objName),
		context: document.body,
		success: function(resp) {
			if (!resp) return
			else resp = JSON.parse(resp)
			if (objType == 'vm' || objType == 'server') {
				buildUtilGraph(resp.cpu_utils,resp.memory_utils)
			} else if (objType == 'customer' || objType == 'image') {
			}
		}
	}) 
}


// Builds a graph showing server resource utilizations
function buildUtilGraph(cpu, mem) {
	var util = new Highcharts.Chart({
		colors: ['#058DC7', '#50B432', '#ED561B', '#DDDF00', '#24CBE5', '#64E572', '#FF9655', '#FFF263', '#6AF9C4'],
		chart: {
			renderTo: 'util-chart-container',
			type: 'spline',
			zoomType: 'xy',
		},
		title: {text: 'Server Resource Utilization'},
		xAxis: {
			title: {text: 'Last 10 Minutes'},
			labels: {style: {display:'none'},},
		},
		yAxis: {
			min:0,
			max:100,
			title : {style: {display:'none'},}, 
			labels: {formatter: function() { return this.value +'%';},}
		},
		tooltip: {formatter: function() {return '' + this.y + '%'}},
		series: [{	
				name: 'CPU',
				data: cpu
			}, {	
				name: 'Memory',
				data: mem
			}],

	});
}

/**
 * Attempt to do a live chart
 */
function requestData(objType, objName) {
	//var cpu = (objType == 'server') ? 'cpu_load' : 'server_cpu_util'
	//var mem = (objType == 'server') ? 'memory_load' : 'server_memory_util'
	var cpu = 'cpu-load'
	var mem = 'memory-load'
	// Amy's
	//var query = '-p ' + cpu + ' ' + mem + ',object-type=' + objType + ' ' + objType + '-name=' + objName
	//
	if (objType == 'flow')
		var query = 'project (bytes packets , object-type=' + objType + ' object-name=' + objName +')'
	else
		var query = 'project (' + cpu + ' ' + mem + ' , object-type=' + objType + ' object-name=' + objName +')'

	var url = "ajax?query=" + URLencode(query) + "&rank="+ false
	$.ajax({
		url: url,
		success: function(response) {
			var data = JSON.parse(response)
			var x = -1
			var oldData = liveChart.series[0].data
			for (i in oldData) {
				if (oldData[i].y < 0) {
					x = i
					break;
				}
			}
			if (objType == 'flow'){
				var yc = data.results[0]['bytes']
				var ym = data.results[0]['packets']
			}else{
				var yc = data.results[0][cpu]
				var ym = data.results[0][mem]
			}
			if (x < 0) {//>= MAX_PLOT_POINTS) {
				// add the point
				liveChart.series[0].addPoint(yc, true, true);
				liveChart.series[1].addPoint(ym, true, true);
			} else {
				liveChart.series[0].data[x].update(yc)
				liveChart.series[1].data[x].update(ym)
			}

			// call it again after five seconds
			timeoutVariable = setTimeout(function() {requestData(objType, objName)}, PLOT_INTERVAL);    
		},
		cache: false
	});
}
var liveChart;
function buildNewLiveUtilGraph(objType, objName){
	var label1 = (objType == 'flow') ? 'bytes' : 'CPU';
	var label2 = (objType == 'flow') ? 'packets' : 'Memory';
	var title1 = (objType == 'flow') ? 'flow information' : 'Server Resource Utilization';
	var unit = (objType == 'flow') ? '' : '%';
	
	liveChart = new Highcharts.Chart({
		colors: ['#058DC7', '#50B432', '#ED561B', '#DDDF00', '#24CBE5', '#64E572', '#FF9655', '#FFF263', '#6AF9C4'],
		chart: {
			renderTo: 'util-chart-container',
			defaultSeriesType: 'spline',
			zoomType: 'xy',
			events: {
				load: requestData(objType, objName)
			}
		},
		plotOptions:{ series: { marker: { radius: 0}}},
		title: {text: title1},
		xAxis: {
			title: {text: 'Last Minute'},
			labels: {style: {display:'none'},},
		},
		yAxis: {
			min:0,
			//max:100,
			title : {style: {display:'none'},}, 
			labels: {formatter: function() { return this.value +unit;},}
		},
		series: [{
				name: label1,
				data: Array.apply(null, new Array(MAX_PLOT_POINTS)).map(Number.prototype.valueOf,-1)
			}, {
				name: label2,
				data: Array.apply(null, new Array(MAX_PLOT_POINTS)).map(Number.prototype.valueOf,-1)
			}]
	});        
}










// Builds a graph showing varying number of VMs
function buildNumVMGraph(series) {
	var util = new Highcharts.Chart({
		colors: ['#058DC7', '#50B432', '#ED561B', '#DDDF00', '#24CBE5', '#64E572', '#FF9655', '#FFF263', '#6AF9C4'],
		chart: {
			renderTo: 'util-chart-container',
			type: 'spline',
			zoomType: 'xy',
		},
		title: {text: 'Server Resource Utilization'},
		xAxis: {
			title: {text: 'Last 10 Minutes'},
			labels: {style: {display:'none'},},
		},
		yAxis: {
			title : {style: {display:'none'},}, 
			labels: {formatter: function() { return this.value +'%';},}
		},
		tooltip: {formatter: function() {return '' + this.y + '%'}},
		series: [{	
				name: 'CPU',
				data: cpu
			}, {	
				name: 'Memory',
				data: mem
			}],

	});
}

function buildMigGraph(names) {
	var util = new Highcharts.Chart({
		colors: ['#058DC7', '#50B432', '#ED561B', '#DDDF00', '#24CBE5', '#64E572', '#FF9655', '#FFF263', '#6AF9C4'],
		chart: {
			renderTo: 'mig-chart-container',
			type: 'spline',
			zoomType: 'xy',
		},
		title: {text: 'Server Locations'},
		xAxis: {
			title: {text: 'Last 10 Servers'},
		},
		yAxis: {
			title : {style: {display:'none'},}, 
		},
		tooltip: {formatter: function() {return '' + this.y + '%'}},
		series: [{	
				name: 'Names',
				data: names 
			}],

	});
}
