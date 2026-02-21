/**
 * Ontology Graph Visualizer using D3.js
 * Renders nodes (Concepts) and links (ConceptRelations) resembling Protege
 */

function initOntologyGraph(containerId, nodesData, linksData, urls) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const width = container.clientWidth;
    const height = container.clientHeight;
    
    // Semantic Colors (Matches Protege/Legend)
    const colors = {
        1: '#3b82f6', // Algorithms (Blue)
        2: '#10b981', // Parameters (Green)
        3: '#f59e0b', // Metrics (Yellow)
        4: '#8b5cf6', // Use Cases (Purple)
        5: '#64748b'  // Others (Grey)
    };

    const svg = d3.select("#" + containerId)
        .append("svg")
        .attr("width", width)
        .attr("height", height);

    const g = svg.append("g");

    // Setup Zoom
    const zoom = d3.zoom()
        .scaleExtent([0.2, 4])
        .on("zoom", (event) => {
            g.attr("transform", event.transform);
        });
    
    svg.call(zoom);
    
    // UI Controls
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

    // Physics Simulation
    const simulation = d3.forceSimulation(nodesData)
        .force("link", d3.forceLink(linksData).id(d => d.id).distance(180)) // Longer links for readability
        .force("charge", d3.forceManyBody().strength(-1000)) // Strong repel to spread graph
        .force("collide", d3.forceCollide().radius(50)) // Prevent overlaps
        .force("center", d3.forceCenter(0, 0));

    // Center graph initially
    svg.call(zoom.transform, d3.zoomIdentity.translate(width/2, height/2).scale(0.8));

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
        .attr("fill", d => colors[d.group] || colors[5]);

    // Node Text (Titles)
    node.append("text")
        .attr("dx", 18)
        .attr("dy", ".35em")
        .text(d => d.title);

    // Tooltip
    const tooltip = d3.select("#graph-tooltip");

    // Smart Hover Interactions
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
        // Reset Node
        d3.select(this).select("circle")
            .attr("r", 12)
            .attr("stroke", "#ffffff");
        
        // Reset Links
        link.style("stroke-opacity", 0.5)
            .style("stroke", "#94a3b8")
            .attr("marker-end", "url(#end)");
            
        // Reset Link Text
        linkText.style("opacity", 1)
                .style("fill", "#64748b")
                .style("font-weight", "normal");
                
        // Reset All Nodes
        node.style("opacity", 1);

        // Hide Tooltip
        tooltip.transition().duration(300).style("opacity", 0);
    })
    .on("click", function(event, d) {
        // Navigate to Concept Detail page
        window.location.href = d.url;
    });

    // Update positions on every tick
    simulation.on("tick", () => {
        link
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);

        // Position text in the middle of the link
        linkText
            .attr("x", d => (d.source.x + d.target.x) / 2)
            .attr("y", d => (d.source.y + d.target.y) / 2 - 5) // Slightly above line
            // Rotate text to follow the line
            .attr("transform", d => {
                const angle = Math.atan2(d.target.y - d.source.y, d.target.x - d.source.x) * 180 / Math.PI;
                // Keep text readable (don't turn upside down)
                const finalAngle = (angle > 90 || angle < -90) ? angle + 180 : angle;
                const cx = (d.source.x + d.target.x) / 2;
                const cy = (d.source.y + d.target.y) / 2 - 5;
                return `rotate(${finalAngle}, ${cx}, ${cy})`;
            });

        node
            .attr("transform", d => `translate(${d.x},${d.y})`);
    });

    // Drag functions
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
