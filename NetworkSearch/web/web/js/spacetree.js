var labelType, useGradients, nativeTextSupport, animate;
var typeColors = {'vm':'#33a', 'server':'#55b', 'customer':'#77c', 'network_interface':'#99d', 'user':'#aae', 'process':'#bf0', 'file':'#cf5'};
	//,'#dfa', '#faccff', '#ffccff', '#CCC', '#C37'}; 
var st;


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


function createNewSubtree(id, objType, server) {
	$.ajax({
		url:'/tree',
		data: {	'startQuery': objType + '-name=' + id + ' object-type=' + objType + (server ? ' server-name=' + server : ''),
			'ajax':true,
			'treeType':'spacetree',
			},
		context: id,
	}).done(function( data ) {
		alert(this + ' ' + data.length)
		var children = JSON.parse(data)
		//st.addSubtree({'id':id, 'name':id, 'data':{}, 'children':children}, 'animate', {
            	//	hideLabels: false,
            	//	onComplete: function() {
                //	Log.write("subtree added");
            	//	}
        	//});
	})
}

function newSubTreeResp(id, tree) {
}

function addText() {
	var treeDesc = 'This animation is to show how to form a link from one object to another.'
	$('#selectionType').show()
	$('#tree-description').append(treeDesc)
}

function init(){
	addText()
    
    //preprocess subtrees orientation
    var arr = json.children, len = arr.length;
    for(var i=0; i < len; i++) {
    	//split half left orientation
      if(i < len / 2) {
    		arr[i].data.$orn = 'left';
    		$jit.json.each(arr[i], function(n) {
    			n.data.$orn = 'left';
    		});
    	} else {
    	//half right
    		arr[i].data.$orn = 'right';
    		$jit.json.each(arr[i], function(n) {
    			n.data.$orn = 'right';
    		});
    	}
    }
    //end
    //grab radio button
    var normal = $jit.id('s-normal');
	var width = 115
    //init Spacetree
    //Create a new ST instance
    st = new $jit.ST({
        //id of viz container element
        injectInto: 'infovis',
        //multitree
    	  multitree: true,
        //set duration for the animation
        duration: 800,
        //set animation transition type
        transition: $jit.Trans.Quart.easeInOut,
        //set distance between node and its children
        levelDistance: 40,
        //sibling and subtrees offsets
        siblingOffset: 3,
        subtreeOffset: 3,
        //set node and edge styles
        //set overridable=true for styling individual
        //nodes or edges
        Node: {
            height: 14,
            width: width,
            //type: 'ellipse',
            color: '#aaa',
            overridable: true,
            //set canvas specific styles
            //like shadows
            //CanvasStyles: {
            //  shadowColor: '#ccc',
            //  shadowBlur: 10
            //}
        },
        Edge: {
            type: 'bezier',
            overridable: true
        },
        
        onBeforeCompute: function(node){
            Log.write("loading " + node.name);
        },
        
        onAfterCompute: function(){
            Log.write("done");
        },
        
        //This method is called on DOM label creation.
        //Use this method to add event handlers and styles to
        //your node.
        onCreateLabel: function(label, node){
            label.id = node.id;            
            label.innerHTML = node.name;
            label.onclick = function(){
            	if(normal.checked) {
                	st.onClick(node.id);
            	} else {
               		st.setRoot(node.id, 'animate');
            	}

		if (false && node.data.object_type) {
			var startQuery = 'object-type=' + node.data.['object-type']//+ (server ? ' server-name=' + server : ''),
			startQuery += ' ' +  node.data['object-type'] + '-name=' + node.id//.substr(0,node.id.indexOf('_'))
			$.ajax({
				url:'/tree',
				data: {	'startQuery': startQuery,
					'ajax':true,
					'treeType':'spacetree',
					},
			}).done(function( data ) {
				var children = JSON.parse(data)
				var subTree =	{	'id':label.id, 
							'name':'testSubtree', 
							'data':{}
						}
				var fakeChildren = [{
								id: "node4101",
								name: "4.101",
								data: {},
								children: []
							    }, {
								id: "node4102",
								name: "4.102",
								data: {},
								children: []
							    }]
				var nodes = {	'id'	: 'fakeNodes',
						'name'	: 'fakeNodes',
						'data'	: {},
						'children' : fakeChildren }
					
				//subTree.children = children
				subTree.children = [nodes]
				st.addSubtree(subTree, 'animate', {hideLabels: false});
			})
		}
            };
		
            //set label styles
            var style = label.style;
            style.width = width + 'px';
            style.height = 14 + 'px';            
            style.cursor = 'pointer';
            style.color = '#333';
            style.fontSize = '10px';
            style.textAlign= 'center';
            style.paddingTop = '1px';
        },
        
        //This method is called right before plotting
        //a node. It's useful for changing an individual node
        //style properties before plotting it.
        //The data properties prefixed with a dollar
        //sign will override the global node style properties.
        onBeforePlotNode: function(node){
            //add some color to the nodes in the path between the
            //root node and the selected node.

		if (false && 'object-type' in node.data && node.data['object-type'] in typeColors){
			node.data.$color = typeColors[node.data['object-type']]
		    }
            else if (node.selected) {
                node.data.$color = "#69f";
            }
            else {
                delete node.data.$color;
                //if the node belongs to the last plotted level
                if(!node.anySubnode("exist")) {
                    //count children number
                    var count = 0;
                    node.eachSubnode(function(n) { count++; });
                    //assign a node color based on
                    //how many children it has
	      	    node.data.$color = ['#aaa', '#baa', '#caa', '#daa', '#eaa', '#faa'][count % 6];                    
                }
            }
        },
        
        //This method is called right before plotting
        //an edge. It's useful for changing an individual edge
        //style properties before plotting it.
        //Edge data proprties prefixed with a dollar sign will
        //override the Edge global style properties.
        onBeforePlotLine: function(adj){
            if (adj.nodeFrom.selected && adj.nodeTo.selected) {
                adj.data.$color = "#eed";
                adj.data.$lineWidth = 3;
            }
            else {
                delete adj.data.$color;
                delete adj.data.$lineWidth;
            }
        }
    });
    //load json data
    st.loadJSON(json);
    //compute node positions and layout
    st.compute('end');
    st.select(st.root);
    //end
}

