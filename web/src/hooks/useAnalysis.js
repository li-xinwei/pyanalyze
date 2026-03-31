import { useState, useCallback } from 'react';
import axios from 'axios';
import demoData from '../demo/demo_result.json';

const API_URL = import.meta.env.VITE_API_URL || '';

export function useAnalysis() {
  const [graph, setGraph] = useState(null);
  const [slice, setSlice] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [files, setFiles] = useState([]);

  const analyze = useCallback(async (inputFiles) => {
    setLoading(true);
    setError(null);
    setSlice(null);
    setFiles(inputFiles);
    try {
      const res = await axios.post(`${API_URL}/api/analyze`, { files: inputFiles });
      setGraph(res.data);
    } catch (e) {
      setError(e.response?.data?.error || e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const computeSlice = useCallback(async (target) => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.post(`${API_URL}/api/slice`, { files, target });
      setSlice(res.data.slice || res.data);
    } catch (e) {
      setError(e.response?.data?.error || e.message);
    } finally {
      setLoading(false);
    }
  }, [files]);

  const loadDemo = useCallback(async () => {
    setLoading(true);
    setError(null);
    setSlice(null);
    try {
      const res = await axios.get(`${API_URL}/api/demo`);
      setGraph(res.data);
    } catch (e) {
      setGraph(demoData);
    } finally {
      setLoading(false);
    }
  }, []);

  const clearSlice = useCallback(() => {
    setSlice(null);
  }, []);

  return { graph, slice, loading, error, analyze, computeSlice, loadDemo, clearSlice };
}
