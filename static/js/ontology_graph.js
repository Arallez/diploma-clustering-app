/**
 * Ontology Graph Visualizer using D3.js
 * Renders nodes (Concepts) and links (ConceptRelations) resembling Protege
 */

function initOntologyGraph(containerId, nodesData, linksData) {
    const container = document.getElementById(containerId);
    if (!container) return;

    // We get dimensions from the container
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

    // Edge Styles Configuration based on raw relation_type
    const edgeStyles = {
        'IS_A': { color: '#94a3b8', dash: null },               // Solid Grey
        'DEPENDS': { color: '#ef4444', dash: '6, 6' },          // Dashed Red
        'USES': { color: '#3b82f6', dash: '2, 4' },             // Dotted Blue
        'RELATED': { color: '#8b5cf6', dash: null },            // Solid Purple
        'PART_OF': { color: '#10b981', dash: '10, 5' },         // Long-dash Green
        'default': { color: '#94a3b8', dash: null }
    };

    // 1. Calculate Hierarchical Depth (for Tree/Radial Layouts)
    nodesData.forEach(n => n.depth = 0);
    for (let i = 0; i < 15; i++) {
        linksData.forEach(l => {
            let s = typeof l.source === 'object' ? l.source : nodesData.find(n => n.id === l.source);
            let t = typeof l.target === 'object' ? l.target : nodesData.find(n => n.id === l.target);
            if (!s || !t) return;

            if (l.raw_type === 'IS_A' || l.raw_type === 'DEPENDS') {
                if (s.depth <= t.depth) {
                    s.depth = t.depth + 1;
                }
            } else {
                if (t.depth <= s.depth) {
                    t.depth = s.depth + 1;
                }
            }
        });
    }
    
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

    // Generate arrow markers dynamically for each relation type color
    const defs = svg.append("defs");
    
    Object.keys(edgeStyles).forEach(type => {
        const style = edgeStyles[type];
        // Normal state marker
        defs.append("marker")
            .attr("id", `arrow-${type}`)
            .attr("viewBox", "0 -5 10 10")
            // Adjusted refX because we are pointing to rectangles, not small circles
            .attr("refX", 10) 
            .attr("refY", 0)
            .attr("markerWidth", 8)
            .attr("markerHeight", 8)
            .attr("orient", "auto")
            .append("path")
            .attr("fill", style.color)
            .attr("d", "M0,-5L10,0L0,5");
            
        // Highlight state marker
        defs.append("marker")
            .attr("id", `arrow-${type}-hl`)
            .attr("viewBox", "0 -5 10 10")
            .attr("refX", 10)
            .attr("refY", 0)
            .attr("markerWidth", 10) // slightly larger when highlighted
            .attr("markerHeight", 10)
            .attr("orient", "auto")
            .append("path")
            .attr("fill", "#0f172a") // dark stroke when highlighted
            .attr("d", "M0,-5L10,0L0,5");
    });

    // Calculate bounding box approximations based on text length
    nodesData.forEach(d => {
        d.rectWidth = Math.max(80, d.title.length * 7 + 20); // 7px per char approx + 20px padding
        d.rectHeight = 26;
    });

    // 3. Initialize Base Simulation
    const simulation = d3.forceSimulation(nodesData)
        .force("link", d3.forceLink(linksData).id(d => d.id).distance(220));

    // Lines (Edges)
    const link = g.append("g")
        .attr("class", "links")
        .selectAll("path")
        .data(linksData)
        .enter().append("path")
        .attr("class", "link")
        .attr("fill", "none")
        .attr("stroke", d => (edgeStyles[d.raw_type] || edgeStyles['default']).color)
        .attr("stroke-dasharray", d => (edgeStyles[d.raw_type] || edgeStyles['default']).dash)
        .attr("marker-end", d => `url(#arrow-${d.raw_type || 'default'})`);

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

    // Node Rectangles (Protege Style)
    node.append("rect")
        .attr("width", d => d.rectWidth)
        .attr("height", d => d.rectHeight)
        // Center the rectangle around the coordinates
        .attr("x", d => -d.rectWidth / 2)
        .attr("y", d => -d.rectHeight / 2)
        .attr("fill", d => colors[d.group] || colors[9]);

    // Node Text (Centered)
    node.append("text")
        .attr("dy", "0.35em") // Vertical center offset
        .text(d => d.title);

    // Overlay Info Panel Element
    const infoPanel = d3.select("#graph-info-panel");

    node.on("mouseover", function(event, d) {
        // Highlight Node Box
        d3.select(this).select("rect")
            .attr("stroke", "#0f172a")
            .attr("stroke-width", "3px");
        
        // Highlight Connected Links
        link.style("stroke-opacity", l => (l.source.id === d.id || l.target.id === d.id) ? 1 : 0.1)
            // Thicker and darker line when highlighted
            .style("stroke-width", l => (l.source.id === d.id || l.target.id === d.id) ? "3px" : "2px")
            .style("stroke", l => (l.source.id === d.id || l.target.id === d.id) ? "#0f172a" : (edgeStyles[l.raw_type] || edgeStyles['default']).color)
            .attr("marker-end", l => (l.source.id === d.id || l.target.id === d.id) ? `url(#arrow-${l.raw_type || 'default'}-hl)` : `url(#arrow-${l.raw_type || 'default'})`);
        
        // Dim Unconnected Nodes
        node.style("opacity", n => {
            if (n.id === d.id) return 1;
            const isConnected = linksData.some(l => 
                (l.source.id === d.id && l.target.id === n.id) || 
                (l.target.id === d.id && l.source.id === n.id)
            );
            return isConnected ? 1 : 0.15;
        });

        // Gather connections for the side panel
        let outgoing = linksData.filter(l => l.source.id === d.id).map(l => `
            <li>
                <span class="panel-conn-type" style="color:${(edgeStyles[l.raw_type]||edgeStyles['default']).color}">▶ ${l.type}</span>
                <span class="panel-conn-node">${(l.target.title || l.target.id)}</span>
            </li>
        `).join("");
        
        let incoming = linksData.filter(l => l.target.id === d.id).map(l => `
            <li>
                <span class="panel-conn-type" style="color:${(edgeStyles[l.raw_type]||edgeStyles['default']).color}">◀ ${l.type}</span>
                <span class="panel-conn-node">${(l.source.title || l.source.id)}</span>
            </li>
        `).join("");
        
        // Update Overlay Panel Content
        infoPanel.html(`
            <div class="panel-title" style="color:${colors[d.group]}">${d.title}</div>
            <div class="panel-uri">URI: ${d.uri.split('#').pop()}</div>
            <div class="panel-desc">${d.desc}</div>
            
            ${(outgoing || incoming) ? `<div class="panel-section-title">Связи графа</div>` : ''}
            <ul class="panel-connections">
                ${outgoing}
                ${incoming}
            </ul>

            <div style="margin-top: 25px; padding-top: 15px; border-top: 1px dashed #e2e8f0; text-align: center; color: #64748b; font-size: 11px;">
                🖱️ Кликните по узлу, чтобы перейти к теории
            </div>
        `);
        
        // Make the overlay visible
        infoPanel.classed("visible", true);
    })
    .on("mouseout", function(d) {
        // Reset Style
        d3.select(this).select("rect")
            .attr("stroke", "#ffffff")
            .attr("stroke-width", "2px");
            
        link.style("stroke-opacity", 0.6)
            .style("stroke-width", "2px")
            .style("stroke", l => (edgeStyles[l.raw_type] || edgeStyles['default']).color)
            .attr("marker-end", l => `url(#arrow-${l.raw_type || 'default'})`);
            
        node.style("opacity", 1);
        
        // Hide the overlay
        infoPanel.classed("visible", false);
    })
    .on("click", function(event, d) {
        window.location.href = d.url;
    });

    // Helper to calculate edge intersection with rectangle boundary
    function getIntersection(sx, sy, tx, ty, tWidth, tHeight) {
        const dx = tx - sx;
        const dy = ty - sy;
        
        if (dx === 0 && dy === 0) return {x: tx, y: ty};

        const hw = tWidth / 2;
        const hh = tHeight / 2;
        
        let ix, iy;
        
        if (Math.abs(dx) > 0) {
            ix = dx > 0 ? tx - hw : tx + hw;
            iy = ty - dy * (Math.abs(hw) / Math.abs(dx));
            
            if (iy < ty - hh) {
                iy = ty - hh;
                ix = tx - dx * (Math.abs(hh) / Math.abs(dy));
            } else if (iy > ty + hh) {
                iy = ty + hh;
                ix = tx - dx * (Math.abs(hh) / Math.abs(dy));
            }
        } else {
            ix = tx;
            iy = dy > 0 ? ty - hh : ty + hh;
        }

        return {x: ix, y: iy};
    }

    // Tick Update
    simulation.on("tick", () => {
        link.attr("d", d => {
            if (!d.source.x || !d.target.x) return "";
            const p = getIntersection(d.source.x, d.source.y, d.target.x, d.target.y, d.target.rectWidth, d.target.rectHeight);
            return `M${d.source.x},${d.source.y} L${p.x},${p.y}`;
        });

        node.attr("transform", d => `translate(${d.x},${d.y})`);
    });

    // 4. Layout Switching Logic
    window.applyGraphLayout = function(type) {
        simulation.force("x", null);
        simulation.force("y", null);
        simulation.force("r", null);
        simulation.force("center", null);

        if (type === 'force') {
            simulation
                .force("charge", d3.forceManyBody().strength(-1500))
                .force("center", d3.forceCenter(0, 0))
                .force("collide", d3.forceCollide().radius(d => d.rectWidth / 2 + 25).iterations(4));
        } else if (type === 'tree') {
            // Tree layout using depth.
            const layerHeight = 180; 
            const yOffset = (maxDepth * layerHeight) / 2;
            
            simulation
                .force("charge", d3.forceManyBody().strength(-1500))
                .force("y", d3.forceY(d => (d.depth * layerHeight) - yOffset).strength(1.2))
                .force("x", d3.forceX(0).strength(0.1)) // Gentle pull to center horizontally
                .force("collide", d3.forceCollide().radius(d => d.rectWidth / 2 + 20).iterations(4));
        } else if (type === 'radial') {
            // Radial layout - fixed jumping
            const radiusStep = 220; // Give them wider rings
            simulation
                // Lower charge to prevent explosion jumping
                .force("charge", d3.forceManyBody().strength(-800))
                // Soften radial pull so large nodes have room to breathe
                .force("r", d3.forceRadial(d => d.depth * radiusStep, 0, 0).strength(0.8))
                // Increase iterations for more accurate, less jumpy collision
                .force("collide", d3.forceCollide().radius(d => d.rectWidth / 2 + 20).iterations(6));
        }
        
        simulation.alpha(1).restart();
        // Recenter view with a smaller scale to see the wider graph
        svg.transition().duration(750).call(zoom.transform, d3.zoomIdentity.translate(width/2, height/2).scale(0.6));
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
