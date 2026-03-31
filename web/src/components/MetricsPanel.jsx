import React from 'react';

function Stat({ label, value }) {
  return (
    <div className="flex justify-between items-center py-1">
      <span className="text-xs text-slate-400">{label}</span>
      <span className="text-sm font-medium text-slate-200">{value}</span>
    </div>
  );
}

export default function MetricsPanel({ graph, selectedNode, slice }) {
  if (!graph) return null;

  const m = graph.metrics || {};

  return (
    <div className="p-4 space-y-4">
      <div>
        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
          Repository
        </h3>
        <Stat label="Files" value={m.total_files ?? graph.files?.length ?? 0} />
        <Stat label="Functions" value={m.total_functions ?? graph.nodes?.length ?? 0} />
        <Stat label="Edges" value={m.total_edges ?? graph.edges?.length ?? 0} />
        <Stat label="Avg Complexity" value={m.avg_complexity ?? '-'} />
        <Stat label="Avg Slice Reduction"
          value={m.avg_slice_reduction != null
            ? `${(m.avg_slice_reduction * 100).toFixed(1)}%`
            : '-'
          }
        />
        {m.max_fan_in != null && <Stat label="Max Fan-in" value={m.max_fan_in} />}
        {m.max_fan_out != null && <Stat label="Max Fan-out" value={m.max_fan_out} />}
      </div>

      {selectedNode && (
        <div className="border-t border-slate-700 pt-3">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Selected Function
          </h3>
          <div className="text-sm font-mono text-sky-400 mb-2 break-all">
            {selectedNode.id}
          </div>
          <Stat label="File" value={selectedNode.file} />
          <Stat label="Line" value={selectedNode.lineno} />
          <Stat label="Lines of Code" value={selectedNode.lines} />
          <Stat label="Complexity" value={selectedNode.complexity} />
          <Stat label="Fan-in" value={selectedNode.fan_in} />
          <Stat label="Fan-out" value={selectedNode.fan_out} />
          {slice && (
            <Stat label="Slice Reduction"
              value={`${(slice.reduction_ratio * 100).toFixed(1)}%`}
            />
          )}
        </div>
      )}
    </div>
  );
}
