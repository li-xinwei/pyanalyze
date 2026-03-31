import React, { useMemo } from 'react';

export default function FunctionList({ graph, selectedNode, onSelectNode }) {
  const sortedNodes = useMemo(() => {
    if (!graph?.nodes) return [];
    return [...graph.nodes].sort((a, b) => (b.complexity || 1) - (a.complexity || 1));
  }, [graph]);

  if (!graph) return null;

  return (
    <div className="p-4">
      <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
        Functions ({sortedNodes.length})
      </h3>
      <div className="space-y-0.5 max-h-40 overflow-y-auto">
        {sortedNodes.map(node => (
          <button
            key={node.id}
            onClick={() => onSelectNode(node)}
            className={`w-full text-left px-2 py-1.5 rounded text-xs transition-colors ${
              selectedNode?.id === node.id
                ? 'bg-sky-900/50 text-sky-300'
                : 'text-slate-300 hover:bg-slate-700/50'
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="font-mono truncate">{node.name}</span>
              <span className="text-slate-500 flex-shrink-0 ml-2">
                CC:{node.complexity}
              </span>
            </div>
            <div className="text-slate-500 text-[10px] truncate">
              {node.file}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
