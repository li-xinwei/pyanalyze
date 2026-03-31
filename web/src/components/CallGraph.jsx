import React, { useEffect, useRef, useMemo } from 'react';
import * as d3 from 'd3';
import { getNodeRadius, getFileColorScale } from '../utils/graphLayout';

export default function CallGraph({ graph, slice, onNodeClick, onBackgroundClick, selectedNode }) {
  const svgRef = useRef(null);
  const containerRef = useRef(null);
  const simulationRef = useRef(null);
  const tooltipRef = useRef(null);

  const sliceIds = useMemo(() => {
    if (!slice) return null;
    return new Set(slice.dependencies || []);
  }, [slice]);

  useEffect(() => {
    if (!graph || !graph.nodes || graph.nodes.length === 0) return;

    const container = containerRef.current;
    const width = container.clientWidth;
    const height = container.clientHeight;

    d3.select(svgRef.current).selectAll('*').remove();

    const svg = d3.select(svgRef.current)
      .attr('width', width)
      .attr('height', height);

    // Arrow marker
    svg.append('defs').append('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 20)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#475569');

    const g = svg.append('g');

    // Zoom
    const zoom = d3.zoom()
      .scaleExtent([0.2, 5])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });

    svg.call(zoom);

    svg.on('dblclick.zoom', null);
    svg.on('dblclick', () => {
      svg.transition().duration(500).call(zoom.transform, d3.zoomIdentity);
      onBackgroundClick();
    });

    svg.on('click', (event) => {
      if (event.target === svgRef.current) {
        onBackgroundClick();
      }
    });

    const colorScale = getFileColorScale(graph.files || []);

    const nodes = graph.nodes.map(n => ({
      ...n,
      radius: getNodeRadius(n.complexity),
    }));

    const nodeIds = new Set(nodes.map(n => n.id));
    const edges = (graph.edges || [])
      .filter(e => nodeIds.has(e.source) && nodeIds.has(e.target))
      .map(e => ({ ...e }));

    // Links
    const link = g.append('g')
      .selectAll('line')
      .data(edges)
      .join('line')
      .attr('stroke', '#334155')
      .attr('stroke-width', 1.5)
      .attr('marker-end', 'url(#arrowhead)');

    // Nodes
    const node = g.append('g')
      .selectAll('g')
      .data(nodes)
      .join('g')
      .attr('cursor', 'pointer')
      .call(d3.drag()
        .on('start', (event, d) => {
          if (!event.active) simulationRef.current.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on('drag', (event, d) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on('end', (event, d) => {
          if (!event.active) simulationRef.current.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        })
      );

    node.append('circle')
      .attr('r', d => d.radius)
      .attr('fill', d => colorScale(d.file))
      .attr('stroke', '#0f172a')
      .attr('stroke-width', 2)
      .attr('opacity', 0.9);

    node.append('text')
      .text(d => d.name)
      .attr('text-anchor', 'middle')
      .attr('dy', d => d.radius + 14)
      .attr('fill', '#94a3b8')
      .attr('font-size', '11px')
      .attr('font-weight', '500')
      .attr('pointer-events', 'none');

    // Tooltip
    let tooltip = d3.select('.graph-tooltip');
    if (tooltip.empty()) {
      tooltip = d3.select('body').append('div').attr('class', 'graph-tooltip').style('display', 'none');
    }
    tooltipRef.current = tooltip;

    node.on('mouseover', (event, d) => {
      tooltip
        .style('display', 'block')
        .html(`
          <div class="tt-name">${d.id}</div>
          <div class="tt-row"><span>File</span><span>${d.file}</span></div>
          <div class="tt-row"><span>Lines</span><span>${d.lines}</span></div>
          <div class="tt-row"><span>Complexity</span><span>${d.complexity}</span></div>
          <div class="tt-row"><span>Fan-in</span><span>${d.fan_in}</span></div>
          <div class="tt-row"><span>Fan-out</span><span>${d.fan_out}</span></div>
        `)
        .style('left', (event.pageX + 15) + 'px')
        .style('top', (event.pageY - 10) + 'px');
    })
    .on('mousemove', (event) => {
      tooltip
        .style('left', (event.pageX + 15) + 'px')
        .style('top', (event.pageY - 10) + 'px');
    })
    .on('mouseout', () => {
      tooltip.style('display', 'none');
    })
    .on('click', (event, d) => {
      event.stopPropagation();
      onNodeClick(d);
    });

    // Simulation
    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(edges).id(d => d.id).distance(100))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(d => d.radius + 8))
      .on('tick', () => {
        link
          .attr('x1', d => d.source.x)
          .attr('y1', d => d.source.y)
          .attr('x2', d => d.target.x)
          .attr('y2', d => d.target.y);

        node.attr('transform', d => `translate(${d.x},${d.y})`);
      });

    simulationRef.current = simulation;

    return () => {
      simulation.stop();
      if (tooltipRef.current) tooltipRef.current.style('display', 'none');
    };
  }, [graph]);

  useEffect(() => {
    if (!graph) return;
    const svg = d3.select(svgRef.current);

    if (sliceIds) {
      svg.selectAll('g g g').each(function(d) {
        const el = d3.select(this);
        const inSlice = sliceIds.has(d.id);
        el.select('circle')
          .transition().duration(500)
          .attr('opacity', inSlice ? 1 : 0.15);
        el.select('text')
          .transition().duration(500)
          .attr('opacity', inSlice ? 1 : 0.15);
      });

      svg.selectAll('line')
        .transition().duration(500)
        .attr('opacity', d => {
          const srcId = typeof d.source === 'object' ? d.source.id : d.source;
          const tgtId = typeof d.target === 'object' ? d.target.id : d.target;
          return sliceIds.has(srcId) && sliceIds.has(tgtId) ? 0.8 : 0.08;
        });
    } else {
      svg.selectAll('circle').transition().duration(500).attr('opacity', 0.9);
      svg.selectAll('g g g text').transition().duration(500).attr('opacity', 1);
      svg.selectAll('line').transition().duration(500).attr('opacity', 1);
    }
  }, [sliceIds, graph]);

  useEffect(() => {
    if (!graph || !selectedNode) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll('g g g circle')
      .attr('stroke', d => d.id === selectedNode.id ? '#38bdf8' : '#0f172a')
      .attr('stroke-width', d => d.id === selectedNode.id ? 3 : 2);
  }, [selectedNode, graph]);

  if (!graph) {
    return (
      <div ref={containerRef} className="w-full h-full flex items-center justify-center text-slate-500">
        <div className="text-center">
          <div className="text-4xl mb-4 opacity-30">&#x1F50E;</div>
          <p className="text-lg">Loading analysis...</p>
        </div>
      </div>
    );
  }

  return (
    <div ref={containerRef} className="w-full h-full">
      <svg ref={svgRef} className="w-full h-full" />
    </div>
  );
}
