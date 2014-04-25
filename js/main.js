(function () {

    var getNetworkRoot = function getNetworkRoot(tag) {
        var s = tag.split('-');

        var sy = $.trim(s[0]);
        var ey = $.trim(s[1]);

        return sy + '-' + ey;
    };

    $('#force-gravity').slider({
          formater: function(value) {
            return 'Current value: '+parseFloat(value)/100;
          }
        });

    $('#force-charge').slider({
          formater: function(value) {
            return 'Current value: '+value;
          }
        });

    $('#force-link-distance').slider({
          formater: function(value) {
            return 'Current value: '+value;
          }
        });


    $('#prediction_top_n').slider({
          formater: function(value) {
            return 'Top '+ value + '% predictions';
          }
        });

    //$('#opt_drilling_prediction').tooltip();

    var user_options = {        
        highlight_ctsa: true,
        centrality_leader: false,
        tracking: false,
        drilling: true,
        tooltip: true,
        connected: false,
        prediction: {
            on: false,
            val: 0.01
        }
    };

    

    var isInExcludingList = function isInExcludingList(element, list) {
        return ($.inArray(element, list) > -1);
    }

    var ignoredNodeAttributes = ['x', 'y', 'index', 'weight', 'px', 'py', 'type'];

    var info_row = function info_row(display_name, value){
        var $div = $('<div class="row clearfix"></div>')
        var $label = $('<label class="pull-left" style="margin-left: 10px; text-align:right !important; width: 150px">' + display_name + ':</label>');
        var $ins = $('<span class="pull-right" style="margin-left: 5px; text-align: left; width: 100px;"><p>' + value + '</p></div>');
        $div.append($label);
        $div.append($ins);

        return $div;
    };

    // generate color chart...
    //var colors = d3.scale.linear().domain([d3.min(c), d3.max(c)]).range([opts.startingColor, opts.endingColor]);
    var tracked_nodes = [];
    var tracked_node_color = "#FF0000";

    var isCentralityLeader = function isCentralityLeader(node){
        return (node.centrality_leader > 0 && node.centrality_leader < 11);
    }

    var getColor = function getColor(node, check_tracked_nodes) {
        //console.log(node.role);
        //console.log(node[opts.colorField]);
        // there is not a point to distinguish PI... a person can be PI on one grant but co-i on another
        var c = '#cccccc'; //node[opts.colorField];//node.ctsa ? '#ADFF2F' : node[opts.colorField] || -1;

        if (node.ctsa && user_options.highlight_ctsa) {
            c = '#5cb85c';//'#ADFF2F';
        }

        if(check_tracked_nodes) {

            if ($.inArray(node['name'], tracked_nodes) > -1) {
                c = tracked_node_color;
                return c;
            }
        }

        if(isCentralityLeader(node) && user_options.centrality_leader){
            c = '#ADFF2F';
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

    var toggle_tracked_node = function toggle_tracked_node(node, node_element, original_color, original_size) {
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

    var default_opts = {
            where: "#canvas",
            r: 10,
            width: 1000,
            height: 1000,
            charge: -80,
            gravity: 0.25,
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
        };

    var network_opts = {
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

    var current_complete_graph;
    var current_focuse_node;

    var drilling_control = {
        in_progress: false,
        click_hack: 200
    };

    var find_node = function find_node(nodes, name) {

        var found;

        nodes.forEach(function(node){
            if(node.name == name) {
                found = node;
            }
        })

        return found;
    };

    var find_link = function find_link(links, names) {
        var found;

        var source_name = names[0], target_name = names[1];

        links.forEach(function(link){

            if((link.source.name == source_name && link.target.name == target_name) || (link.source.name == target_name && link.target.name == source_name)){
                found = link;
            }
        });

        return found;
    };

    var filter_graph = function filter_graph(focus_node, complete_graph) {
        //node.focused = !node.focused;

        var links = [], nodes = [];

        var keep = [];

        var c_focus_node;


        complete_graph.nodes.some(function(node){
            if(node.name == focus_node.name){
                c_focus_node = $.extend(true, {}, node);
                return true;
            }
            return false;
        });


        if(!c_focus_node) {
            alert("The focused node does not exist in this snapshot... Reset and try another one...");
            console.log("The focused node does not exist in this snapshot... Reset and try another one...");
            return $.extend(true, {}, complete_graph);
        }

        // find all nodes that links to the focus node...
        complete_graph.links.forEach(function(link){

            if(link.source == c_focus_node.index || link.target == c_focus_node.index){
                //links.push($.extend(true, {}, link));
                if($.inArray(link.source, keep) == -1) {
                    var newNode = $.extend(true, {}, complete_graph.nodes[link.source]);
                    newNode.focused = (c_focus_node.name == newNode.name);
                    nodes.push(newNode);
                    keep.push(link.source);
                }

                if($.inArray(link.target, keep) == -1) {
                    var newNode = $.extend(true, {}, complete_graph.nodes[link.target]);
                    newNode.focused = (c_focus_node.name == newNode.name);
                    nodes.push(newNode);
                    keep.push(link.target);
                }

            }
        });

        //make up the links that are between nodes in this list...
        complete_graph.links.forEach(function(link){
            if($.inArray(link.source, keep) > -1 && $.inArray(link.target, keep) > -1) {
                links.push({
                    source: find_node(nodes, complete_graph.nodes[link.source].name),
                    target: find_node(nodes, complete_graph.nodes[link.target].name),
                    weight: link.weight
                });
            }
        });

        return {
            links: links,
            nodes: nodes
        };

    };

    var get_graph = function get_graph(graph, opts) {

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

        return {
            graph: graph,
            link_tracks: link_tracks,
            colorTypes: colorTypes
        };
    };

    var replace_graph = function replace_graph(graph, new_graph) {
        graph.nodes.splice(0, graph.nodes.length);
        graph.links.splice(0, graph.links.length);

        [].push.apply(graph.nodes, new_graph.nodes);
        [].push.apply(graph.links, new_graph.links);
    };

    //add predicted links to current_graph and update graph
    var add_predicted_links = function add_predicted_links(graph, current_complete_graph, rwrs, confidence) {

        var gg = $.extend(true, {}, current_complete_graph);

        var ss = [];

        for (var key in rwrs) {
            ss.push(rwrs[key]);
        }

        ss.sort();

        ss.reverse();

        var ti = parseInt(parseFloat(confidence)/100 * ss.length);

        var threshold = ss[ti];

        for (var key in rwrs) {
            if(rwrs[key] >= threshold) {
                var names = key.split(',');

                var source = find_node(graph.nodes, names[0]), target = find_node(graph.nodes, names[1]);

                if (source && target && !find_link(graph.links, names)) {

                    graph.links.push({
                        source: find_node(graph.nodes, names[0]),
                        target: find_node(graph.nodes, names[1]),
                        type: "basic",
                        weight: 1,
                        predicted: true
                    });
                }
            }
        }

    };

    var d3_draw = function d3_draw(activeNetwork) {

        var z = d3.scale.category20c();

        //var opts = $.extend({}, default_opts, opts);
        var opts = network_opts[getNetworkRoot(activeNetwork)];

        var draw_graph = function draw_graph(graph) {

            var rg = get_graph(graph, opts);

            var graph = rg.graph, link_tracks = rg.link_tracks, colorTypes = rg.colorTypes;

            var isConnected = function isConnected(e, t) {
                return link_tracks[e.index + "," + t.index] || link_tracks[t.index + "," + e.index] || e.index === t.index;
            };

            graph.nodes = d3.values(graph.nodes);

            var force = d3.layout.force()
                .nodes(graph.nodes)
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
                .on("tick", tick);

            d3.select('svg').remove();
            var svg = d3.select("#canvas").append("svg:svg")
                .attr("width", opts.width)
                .attr("height", opts.height);

            var path = svg.append("svg:g").selectAll("path"),
                circle = svg.append("svg:g").selectAll("circle"),
                text = svg.append("svg:g").selectAll("text");


            var update = function update() {
                path = path.data(force.links());

                var pathEnter = path.enter().append("svg:path");


                path.attr("class", function (d) {
                        return "link " + d.type + (d.predicted?" predicted":"");
                    })
                    .attr("style", function (d) {
                        // edge width based on weight
                        return 'stroke-width: ' + (d.predicted?5:d.weight) + 'px !important;'
                    })
                    .attr("marker-end", function (d) {
                        return "url(#" + d.type + ")";
                    });

                path.exit().remove();


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

                circle = circle.data(force.nodes());

                var circleEnter = circle.enter().append("svg:circle")
                    .call(force.drag);

                circle.on("click", function(node){
                        if(user_options.tracking){
                            toggle_tracked_node(node, d3.select(this), getColor(node), opts.r);
                            //console.log(tracked_nodes);
                        }

                        if(user_options.drilling) {


                            setTimeout(function(){
                                if (!drilling_control.in_progress) {
                                    drilling_control.in_progress = true;
                                }
                                current_focuse_node = $.extend(true, {}, node);

                                replace_graph(graph, filter_graph(node, current_complete_graph));

                                update();
                            },drilling_control.click_hack);
                        }
                    }).on("dblclick", function(node){


                    });

                    if(user_options.connected) {
                        circle.on("mouseover", function (node) {
                        return mouseover_func(node);
                        }).on("mouseout", function (node) {
                            return mouseout_func(node);
                        });
                    }

                    if(user_options.tooltip) {
                        circle.tooltip(function (d, i) {

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
                            
                            var $content = $('<div></div>');
                            $content.append(info_row('ID', d['name']));
                            $content.append(info_row('Department', d['department'].toLowerCase().replace(/\b[a-z]/g, function(letter) {
                                return letter.toUpperCase();
                            })));
                            $content.append(info_row('CTSA-supported?', (d['ctsa'] == 1?'Yes':'No')));
                            $content.append(info_row('Degree', d['degree']));
                            $content.append(info_row('Strength', d['strength']));
                            $content.append(info_row('Betweenness', d['betweenness']));
                            $content.append(info_row('Closeness', d['closeness']));
                            $content.append(info_row('Eigen Centrality', d['evcent']));
                            $content.append(info_row('Clustering Coeff', d['clustering_coefficient']));

                            return {
                                type: "popover",
                                title: "Node Information",
                                content: $content,
                                detection: "shape",
                                placement: "mouse",
                                gravity: "right",
                                position: [d.x, d.y],
                                displacement: [r + 2, -155],
                                mousemove: true,
                                class: "node-info"
                            };
                        });
                    }


                circle.attr("r", function (d) {

                        if(user_options.centrality_leader){
                            var factor = 1.0;

                            if(isCentralityLeader(d)) {
                                factor = parseFloat(11 - d.centrality_leader) / 5 * 2;
                            }
                            return opts.r * factor;
                        }else{
                            return ($.inArray(d['name'], tracked_nodes) > -1 || d.focused) ? opts.r * 1.5:opts.r;
                        }
                        //return d.ctsa == 1 && d.role == 'Principal Investigator'?opts.r * 1.5:opts.r; // need to figure out a better way to do this...
                    })
                    .attr("class", function (d) {
                        var c = d.type || '';
                        if (d.ctsa) c = c + ' ctsa';
                        for (var key in d) {
                            if (!isInExcludingList(key, ignoredNodeAttributes)) {
                                c = c + ' ' + key + '-' + d[key];
                            }
                        }
                        //console.log(d);

                        return c;
                    }).style("fill", function (node) {
                        return (node.focused || node.found)?tracked_node_color:getColor(node, true);
                    })

                    // bind options to highlight ctsa nodes...
                $('#opt_highlight_ctsa').click(function(){
                    user_options.highlight_ctsa = $(this).prop('checked');
                    circle.style("fill", function (node) {
                        return getColor(node, true);
                    });
                });

                $('#opt_centrality_leader').click(function(){
                    user_options.centrality_leader = $(this).prop('checked');
                    circle.style("fill", function (node) {
                        return getColor(node, true);
                    });
                    if(user_options.centrality_leader){

                        circle.attr("r", function (d) {
                            var factor = 1.0;

                            if(isCentralityLeader(d)) {
                                factor = parseFloat(11 - d.centrality_leader) / 5 * 2;
                            }
                            return opts.r * factor;
                            //return d.ctsa == 1 && d.role == 'Principal Investigator'?opts.r * 1.5:opts.r; // need to figure out a better way to do this...
                        });

                    }else{
                        //going back to original size...
                        circle.attr("r", function (d) {

                            return ($.inArray(d['name'], tracked_nodes) > -1 || d.focused) ? opts.r * 1.5:opts.r;
                            //return d.ctsa == 1 && d.role == 'Principal Investigator'?opts.r * 1.5:opts.r; // need to figure out a better way to do this...
                        });
                    }
                    
                });

                circle.exit().remove();

                text = text.data(force.nodes());

                var textEnter = text.enter().append("svg:text");

                text.attr("class", function (d) {
                        return d.type
                    });

                var show_id = true;
                // //  // only show a label if the node is being tracked
                // // if ($.inArray(d['name'], tracked_nodes) > -1) {
                // //     show_id = true;
                // // }
                // // A copy of the text with a thick white stroke for legibility.
                // text.append("svg:text")
                //     .attr("x", 8)
                //     .attr("y", ".31em")
                //     .attr("class", "shadow")
                //     .attr("class", function (d) {
                //         return d.type
                //     })
                //     .text(function (d) {
                //         console.log(d);
                //         return show_id?d.name:'';
                //     });

                text
                    .attr("x", 8)
                    .attr("y", ".31em")
                    .attr("class", function (d) {
                        //console.log(d);
                        return d.type
                    })
                    .text(function (d) {
                        // console.log("here.........");
                        //console.log(d);
                        return show_id?d.name:'';
                        //return "here";
                    });

                text.exit().remove();


                force.start();
            }

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
                }).attr("x1", function (d) {
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

            $('#force-gravity').on('slide', function(e){
                opts.gravity = parseFloat(e.value)/100;
                $('#force-gravity-value').text(opts.gravity);
                force.gravity(opts.gravity).start();
                network_opts[getNetworkRoot(activeNetwork)] = opts;
            });

            $('#force-charge').on('slide', function(e){
                opts.charge = parseFloat(e.value);
                $('#force-charge-value').text(opts.charge);
                force.charge(opts.charge).start();
                network_opts[getNetworkRoot(activeNetwork)] = opts;
            });

            $('#force-link-distance').on('slide', function(e){
                opts.linkDistance = parseFloat(e.value);
                $('#force-link-distance-value').text(opts.linkDistance);
                network_opts[getNetworkRoot(activeNetwork)] = opts;
                force.linkDistance(opts.linkDistance).start();
            });

            $('#opt_show_prediction').click(function(){
                user_options.prediction.on = $(this).prop('checked');

                if(user_options.prediction.on){
                    d3.json('data/' + getNetworkRoot(activeNetwork) + "-rwr.json", function (error, rwrs) {

                        add_predicted_links(graph, current_complete_graph, rwrs, user_options.prediction.val);

                        update();
                    });
                }
            });

            $('#prediction_top_n').on('slideStop', function(e){
                user_options.prediction.val = parseFloat(e.value);

                //console.log(user_options);
                if(user_options.prediction.on){
                    d3.json('data/' + getNetworkRoot(activeNetwork) + "-rwr.json", function (error, rwrs) {

                        add_predicted_links(graph, current_complete_graph, rwrs, user_options.prediction.val);

                        update();
                    });
                }

            });

            $('#opt_find_btn').click(function(){
                var name_to_find = $('#opt_find_name_text').val();

                if(name_to_find){

                    setTimeout(function(){
                        graph.nodes.forEach(function(node){
                            node.found = false;
                            if(node.name == name_to_find) {
                                node.found = true;
                            }
                        });

                        update();
                    }, 200);
                    
                }
            });

            $('#opt_find_clear_btn').click(function(){
                setTimeout(function(){
                    $('#opt_find_name_text').val('');

                    graph.nodes.forEach(function(node){
                        node.found = false;
                    });

                    update();
                }, 200);

                

            });

            var reset_tracking = function reset_tracking(){
            
                setTimeout(function(){
                    draw_graph($.extend(true, {}, current_complete_graph));
                    tracked_nodes.splice(0, tracked_nodes.length);
                    render_tracked_nodes_sidebar();
                }, 200);
            };

            $('#opt_tracking').click(function(){
                user_options.tracking = $(this).prop('checked');

                //switching to tracking mode and drilling was on... reset 
                if(user_options.tracking && (user_options.drilling || drilling_control.in_progress)) {
                    $('#opt_drilling').attr("checked", false);
                    user_options.drilling = false;
                    drilling_control.in_progress = false;
                }
                
                reset_tracking();

            });

            $('#opt_drilling').click(function(){
                user_options.drilling = $(this).prop('checked');

                //switching to drilling mode and tracking was on... reset tracking...
                if (user_options.drilling && user_options.tracking){

                    $('#opt_tracking').attr("checked", false);
                    user_options.tracking = false;
                    reset_tracking();
                    
                }

            });

            $('#opt_drilling_reset').click(function(){
                setTimeout(function(){
                    drilling_control.in_progress = false;

                    replace_graph(graph, $.extend(true, {}, current_complete_graph));

                    current_focuse_node = null;
                    update();
                }, 200);
            });

            if(current_focuse_node && drilling_control.in_progress) {
                current_focuse_node = $.extend(true, {}, find_node(current_complete_graph.nodes, current_focuse_node.name));
                replace_graph(graph, filter_graph(current_focuse_node, current_complete_graph));
            }
            update();
        };

        //these two functions need to be a total redraw... unless we find a way to rebind mouseover/mouseout events... (doable... just need to rewrite a lot...)
        $('#opt_tooltip').click(function(){
            user_options.tooltip = $(this).prop('checked');

            if(user_options.tooltip) {
                $('#opt_connected').attr("checked", false);
                user_options.connected = false;
            }
            setTimeout(function(){
                
                draw_graph($.extend(true, {}, current_complete_graph));
            }, 200);
        });

        $('#opt_connected').click(function(){
            user_options.connected = $(this).prop('checked');
            if (user_options.connected){
                $('#opt_tooltip').attr("checked", false);
                user_options.tooltip = false;
            }
            setTimeout(function(){
                draw_graph($.extend(true, {}, current_complete_graph));
            }, 200);
        });



        d3.json('data/' + activeNetwork + ".json", function (error, graph) {
            current_complete_graph = $.extend(true, {}, graph);

            draw_graph($.extend(true, {}, current_complete_graph));
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


    var createNav = function createNavBar(activeNetwork) {

        $ul = $('<ul class="nav navbar-nav"></ul>');

        var ditems = {
            'largest-component': 'Largest Component',
            'complete': 'Complete Network'
        };

        $.each(network_opts, function (current) {

            if (current == getNetworkRoot(activeNetwork)) {
                $li = $('<li class="dropdown active"></li>');
            }else{
                $li = $('<li class="dropdown"></li>');
            }


            $a = $('<a href="#" style="display:inline-block;padding-right:0px;" tag="' + current + '">' + parseNavText(current) + '</a>').click(function () {
                var tag = $(this).attr('tag');
                $('#canvas > svg').hide('slow', function () {
                    $('#canvas > svg').remove();
                    d3_draw(tag);
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
                        d3_draw(tag);
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
            $network_info_div.append(info_row('FY', parseNavText(getNetworkRoot(activeNetwork))));
            $network_info_div.append(info_row('# of Nodes', network_info['vs']));
            $network_info_div.append(info_row('# of Edges', network_info['es']));
            $network_info_div.append(info_row('Avg # of New Edges', network_info['avg_new_edges']));
            $network_info_div.append(info_row('# of Edges', network_info['isolated_components']));

            $network_info_div.append($('<div class="row clearfix divider"><hr/></div>'));
            $network_info_div.append($('<div class="clearfix title "><b>Largest Component:</b></div>'));

            $network_info_div.append(info_row('# of Nodes', network_info['largest_component']['vs']));
            $network_info_div.append(info_row('# of Edges', network_info['largest_component']['es']));
            $network_info_div.append(info_row('C (unweighted)', network_info['largest_component']['c_g']));
            $network_info_div.append(info_row('C (weighted)', network_info['largest_component']['c_wg']));
            //$network_info_div.append(network_info_row('C (triplets definition)', network_info['largest_component']['c_tg']));
            $network_info_div.append(info_row('L (unweighted)', network_info['largest_component']['l_g']));
            $network_info_div.append(info_row('L (weighted)', network_info['largest_component']['l_wg']));

            $network_info_div.append($('<div class="row clearfix divider"><hr/></div>'));
            $network_info_div.append($('<div class="clearfix"><p><i>* C is the network <u>Clustering Coefficient</u>, and L is the network <u>Characteristic Path Length</u>.</i></p></div>'));

        });
    };

    $(document).ready(function () {

        activeNetwork = '2006-2012';

        createNav(activeNetwork);

        d3_draw(activeNetwork);

        render_tracked_nodes_sidebar();
    });

}).call(this);
