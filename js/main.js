
var isInExcludingList = function isInExcludingList(element, list){
    return ($.inArray(element, list) > -1);
}

var ignoredNodeAttributes = ['x', 'y', 'index', 'weight', 'px', 'py', 'type'];

var d3_draw = function d3_draw(activeYear) {
	var w = 1200,
    h = 900,
    r = 6,
    z = d3.scale.category20c();

	d3.json(activeYear + ".json", function(error, graph) {
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

		  link.source.type = t;
		});

		var force = d3.layout.force()
		.nodes(d3.values(graph.nodes))
      .links(graph.links)
	    .linkStrength(function(d) { return (d.type == "self-loop"? 1 : 0.5); })
	    .size([w, h])
	    .linkDistance(function(d) { return (d.type == "self-loop"? 5 : 10); })
	    .gravity(0.30)
    	.charge(-80)
      .on("tick", tick)
      .start();

	    var svg = d3.select("#canvas").append("svg:svg")
	    .attr("width", w)
	    .attr("height", h);



	    var path = svg.append("svg:g").selectAll("path")
	    .data(force.links())
	    .enter().append("svg:path")
	    .attr("class", function(d) { return "link " + d.type; })
	    .attr("marker-end", function(d) { return "url(#" + d.type + ")"; });

	    var circle = svg.append("svg:g").selectAll("circle")
    	.data(force.nodes())
	  	.enter().append("svg:circle")
	    .attr("r", function(d) {
	    	return d.ctsa?r * 2:r;
	    })
	    .call(force.drag)
	    .attr("class",function(d){
	    	var c = d.type;
	    	if (d.ctsa) c = c + ' ctsa';
	    	for (var key in d) {
	    		if(!isInExcludingList(key, ignoredNodeAttributes)) {
	    			c = c + ' ' + key + '-' + d[key];
	    		}
	    	}
	    	
	    	return c;
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

var createNav = function createNavBar(activeYear) {

		$ul = $('<ul class="breadcrumb"></ul>');

		for(var i = 2005; i < 2013; i++){
			$li = $('<li></li>');
			if(activeYear == i){
				$li.addClass('active');
				$li.text(i);
			}else{
				$a = $('<a href="#">' + i + '</a>').click(function(){
					var y = $(this).text();
					$('#canvas > svg').hide('slow', function(){
						$('#canvas > svg').remove();
						d3_draw(y);
						createNav(y);
					});				
				});
				$li.append($a);			
			}
			$li.append($('<span class="divider">/</span>'));
			$ul.append($li);
			
		}
		$('#nav-bar').html($ul);
	};


$(document).ready(function(){

	activeYear = 2005;

	createNav(activeYear);

	d3_draw(activeYear);

	

});

