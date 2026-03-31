import React, { useEffect, useRef } from 'react';
import hljs from 'highlight.js/lib/core';
import python from 'highlight.js/lib/languages/python';
import 'highlight.js/styles/github-dark.css';

hljs.registerLanguage('python', python);

export default function SliceView({ slice, onClose }) {
  const codeRef = useRef(null);

  useEffect(() => {
    if (codeRef.current && slice?.code) {
      codeRef.current.textContent = slice.code;
      hljs.highlightElement(codeRef.current);
    }
  }, [slice]);

  if (!slice) return null;

  const deps = slice.dependencies || [];
  const reduction = slice.reduction_ratio != null
    ? (slice.reduction_ratio * 100).toFixed(1)
    : '0';

  return (
    <div className="p-4 h-full flex flex-col">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-4">
          <h3 className="text-sm font-semibold text-white">
            Backward Slice: <span className="text-sky-400">{slice.target}</span>
          </h3>
          <span className="text-xs px-2 py-0.5 bg-emerald-900/60 text-emerald-300 rounded-full">
            {slice.total_lines} of {slice.original_lines} lines ({reduction}% reduction)
          </span>
        </div>
        <button onClick={onClose} className="text-slate-500 hover:text-white text-sm">
          ✕
        </button>
      </div>

      <div className="flex gap-4 flex-1 overflow-hidden">
        {/* Dependency tree */}
        <div className="w-56 flex-shrink-0 overflow-y-auto">
          <h4 className="text-xs font-medium text-slate-400 mb-2 uppercase tracking-wider">
            Dependencies ({deps.length})
          </h4>
          <div className="space-y-0.5">
            {deps.map((dep, i) => (
              <div key={dep}
                className={`text-xs font-mono py-1 px-2 rounded ${
                  dep === slice.target
                    ? 'bg-sky-900/40 text-sky-300'
                    : 'text-slate-400 hover:bg-slate-700/50'
                }`}
                style={{ paddingLeft: `${Math.min(i, 6) * 8 + 8}px` }}
              >
                {dep === slice.target ? '→ ' : '  '}{dep.split('.').pop()}
                <span className="text-slate-600 ml-1">
                  {dep.includes('.') ? dep.substring(0, dep.lastIndexOf('.')) : ''}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Code */}
        <div className="flex-1 overflow-y-auto bg-slate-900 rounded-lg border border-slate-700">
          <pre className="p-3 text-xs leading-relaxed">
            <code ref={codeRef} className="language-python">
              {slice.code || '# No code available'}
            </code>
          </pre>
        </div>
      </div>
    </div>
  );
}
