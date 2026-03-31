import React, { useEffect, useState } from 'react';
import { useAnalysis } from './hooks/useAnalysis';
import CodeInput from './components/CodeInput';
import CallGraph from './components/CallGraph';
import SliceView from './components/SliceView';
import MetricsPanel from './components/MetricsPanel';
import FunctionList from './components/FunctionList';
import ExportButton from './components/ExportButton';

export default function App() {
  const { graph, slice, loading, error, analyze, computeSlice, loadDemo, clearSlice } = useAnalysis();
  const [selectedNode, setSelectedNode] = useState(null);

  useEffect(() => {
    loadDemo();
  }, [loadDemo]);

  const handleNodeClick = (node) => {
    setSelectedNode(node);
    computeSlice(node.id);
  };

  const handleBackgroundClick = () => {
    setSelectedNode(null);
    clearSlice();
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-900">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-3 bg-slate-800 border-b border-slate-700">
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-bold text-white tracking-tight">
            <span className="text-sky-400">Py</span>Analyze
          </h1>
          <span className="text-xs text-slate-400 hidden sm:inline">Python Static Analysis Tool</span>
        </div>
        <div className="flex items-center gap-3">
          <ExportButton graph={graph} />
          <a href="https://github.com" target="_blank" rel="noreferrer"
             className="text-slate-400 hover:text-white text-sm">
            GitHub
          </a>
        </div>
      </header>

      {/* Loading bar */}
      {loading && (
        <div className="h-0.5 bg-sky-500 animate-pulse" />
      )}

      {/* Error */}
      {error && (
        <div className="mx-6 mt-3 p-3 bg-red-900/40 border border-red-700 rounded-lg text-red-300 text-sm">
          {error}
        </div>
      )}

      {/* Main content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left sidebar */}
        <aside className="w-80 flex-shrink-0 flex flex-col border-r border-slate-700 bg-slate-800/50 overflow-y-auto">
          <CodeInput onAnalyze={analyze} onLoadDemo={loadDemo} loading={loading} />
          <div className="border-t border-slate-700" />
          <FunctionList
            graph={graph}
            selectedNode={selectedNode}
            onSelectNode={handleNodeClick}
          />
          <div className="border-t border-slate-700" />
          <MetricsPanel graph={graph} selectedNode={selectedNode} slice={slice} />
        </aside>

        {/* Main area */}
        <main className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 relative">
            <CallGraph
              graph={graph}
              slice={slice}
              onNodeClick={handleNodeClick}
              onBackgroundClick={handleBackgroundClick}
              selectedNode={selectedNode}
            />
          </div>

          {slice && (
            <div className="h-72 border-t border-slate-700 overflow-y-auto bg-slate-800/60">
              <SliceView slice={slice} onClose={handleBackgroundClick} />
            </div>
          )}
        </main>
      </div>

      {/* Footer */}
      <footer className="px-6 py-2 bg-slate-800 border-t border-slate-700 text-center text-xs text-slate-500">
        Built by Xinwei Li | Berkeley CS '27
      </footer>
    </div>
  );
}
