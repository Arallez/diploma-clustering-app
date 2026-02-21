/**
 * Ontology Graph Visualizer using D3.js
 * Renders nodes (Concepts) and links (ConceptRelations) resembling Protege
 */

function initOntologyGraph(containerId, nodesData, linksData) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const width = container.clientWidth;
    const height = container.clientHeight;
    
    // Semantic Colors (Matches Protege/Legend exact clustering domains)
    const colors = {
        1: '#3b82f6', // Algorithms (Blue)
        2: '#10b981', // Parameters (Green)
        3: '#f59e0b', // Metrics (Yellow)
        4: '#8b5cf6', // Use Cases (Purple)
        5: '#ec4899', // Geometry (Pink)
        6: '#14b8a6', // Scalability (Teal)
        7: '#f43f5e', // Cluster Size (Rose)
        8: '#64748b', // Inference Type (Slate)
        9: '#cbd5e1'  // Default/Thing (Light Gray)
    };

    // 1. Calculate Hierarchical Depth (for Tree/Radial Layouts)
    // Initialize depth
    nodesData.forEach(n => n.depth = 0);
    // Iterative relaxation to calculate topological depth
    for (let i = 0; i < 15; i++) {
        linksData.forEach(l => {
            // Pre-process safe lookup since D3 might change strings to objects later
            let s = typeof l.source === 'object' ? l.source : nodesData.find(n => n.id === l.source);
            let t = typeof l.target === 'object' ? l.target : nodesData.find(n => n.id === l.target);
            
            if (!s || !t) return;

            // IS_A or DEPENDS usually implies the target is the "parent/prerequisite" conceptually.
            // Target should be higher (lower depth value) than source.
            if (l.type === 'Является (Is A)' || l.type === 'Зависит от (Пререквизит)') {
                if (s.depth <= t.depth) {
                    s.depth = t.depth + 1;
                }
            } else {
                // USES, RELATED: standard flow
                if (t.depth <= s.depth) {
                    t.depth = s.depth + 1;
                }
            }
        });
    }
    // Normalize depths to start at 0
    let minDepth = d3.min(nodesData, d => d.depth) || 0;
    nodesData.forEach(n => n.depth -= minDepth);
    let maxDepth = d3.max(nodesData, d => d.depth) || 1;

    // 2. Setup D3 Canvas
    const svg = d3.select("#" + containerId)
        .append("svg")
        .attr("width", width)
        .attr("height", height);

    const g = svg.append("g");

    // Setup Zoom
    const zoom = d3.zoom()
        .scaleExtent([0.1, 4])
        .on("zoom", (event) => {
            g.attr("transform", event.transform);
        });
    
    svg.call(zoom);
    
    // UI Zoom Controls
    d3.select("#btn-zoom-in").on("click", () => zoom.scaleBy(svg.transition().duration(300), 1.3));
    d3.select("#btn-zoom-out").on("click", () => zoom.scaleBy(svg.transition().duration(300), 1 / 1.3));
    d3.select("#btn-reset").on("click", () => {
        svg.transition().duration(500).call(zoom.transform, d3.zoomIdentity.translate(width/2, height/2).scale(0.8));
    });

    // Arrow markers for links
    svg.append("defs").selectAll("marker")
        .data(["end", "end-highlight"])
        .enter().append("marker")
        .attr("id", String)
        .attr("viewBox", "0 -5 10 10")
        .attr("refX", 25) // Offset from node center
        .attr("refY", 0)
        .attr("markerWidth", 6)
        .attr("markerHeight", 6)
        .attr("orient", "auto")
        .append("path")
        .attr("fill", d => d === "end-highlight" ? "#3b82f6" : "#94a3b8")
        .attr("d", "M0,-5L10,0L0,5");

    // 3. Initialize Base Simulation
    const simulation = d3.forceSimulation(nodesData)
        .force("link", d3.forceLink(linksData).id(d => d.id).distance(180));

    // Lines
    const link = g.append("g")
        .attr("class", "links")
        .selectAll("line")
        .data(linksData)
        .enter().append("line")
        .attr("class", "link")
        .attr("marker-end", "url(#end)");

    // Text on lines (Relations)
    const linkText = g.append("g")
        .attr("class", "link-labels")
        .selectAll("text")
        .data(linksData)
        .enter().append("text")
        .attr("class", "link-label")
        .text(d => d.type);

    // Nodes container
    const node = g.append("g")
        .attr("class", "nodes")
        .selectAll("g")
        .data(nodesData)
        .enter().append("g")
        .attr("class", "node")
        .call(d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended));

    // Node Circles
    node.append("circle")
        .attr("r", 12)
        .attr("fill", d => colors[d.group] || colors[9]);

    // Node Text (Titles)
    node.append("text")
        .attr("dx", 18)
        .attr("dy", ".35em")
        .text(d => d.title);

    // Tooltip Interactions
    const tooltip = d3.select("#graph-tooltip");

    node.on("mouseover", function(event, d) {
        // Highlight Node
        d3.select(this).select("circle")
            .attr("r", 16)
            .attr("stroke", "#0f172a");
        
        // Highlight Connected Links
        link.style("stroke-opacity", l => (l.source.id === d.id || l.target.id === d.id) ? 1 : 0.1)
            .style("stroke", l => (l.source.id === d.id || l.target.id === d.id) ? "#3b82f6" : "#94a3b8")
            .attr("marker-end", l => (l.source.id === d.id || l.target.id === d.id) ? "url(#end-highlight)" : "url(#end)");
        
        // Highlight Connected Link Text
        linkText.style("opacity", l => (l.source.id === d.id || l.target.id === d.id) ? 1 : 0)
                .style("fill", l => (l.source.id === d.id || l.target.id === d.id) ? "#3b82f6" : "#64748b")
                .style("font-weight", l => (l.source.id === d.id || l.target.id === d.id) ? "bold" : "normal");

        // Dim Unconnected Nodes
        node.style("opacity", n => {
            if (n.id === d.id) return 1;
            const isConnected = linksData.some(l => 
                (l.source.id === d.id && l.target.id === n.id) || 
                (l.target.id === d.id && l.source.id === n.id)
            );
            return isConnected ? 1 : 0.15;
        });

        // Show Tooltip
        tooltip.transition().duration(200).style("opacity", 1);
        tooltip.html(
            `<div class="tooltip-title" style="color:${colors[d.group]}">${d.title}</div>` +
            `<div class="tooltip-uri">URI: ${d.uri.split('#').pop()}</div>` +
            `<div class="tooltip-desc">${d.desc}</div>`
        )
        .style("left", (event.pageX + 15) + "px")
        .style("top", (event.pageY - 15) + "px");
    })
    .on("mouseout", function(d) {
        // Reset Style
        d3.select(this).select("circle").attr("r", 12).attr("stroke", "#ffffff");
        link.style("stroke-opacity", 0.5).style("stroke", "#94a3b8").attr("marker-end", "url(#end)");
        linkText.style("opacity", 1).style("fill", "#64748b").style("font-weight", "normal");
        node.style("opacity", 1);
        tooltip.transition().duration(300).style("opacity", 0);
    })
    .on("click", function(event, d) {
        window.location.href = d.url;
    });

    // Tick Update
    simulation.on("tick", () => {
        link
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);

        linkText
            .attr("x", d => (d.source.x + d.target.x) / 2)
            .attr("y", d => (d.source.y + d.target.y) / 2 - 5)
            .attr("transform", d => {
                const angle = Math.atan2(d.target.y - d.source.y, d.target.x - d.source.x) * 180 / Math.PI;
                const finalAngle = (angle > 90 || angle < -90) ? angle + 180 : angle;
                const cx = (d.source.x + d.target.x) / 2;
                const cy = (d.source.y + d.target.y) / 2 - 5;
                return `rotate(${finalAngle}, ${cx}, ${cy})`;
            });

        node.attr("transform", d => `translate(${d.x},${d.y})`);
    });

    // 4. Layout Switching Logic
    window.applyGraphLayout = function(type) {
        // Clear all forces
        simulation.force("x", null);
        simulation.force("y", null);
        simulation.force("r", null);
        simulation.force("center", null);

        if (type === 'force') {
            simulation
                .force("charge", d3.forceManyBody().strength(-1000))
                .force("center", d3.forceCenter(0, 0))
                .force("collide", d3.forceCollide().radius(50));
        } else if (type === 'tree') {
            // Tree layout using depth
            const layerHeight = 150;
            const yOffset = (maxDepth * layerHeight) / 2;
            
            simulation
                .force("charge", d3.forceManyBody().strength(-800))
                .force("y", d3.forceY(d => (d.depth * layerHeight) - yOffset).strength(1.5))
                .force("x", d3.forceX(0).strength(0.2)) // Center horizontally
                .force("collide", d3.forceCollide().radius(60));
        } else if (type === 'radial') {
            // Radial layout using depth as radius
            const radiusStep = 120;
            simulation
                .force("charge", d3.forceManyBody().strength(-800))
                .force("r", d3.forceRadial(d => d.depth * radiusStep, 0, 0).strength(1.5))
                .force("collide", d3.forceCollide().radius(50));
        }
        
        // Re-heat simulation
        simulation.alpha(1).restart();
        // Recenter view
        svg.transition().duration(750).call(zoom.transform, d3.zoomIdentity.translate(width/2, height/2).scale(0.7));
    };

    // Initial Layout Setup
    window.applyGraphLayout('force');

    // Attach Toolbar Listeners
    document.querySelectorAll('.toolbar-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.toolbar-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            window.applyGraphLayout(this.getAttribute('data-layout'));
        });
    });

    // Drag Functions
    function dragstarted(event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }
    function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }
    function dragended(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }
}
