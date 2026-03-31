import React from 'react';

export default function ExportButton({ graph }) {
  const handleExport = () => {
    if (!graph) return;
    const blob = new Blob([JSON.stringify(graph, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'callgraph.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!graph) return null;

  return (
    <button
      onClick={handleExport}
      className="text-xs text-slate-400 hover:text-white px-2 py-1 border border-slate-600 rounded hover:border-slate-400 transition-colors"
    >
      Export JSON
    </button>
  );
}
