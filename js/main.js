(function () {
var isInExcludingList = function isInExcludingList(element, list){
    return ($.inArray(element, list) > -1);
}

var ignoredNodeAttributes = ['x', 'y', 'index', 'weight', 'px', 'py', 'type'];

var d3_draw = function d3_draw(activeNetwork, opts) {

    var z = d3.scale.category20c();

    var default_opts = {
            where: "#canvas",
            r: 10,
            width: 1200,
            height: 1200,
            charge: -80,
            gravity: 0.10,
            linkDistance: 30,
            selfLoopLinkDistance: 20,
            nodeOpacity: .9,
            linkOpacity: .85,
            fadedOpacity: .1,
            mousedOverNodeOpacity: .9,
            mousedOverLinkOpacity: .9,
            nodeStrokeWidth: 1.5,
            nodeStrokeColor: "#333",
            colorField: "color",
            startingColor: "#ccc",
            endingColor: "#BD0026"
    }, opts = $.extend({}, default_opts, opts);

	d3.json('data/' + activeNetwork + ".json", function(error, graph) {

		var link_tracks = {}, colorTypes = {};
		// Compute the distinct nodes from the links.
		graph.links.forEach(function(link) {
		  var t = 'basic';
		  if (link.source == link.target) {
		  	// These are for rendering self reference.  The 'null' vertex is a secret extra vertex.
		  	t = 'self-loop';
		  	link.source = link.source+"-null";
		  	link.source.type = t;
		  }
		  
		  link.type = t;
		  // add the secret nodes, if link.source doesn't exist
		  link.source = graph.nodes[link.source] || (graph.nodes[link.source] = {name: link.source, type: t});
		  link.target = graph.nodes[link.target]; // || (graph.nodes[link.target] = {name: link.target});
		  


		  link_tracks[link.source.index + "," + link.target.index] = 1;

		  // figure out the number of distince color types we need...
		  if (typeof link.source[opts.colorField] != 'undefined' ) {

		  	colorTypes[link.source[opts.colorField]] = 1;
		  }		  
		});

		var c = [-1];
		for(key in colorTypes) {
			c.push(key);
		}

		// generate color chart...
		var colors = d3.scale.linear().domain([d3.min(c), d3.max(c)]).range([opts.startingColor, opts.endingColor]);

		var isConnected = function isConnected(e, t){
			return link_tracks[e.index + "," + t.index] || link_tracks[t.index + "," + e.index] || e.index === t.index;
		};

		var force = d3.layout.force()
		.nodes(d3.values(graph.nodes))
	      .links(graph.links)
		    .linkStrength(function(d) { return (d.type == "self-loop"? 1 : 0.5); })
		    .size([opts.width, opts.height])
		    .linkDistance(function(d) { return (d.type == "self-loop"? opts.selfLoopLinkDistance : opts.linkDistance); })
		    .gravity(opts.gravity)
	    	.charge(opts.charge)
	      .on("tick", tick)
	      .start();

	    var svg = d3.select("#canvas").append("svg:svg")
	    .attr("width", opts.width)
	    .attr("height", opts.height);

	    var path = svg.append("svg:g").selectAll("path")
	    .data(force.links())
	    .enter().append("svg:path")
	    .attr("class", function(d) { return "link " + d.type; })
	    .attr("marker-end", function(d) { return "url(#" + d.type + ")"; });


	    var mouseover_func = function mouseover_func(e) {
	   		return circle.style("opacity", function (t) {
	            return isConnected(e, t) ? opts.mousedOverNodeOpacity : opts.fadedOpacity
	        }), path.style("opacity", function (t) {
	        	return t.source === e || t.target === e ? opts.mousedOverLinkOpacity : opts.fadedOpacity;       
	        });
	   	};

	   	var mouseout_func = function mouseout_func(e) {
	   		return circle.style("fill", function (e) {
	   			var c = e[opts.colorField] || -1;
                return colors(c);
            }).attr("r", function(d) {
	    	return d.ctsa == 1?opts.r * 2:opts.r;
	    }).style("stroke", opts.nodeStrokeColor).style("stroke-width", opts.nodeStrokeWidth).call(force.drag).style("opacity", opts.nodeOpacity), path.style("opacity", opts.linkOpacity);
	   	}


	    var circle = svg.append("svg:g").selectAll("circle")
    	.data(force.nodes())
	  	.enter().append("svg:circle")
	    .attr("r", function(d) {
	    	return d.ctsa == 1?opts.r * 2:opts.r; // need to figure out a better way to do this...
	    })
	    .call(force.drag)
	    .attr("class",function(d){
	    	var c = d.type || '';
	    	if (d.ctsa) c = c + ' ctsa';
	    	for (var key in d) {
	    		if(!isInExcludingList(key, ignoredNodeAttributes)) {
	    			c = c + ' ' + key + '-' + d[key];
	    		}
	    	}
	    	
	    	return c;
	    })
	    .on("mouseover", function (e) {
            return mouseover_func(e);
        }).on("mouseout", function (e) {
            return mouseout_func(e);
        });

	    var text = svg.append("svg:g").selectAll("g")
	    .data(force.nodes())
	    .enter().append("svg:g")
	    .attr("class",function(d){ return d.type });

		// A copy of the text with a thick white stroke for legibility.
		text.append("svg:text")
		.attr("x", 8)
		.attr("y", ".31em")
		.attr("class", "shadow")
		.attr("class",function(d){ return d.type })
		.text(function(d) { return d.name; });

		text.append("svg:text")
		.attr("x", 8)
		.attr("y", ".31em")
		.attr("class",function(d){ return d.type })
		.text(function(d) { return d.name; });


		function tick() {
			
			path.attr("d", function(d) {
			    if (d.type != "self-loop") {
			      // Use elliptical arc path segments to doubly-encode directionality.
			      var dx = d.target.x - d.source.x,
			          dy = d.target.y - d.source.y,
			          dr = Math.sqrt(dx * dx + dy * dy);
			      return "M" + d.source.x + "," + d.source.y + "A" + dr + "," + dr + " 0 0,1 " + d.target.x + "," + d.target.y;
			    } else if (d.type == "self-loop") {
			      // draw a little loop back to the self, keeping in mind that all self loops from the dummy node toward the self.
			      var dx = d.source.x - d.target.x,
			          dy = d.source.y - d.target.y,
			          dr = Math.sqrt(dx * dx + dy * dy);
			          a = Math.atan2(dx,dy);
			          da = 0.4;
			          b = 1;
			      return "M" + d.target.x + "," + d.target.y + "q" +
			        b*dr*Math.sin(a) + "," + b*dr*Math.cos(a) + " " +
			        b*dr*Math.sin(a+da) + "," + b*dr*Math.cos(a+da) + " " +  " T " + d.target.x + "," + d.target.y;      
			    }
			})
.attr("x1", function(d) { return d.source.x; })
        .attr("y1", function(d) { return d.source.y; })
        .attr("x2", function(d) { return d.target.x; })
        .attr("y2", function(d) { return d.target.y; });

			circle.attr("transform", function(d) {
				return "translate(" + d.x + "," + d.y + ")";
			});/*
			.attr("cx", function(d) { return d.x = Math.max(r, Math.min(w - r, d.x)); })
        	.attr("cy", function(d) { return d.y = Math.max(r, Math.min(h - r, d.y)); });
			*/
			text.attr("transform", function(d) {
				return "translate(" + d.x + "," + d.y + ")";
			});
		}
	});
};

var parseNavText = function parseNavText(text) {

	var s = text.split('-');
	var ret = text;

	var sy = $.trim(text.split('-')[0]);
	var ey = $.trim(text.split('-')[1]);
	if (sy == ey) {
		s.splice(0,1);
		ret = s.join('-');
	}

	return ret;
};

/*
var default_opts = {
            where: "#canvas",
            r: 10,
            width: 1200,
            height: 1200,
            charge: -80,
            gravity: 0.10,
            linkDistance: 30,
            selfLoopLinkDistance: 20,
            nodeOpacity: .9,
            linkOpacity: .85,
            fadedOpacity: .1,
            mousedOverNodeOpacity: .9,
            mousedOverLinkOpacity: .9,
            nodeStrokeWidth: 1.5,
            nodeStrokeColor: "#333",
            colorField: "color",
            startingColor: "#ccc",
            endingColor: "#BD0026"
        }
*/

var default_opts = {
	gravity: 0.25
};

var networkfiles = {
	'2005-2005': default_opts,
	'2006-2006': default_opts,
	'2007-2007': default_opts,
	'2008-2008': default_opts,
	'2009-2009': default_opts,
	'2009-2009-simplified': {
		gravity: 0.10
	},
	'2010-2010': default_opts,
	'2011-2011': default_opts,
	'2012-2012': default_opts,
	'2005-2008': default_opts,
	'2009-2012': default_opts
};
var createNav = function createNavBar(activeNetwork) {

		$ul = $('<ul class="breadcrumb"></ul>');

		$.each(networkfiles, function(current){

			$li = $('<li></li>');
			if(activeNetwork == current){
				$li.text(parseNavText(current));
			}else{
				$a = $('<a href="#" tag="' + current + '">' + parseNavText(current) + '</a>').click(function(){
					var y = $(this).attr('tag');
					$('#canvas > svg').hide('slow', function(){
						$('#canvas > svg').remove();
						d3_draw(y, networkfiles[y]);
						createNav(y);
					});				
				});
				$li.append($a);			
			}
			$li.append($('<span class="divider">/</span>'));
			$ul.append($li);
		});

		$('#nav-bar').html($ul);
	};


$(document).ready(function(){

	activeNetwork = '2009-2009-simplified';

	createNav(activeNetwork);

	d3_draw(activeNetwork, networkfiles[activeNetwork]);

	

});

}).call(this);

