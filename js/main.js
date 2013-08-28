(function () {
    var isInExcludingList = function isInExcludingList(element, list) {
        return ($.inArray(element, list) > -1);
    }

    var ignoredNodeAttributes = ['x', 'y', 'index', 'weight', 'px', 'py', 'type'];

    var node_info_row = function node_info_row(display_name, value){
        var $div = $('<div class="row clearfix"></div>')
        var $label = $('<label class="pull-left" style="text-align:right !important;">' + display_name + ':</label>');
        var $ins = $('<span class="pull-right" style="margin-left: 5px; text-align: left; width: 100px;"><p>' + value + '</p></div>');
        $div.append($label);
        $div.append($ins);

        return $div;
    };

     // var c = [-1];
    // for(key in colorTypes) {
    //  c.push(key);
    // }

    // generate color chart...
    //var colors = d3.scale.linear().domain([d3.min(c), d3.max(c)]).range([opts.startingColor, opts.endingColor]);
    var tracked_nodes = [];
    var tracked_node_color = "#FF0000";

    var getColor = function getColor(node, check_tracked_nodes) {
        //console.log(node.role);
        //console.log(node[opts.colorField]);
        // there is not a point to distinguish PI... a person can be PI on one grant but co-i on another
        var c = '#cccccc'; //node[opts.colorField];//node.ctsa ? '#ADFF2F' : node[opts.colorField] || -1;
        // if (node.ctsa && node.role != 'Principal Investigator') {
        //     c = '#ADFF2F';
        // } else if (node.ctsa && node.role == 'Principal Investigator') {
        //     c = '#FFFF00';
        // } else if (!node.ctsa && node.role == 'Principal Investigator') {
        //     c = '#800080';
        // }
        if (node.ctsa) {
            c = '#ADFF2F';
        }

        if(check_tracked_nodes) {

            if ($.inArray(node['name'], tracked_nodes) > -1) {
                c = tracked_node_color;
                return c;
            }
        }
        //console.log(colors(c));
        return c;
    }

    var render_tracked_nodes_sidebar = function render_tracked_nodes_sidebar() {
        var $div = $('#tracked-nodes');
        $div.empty();
        $.each(tracked_nodes, function(i, v){
            $div.append($('<div class="clearfix">' + v + '</div>'))
        });

    };

    var toggle_tracked_node = function(node, node_element, original_color, original_size) {
        var exist = false;
        var color = original_color; // original node color before being tracked
        var size = original_size;
        tracked_nodes = $.grep(tracked_nodes, function(node_id){
            if (node_id == node['name']){
                exist = true;
                return false;
            }else{
                return true;
            }
        });

        if(!exist) {
            tracked_nodes.push(node['name']);
            color = tracked_node_color;
            size = original_size * 1.5;
        }
        node_element.style("fill",color);
        node_element.attr("r",size);
        render_tracked_nodes_sidebar();
    };
   

    var d3_draw = function d3_draw(activeNetwork, opts) {

        var z = d3.scale.category20c();

        var default_opts = {
            where: "#canvas",
            r: 10,
            width: 1000,
            height: 1000,
            charge: -80,
            gravity: 0.15,
            linkDistance: 20,
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

        d3.json('data/' + activeNetwork + ".json", function (error, graph) {

            var link_tracks = {}, colorTypes = {};
            // Compute the distinct nodes from the links.
            graph.links.forEach(function (link) {
                var t = 'basic';
                if (link.source == link.target) {
                    // These are for rendering self reference.  The 'null' vertex is a secret extra vertex.
                    t = 'self-loop';
                    link.source = link.source + "-null";
                    link.source.type = t;
                }

                link.type = t;
                // add the secret nodes, if link.source doesn't exist
                link.source = graph.nodes[link.source] || (graph.nodes[link.source] = {
                    name: link.source,
                    type: t
                });
                link.target = graph.nodes[link.target]; // || (graph.nodes[link.target] = {name: link.target});



                link_tracks[link.source.index + "," + link.target.index] = 1;

                // figure out the number of distince color types we need...
                if (typeof link.source[opts.colorField] != 'undefined') {

                    colorTypes[link.source[opts.colorField]] = 1;
                }
            });

           



            var isConnected = function isConnected(e, t) {
                return link_tracks[e.index + "," + t.index] || link_tracks[t.index + "," + e.index] || e.index === t.index;
            };

            var force = d3.layout.force()
                .nodes(d3.values(graph.nodes))
                .links(graph.links)
                .linkStrength(function (d) {
                    return (d.type == "self-loop" ? 1 : 0.5);
                })
                .size([opts.width, opts.height])
                .linkDistance(function (d) {
                    return (d.type == "self-loop" ? opts.selfLoopLinkDistance : opts.linkDistance);
                })
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
                .attr("class", function (d) {
                    return "link " + d.type;
                })
                .attr("style", function (d) {
                    // edge width based on weight
                    return 'stroke-width: ' + d.weight + 'px !important;'
                })
                .attr("marker-end", function (d) {
                    return "url(#" + d.type + ")";
                });


            var mouseover_func = function mouseover_func(node) {

                return circle.style("opacity", function (otherNode) {
                    return isConnected(node, otherNode) ? opts.mousedOverNodeOpacity : opts.fadedOpacity
                }), path.style("opacity", function (p) {
                    return p.source === node || p.target === node ? opts.mousedOverLinkOpacity : opts.fadedOpacity;
                });
            };

            var mouseout_func = function mouseout_func(node) {
                return circle.style("fill", function (node) {
                    return getColor(node);
                }).attr("r", function (d) {
                    return ($.inArray(d['name'], tracked_nodes) > -1) ? opts.r * 1.5:opts.r; //d.ctsa == 1 && d.role == 'Principal Investigator'?opts.r * 1.5:opts.r;
                }).style("stroke", opts.nodeStrokeColor).style("stroke-width", opts.nodeStrokeWidth).call(force.drag).style("opacity", opts.nodeOpacity), path.style("opacity", opts.linkOpacity);
            }


            var circle = svg.append("svg:g").selectAll("circle")
                .data(force.nodes())
                .enter().append("svg:circle")
                .attr("r", function (d) {

                    return ($.inArray(d['name'], tracked_nodes) > -1) ? opts.r * 1.5:opts.r;
                    //return d.ctsa == 1 && d.role == 'Principal Investigator'?opts.r * 1.5:opts.r; // need to figure out a better way to do this...
                })
                .call(force.drag)
                .attr("class", function (d) {
                    var c = d.type || '';
                    if (d.ctsa) c = c + ' ctsa';
                    for (var key in d) {
                        if (!isInExcludingList(key, ignoredNodeAttributes)) {
                            c = c + ' ' + key + '-' + d[key];
                        }
                    }

                    return c;
                }).style("fill", function (node) {
                    return getColor(node, true);
                }).on("click", function(node){

                    toggle_tracked_node(node, d3.select(this), getColor(node), opts.r);
                    console.log(tracked_nodes);
                }).on("mouseover", function (node) {
                    return mouseover_func(node);
                }).on("mouseout", function (node) {
                    return mouseout_func(node);
                }).tooltip(function (d, i) {
                    var r; //, svg;
                    r = +d3.select(this).attr('r');
                    //svg = d3.select(document.createElement("svg")).attr("height", 50);
                    //g = svg.append("g");
                    //g.append("rect").attr("width", r * 10).attr("height", 10);
                    //g.append("text").text("10 times the radius of the cirlce").attr("dy", "25");
  //                   <div class="form-group">
  //   <label class="col-lg-2 control-label">Email</label>
  //   <div class="col-lg-10">
  //     <p class="form-control-static">email@example.com</p>
  //   </div>
  // </div>
                    var $content = $('<div class="container"></div>');
                    $content.append(node_info_row('ID', d['name']));
                    $content.append(node_info_row('Department', d['department'].toLowerCase().replace(/\b[a-z]/g, function(letter) {
                        return letter.toUpperCase();
                    })));
                    $content.append(node_info_row('CTSA-supported?', (d['ctsa'] == 1?'Yes':'No')));
                    $content.append(node_info_row('Degree', d['degree']));
                    $content.append(node_info_row('Strength', d['strength']));
                    $content.append(node_info_row('Betweenness', d['betweenness']));
                    $content.append(node_info_row('Closeness', d['closeness']));
                    $content.append(node_info_row('Eigen Centrality', d['evcent']));
                    $content.append(node_info_row('Clustering Coefficient', d['clustering_coefficient']));

                    return {
                        type: "popover",
                        title: "Node Information",
                        content: $content,
                        detection: "shape",
                        placement: "mouse",
                        gravity: "right",
                        position: [d.x, d.y],
                        displacement: [r + 2, -155],
                        mousemove: true
                    };
                });

            var text = svg.append("svg:g").selectAll("g")
                .data(force.nodes())
                .enter().append("svg:g")
                .attr("class", function (d) {
                    return d.type
                });

            // var show_id = false;
            //  // only show a label if the node is being tracked
            // if ($.inArray(d['name'], tracked_nodes) > -1) {
            //     show_id = true;
            // }
            //     // A copy of the text with a thick white stroke for legibility.
            //     text.append("svg:text")
            //         .attr("x", 8)
            //         .attr("y", ".31em")
            //         .attr("class", "shadow")
            //         .attr("class", function (d) {
            //             return d.type
            //         })
            //         .text(function (d) {
            //             return show_id?d.name:'';
            //         });

            //     text.append("svg:text")
            //         .attr("x", 8)
            //         .attr("y", ".31em")
            //         .attr("class", function (d) {
            //             return d.type
            //         })
            //         .text(function (d) {
            //              return show_id?d.name:'';
            //         });

            function tick() {

                path.attr("d", function (d) {
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
                        a = Math.atan2(dx, dy);
                        da = 0.4;
                        b = 1;
                        return "M" + d.target.x + "," + d.target.y + "q" +
                            b * dr * Math.sin(a) + "," + b * dr * Math.cos(a) + " " +
                            b * dr * Math.sin(a + da) + "," + b * dr * Math.cos(a + da) + " " + " T " + d.target.x + "," + d.target.y;
                    }
                })
                    .attr("x1", function (d) {
                        return d.source.x;
                    })
                    .attr("y1", function (d) {
                        return d.source.y;
                    })
                    .attr("x2", function (d) {
                        return d.target.x;
                    })
                    .attr("y2", function (d) {
                        return d.target.y;
                    });

                circle.attr("transform", function (d) {
                    return "translate(" + d.x + "," + d.y + ")";
                });
                /*
				.attr("cx", function(d) { return d.x = Math.max(r, Math.min(w - r, d.x)); })
	        	.attr("cy", function(d) { return d.y = Math.max(r, Math.min(h - r, d.y)); });
				*/
                text.attr("transform", function (d) {
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
            s.splice(0, 1);
            ret = s.join('-');
        }

        return ret;
    };

    var getNetworkRoot = function getNetworkRoot(tag) {
        var s = tag.split('-');

        var sy = $.trim(s[0]);
        var ey = $.trim(s[1]);
        
        return sy + '-' + ey;
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
        '2006-2006': default_opts,
        '2007-2007': default_opts,
        '2008-2008': default_opts,
        '2009-2009': default_opts,
        '2010-2010': default_opts,
        '2011-2011': default_opts,
        '2012-2012': default_opts,
        '2006-2009': default_opts,
        '2010-2012': default_opts,
        '2006-2012': default_opts
    };

     var network_info_row = function node_info_row(display_name, value){
        var $div = $('<div class="row clearfix"></div>')
        var $label = $('<label class="pull-left" style="margin-left: 10px; text-align:right !important; width: 150px">' + display_name + ':</label>');
        var $ins = $('<span class="pull-right" style="margin-left: 5px; text-align: left; width: 120px;"><p>' + value + '</p></div>');
        $div.append($label);
        $div.append($ins);

        return $div;
    }; 

    var createNav = function createNavBar(activeNetwork) {

        $ul = $('<ul class="nav navbar-nav"></ul>');

        var ditems = {
            'largest-component': 'Largest Component',
            'complete': 'Complete Network'
        };

        $.each(networkfiles, function (current) {

            if (current == getNetworkRoot(activeNetwork)) {
                $li = $('<li class="dropdown active"></li>');
            }else{
                $li = $('<li class="dropdown"></li>');
            }
            

            $a = $('<a href="#" style="display:inline-block;padding-right:0px;" tag="' + current + '">' + parseNavText(current) + '</a>').click(function () {
                var tag = $(this).attr('tag');
                $('#canvas > svg').hide('slow', function () {
                    $('#canvas > svg').remove();
                    d3_draw(tag, networkfiles[tag]);
                    createNav(tag);
                });
            });


            $li.append($a);

            $dropdown_toggle_a = $('<a href="#" class="dropdown-toggle" data-toggle="dropdown" style="display:inline-block;padding-left:5px;"><b class="caret"></b></a>');

            $li.append($dropdown_toggle_a);

            $dul = $('<ul class="dropdown-menu"></ul>');

            $.each(ditems, function (menu) {
                $action_li = $('<li></li>');
                $action_a = $('<a href="#" tag="' + current + '-' + menu + '">' + ditems[menu] + '</a>').click(function () {
                    var tag = $(this).attr('tag');
                    $('#canvas > svg').hide('slow', function () {
                        $('#canvas > svg').remove();
                        d3_draw(tag, networkfiles[tag]);
                        createNav(tag);
                    });
                });
                $action_li.append($action_a);
                $dul.append($action_li);
            });

            $li.append($dul);

            $ul.append($li);
        });

        $('#nav-bar').html($ul);

        var $network_info_div = $('#network-characteristics');
        $network_info_div.empty();
        d3.json('data/' + getNetworkRoot(activeNetwork) + "-info.json", function (error, network_info) {
            $network_info_div.append(network_info_row('FY', parseNavText(getNetworkRoot(activeNetwork))));
            $network_info_div.append(network_info_row('# of Nodes', network_info['vs']));
            $network_info_div.append(network_info_row('# of Edges', network_info['es']));
            $network_info_div.append(network_info_row('Avg # of New Edges', network_info['avg_new_edges']));
            $network_info_div.append(network_info_row('# of Edges', network_info['isolated_components']));

            $network_info_div.append($('<div class="row clearfix divider"><hr/></div>'));
            $network_info_div.append($('<div class="clearfix title "><b>Largest Component:</b></div>'));

            $network_info_div.append(network_info_row('# of Nodes', network_info['largest_component']['vs']));
            $network_info_div.append(network_info_row('# of Edges', network_info['largest_component']['es']));
            $network_info_div.append(network_info_row('C (unweighted)', network_info['largest_component']['c_g']));
            $network_info_div.append(network_info_row('C (weighted)', network_info['largest_component']['c_wg']));
            //$network_info_div.append(network_info_row('C (triplets definition)', network_info['largest_component']['c_tg']));
            $network_info_div.append(network_info_row('L (unweighted)', network_info['largest_component']['l_g']));
            $network_info_div.append(network_info_row('L (weighted)', network_info['largest_component']['l_wg']));

            $network_info_div.append($('<div class="row clearfix divider"><hr/></div>'));
            $network_info_div.append($('<div class="clearfix"><p><i>* C is the network <u>Clustering Coefficient</u>, and L is the network <u>Characteristic Path Length</u>.</i></p></div>'));

        });
    };

    $(document).ready(function () {

        activeNetwork = '2006-2012';

        createNav(activeNetwork);

        d3_draw(activeNetwork, networkfiles[activeNetwork]);

        render_tracked_nodes_sidebar();
    });

}).call(this);