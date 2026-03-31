import React, { useState, useRef } from 'react';

export default function CodeInput({ onAnalyze, onLoadDemo, loading }) {
  const [entries, setEntries] = useState([{ name: 'main.py', content: '' }]);
  const [mode, setMode] = useState('paste');
  const fileInputRef = useRef(null);

  const addEntry = () => {
    setEntries(prev => [...prev, { name: `file_${prev.length + 1}.py`, content: '' }]);
  };

  const removeEntry = (idx) => {
    setEntries(prev => prev.filter((_, i) => i !== idx));
  };

  const updateEntry = (idx, field, value) => {
    setEntries(prev => prev.map((e, i) => i === idx ? { ...e, [field]: value } : e));
  };

  const handleAnalyze = () => {
    const validFiles = entries.filter(e => e.name && e.content.trim());
    if (validFiles.length === 0) return;
    onAnalyze(validFiles);
  };

  const handleFileUpload = (e) => {
    const files = Array.from(e.target.files);
    const newEntries = [];
    let processed = 0;

    files.forEach(file => {
      const reader = new FileReader();
      reader.onload = (ev) => {
        newEntries.push({ name: file.name, content: ev.target.result });
        processed++;
        if (processed === files.length) {
          setEntries(prev => [...prev.filter(e => e.content.trim()), ...newEntries]);
        }
      };
      reader.readAsText(file);
    });
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const files = Array.from(e.dataTransfer.files).filter(f => f.name.endsWith('.py'));
    if (files.length === 0) return;

    const newEntries = [];
    let processed = 0;
    files.forEach(file => {
      const reader = new FileReader();
      reader.onload = (ev) => {
        newEntries.push({ name: file.name, content: ev.target.result });
        processed++;
        if (processed === files.length) {
          setEntries(prev => [...prev.filter(e => e.content.trim()), ...newEntries]);
        }
      };
      reader.readAsText(file);
    });
  };

  return (
    <div className="p-4 space-y-3">
      <div className="flex items-center gap-2 mb-2">
        <button
          onClick={onLoadDemo}
          disabled={loading}
          className="flex-1 py-2 px-3 bg-sky-600 hover:bg-sky-500 disabled:bg-sky-800 text-white text-sm font-medium rounded-lg transition-colors"
        >
          Load Demo
        </button>
        <button
          onClick={handleAnalyze}
          disabled={loading}
          className="flex-1 py-2 px-3 bg-emerald-600 hover:bg-emerald-500 disabled:bg-emerald-800 text-white text-sm font-medium rounded-lg transition-colors"
        >
          {loading ? 'Analyzing...' : 'Analyze'}
        </button>
      </div>

      {/* Mode toggle */}
      <div className="flex text-xs border border-slate-600 rounded-md overflow-hidden">
        <button
          onClick={() => setMode('paste')}
          className={`flex-1 py-1.5 ${mode === 'paste' ? 'bg-slate-600 text-white' : 'text-slate-400 hover:text-white'}`}
        >
          Paste Code
        </button>
        <button
          onClick={() => setMode('upload')}
          className={`flex-1 py-1.5 ${mode === 'upload' ? 'bg-slate-600 text-white' : 'text-slate-400 hover:text-white'}`}
        >
          Upload Files
        </button>
      </div>

      {mode === 'paste' ? (
        <div className="space-y-2 max-h-48 overflow-y-auto">
          {entries.map((entry, idx) => (
            <div key={idx} className="space-y-1">
              <div className="flex items-center gap-1">
                <input
                  type="text"
                  value={entry.name}
                  onChange={(e) => updateEntry(idx, 'name', e.target.value)}
                  className="flex-1 bg-slate-700 text-xs text-slate-200 px-2 py-1 rounded border border-slate-600 focus:border-sky-500 outline-none"
                  placeholder="filename.py"
                />
                {entries.length > 1 && (
                  <button onClick={() => removeEntry(idx)}
                    className="text-slate-500 hover:text-red-400 text-xs px-1">
                    ✕
                  </button>
                )}
              </div>
              <textarea
                value={entry.content}
                onChange={(e) => updateEntry(idx, 'content', e.target.value)}
                className="w-full h-20 bg-slate-900 text-xs text-slate-300 p-2 rounded border border-slate-600 focus:border-sky-500 outline-none font-mono resize-none"
                placeholder="Paste Python code here..."
              />
            </div>
          ))}
          <button onClick={addEntry}
            className="text-xs text-sky-400 hover:text-sky-300">
            + Add another file
          </button>
        </div>
      ) : (
        <div
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
          onClick={() => fileInputRef.current?.click()}
          className="border-2 border-dashed border-slate-600 rounded-lg p-6 text-center cursor-pointer hover:border-sky-500 transition-colors"
        >
          <p className="text-sm text-slate-400">Drop .py files here or click to upload</p>
          <input
            ref={fileInputRef}
            type="file"
            accept=".py"
            multiple
            onChange={handleFileUpload}
            className="hidden"
          />
        </div>
      )}

      {entries.some(e => e.content.trim()) && (
        <p className="text-xs text-slate-500">
          {entries.filter(e => e.content.trim()).length} file(s) ready
        </p>
      )}
    </div>
  );
}
