import * as d3 from 'd3';

export function createSimulation(nodes, edges, width, height) {
  return d3.forceSimulation(nodes)
    .force('link', d3.forceLink(edges).id(d => d.id).distance(100))
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(d => (d.radius || 12) + 8));
}

export function getNodeRadius(complexity) {
  return Math.min(30, 8 + (complexity || 1) * 3);
}

export function getFileColorScale(files) {
  return d3.scaleOrdinal(d3.schemeCategory10).domain(files);
}
