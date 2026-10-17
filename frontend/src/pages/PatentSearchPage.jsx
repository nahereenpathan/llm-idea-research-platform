import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { researchService } from '../services/researchService';
import { projectService } from '../services/projectService';
import { useProject } from '../contexts/ProjectContext';
import {
  Search,
  ShieldAlert,
  ExternalLink,
  BookmarkPlus,
  Trash2,
  Calendar,
  User,
  Scale,
  FileCheck
} from 'lucide-react';

export default function PatentSearchPage() {
  const { id } = useParams();
  const projectId = parseInt(id);
  const { setActiveProject } = useProject();

  const [activeTab, setActiveTab] = useState('search');
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [savedPatents, setSavedPatents] = useState([]);
  const [searching, setSearching] = useState(false);
  const [disclaimer, setDisclaimer] = useState('');

  const fetchSaved = async () => {
    try {
      const proj = await projectService.getProject(projectId);
      setActiveProject(proj);
      const list = await researchService.getSavedPatents(projectId);
      setSavedPatents(list);
    } catch (err) {
      console.error("Error loading saved patents:", err);
    }
  };

  useEffect(() => {
    fetchSaved();
  }, [projectId]);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    setSearching(true);
    try {
      const data = await researchService.searchPatents(query, 12);
      setSearchResults(data.results || []);
      setDisclaimer(data.disclaimer || '');
    } catch (err) {
      alert("Failed to search patents.");
    } finally {
      setSearching(false);
    }
  };

  const handleSavePatent = async (patent) => {
    try {
      await researchService.savePatent(projectId, {
        patent_number: patent.patent_number,
        title: patent.title,
        inventors: patent.inventors,
        publication_date: patent.publication_date,
        filing_date: patent.filing_date,
        abstract: patent.abstract,
        status: patent.status,
        source: patent.source,
        source_url: patent.source_url,
        similarity_notes: patent.similarity_notes
      });
      await fetchSaved();
      alert("Patent record saved to project library!");
    } catch (err) {
      alert("Failed to save patent record.");
    }
  };

  const handleDeletePatent = async (patentId) => {
    if (window.confirm("Remove this patent from project library?")) {
      try {
        await researchService.deletePatent(patentId);
        await fetchSaved();
      } catch (err) {
        alert("Failed to delete patent.");
      }
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <Search className="w-5 h-5 text-brand-400" /> Patent Prior Art Search
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Search official USPTO patent records to discover related technical concepts and evaluate novelty distance.
          </p>
        </div>

        <div className="flex bg-slate-900 border border-slate-800 p-1 rounded-xl self-start sm:self-auto">
          <button
            onClick={() => setActiveTab('search')}
            className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'search' ? 'bg-brand-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Patent Search
          </button>
          <button
            onClick={() => setActiveTab('saved')}
            className={`px-4 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
              activeTab === 'saved' ? 'bg-brand-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Saved Patents ({savedPatents.length})
          </button>
        </div>
      </div>

      {/* Mandatory Legal Disclaimer Banner */}
      <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300/90 flex items-start gap-3">
        <ShieldAlert className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
        <div className="space-y-0.5">
          <strong className="text-amber-200">Legal Notice & Epistemic Disclaimer:</strong>
          <p className="leading-relaxed text-[11px]">
            Automated patent searches identify technical concept overlap and potential prior art. An automated search does NOT determine definitive legal patentability, non-infringement, or freedom-to-operate. Always consult a registered patent attorney for formal legal diligence.
          </p>
        </div>
      </div>

      {/* SEARCH TAB */}
      {activeTab === 'search' && (
        <div className="space-y-6">
          <form onSubmit={handleSearch} className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-sm flex flex-col sm:flex-row gap-3">
            <div className="flex-1 relative">
              <Search className="w-4 h-4 text-slate-500 absolute left-3 top-3.5" />
              <input
                type="text"
                required
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search patent title, claims, or technical problem (e.g., 'machine learning pipeline automation')"
                className="w-full pl-9 pr-3 py-2.5 bg-slate-950 border border-slate-700/80 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500"
              />
            </div>
            <button
              type="submit"
              disabled={searching}
              className="px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold flex items-center justify-center gap-2 shadow-md disabled:opacity-50"
            >
              {searching ? (
                <span className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
              ) : (
                <Search className="w-4 h-4" />
              )}
              Search Patents
            </button>
          </form>

          {searchResults.length === 0 && !searching && (
            <div className="text-center py-12 bg-slate-900/30 border border-dashed border-slate-800 rounded-2xl">
              <Scale className="w-8 h-8 text-slate-600 mx-auto mb-2" />
              <p className="text-xs text-slate-400">Search for granted patents and published applications above.</p>
              <p className="text-[11px] text-slate-500 mt-1">Direct Google Patents links and publication numbers are indexed.</p>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {searchResults.map((pat, idx) => (
              <div key={idx} className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 flex flex-col justify-between hover:border-slate-700 transition-all space-y-3">
                <div className="space-y-2">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-bold font-mono text-brand-400 px-2 py-0.5 rounded bg-brand-500/10 border border-brand-500/20">
                      {pat.patent_number}
                    </span>
                    <span className="text-[10px] font-medium text-emerald-400 px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20">
                      {pat.status || 'Active Grant'}
                    </span>
                  </div>

                  <h3 className="text-sm font-bold text-white line-clamp-2">{pat.title}</h3>

                  <div className="flex items-center gap-2 text-xs text-slate-400">
                    <User className="w-3.5 h-3.5 text-slate-500" />
                    <span className="line-clamp-1">{pat.inventors?.join(', ')}</span>
                  </div>

                  <p className="text-xs text-slate-300 line-clamp-3 bg-slate-950/60 p-3 rounded-xl border border-slate-800 leading-relaxed">
                    {pat.abstract}
                  </p>

                  {pat.similarity_notes && (
                    <p className="text-[11px] text-amber-300/80 italic">
                      Concept Overlap: {pat.similarity_notes}
                    </p>
                  )}
                </div>

                <div className="pt-3 border-t border-slate-800 flex items-center justify-between text-xs">
                  {pat.source_url && (
                    <a
                      href={pat.source_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-brand-400 hover:underline flex items-center gap-1 text-[11px]"
                    >
                      Google Patents Record <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                  <button
                    onClick={() => handleSavePatent(pat)}
                    className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-brand-600 text-slate-200 hover:text-white text-xs font-medium flex items-center gap-1 transition-colors"
                  >
                    <BookmarkPlus className="w-3.5 h-3.5" /> Save
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* SAVED PATENTS TAB */}
      {activeTab === 'saved' && (
        <div className="space-y-4">
          {savedPatents.length === 0 ? (
            <div className="text-center py-16 bg-slate-900/40 border border-dashed border-slate-800 rounded-2xl">
              <BookmarkPlus className="w-8 h-8 text-slate-600 mx-auto mb-2" />
              <p className="text-sm font-medium text-slate-300">No Saved Patents</p>
              <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
                Save relevant patent records during your search to compare technical claims and include them in reports.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {savedPatents.map((pat) => (
                <div key={pat.id} className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold font-mono text-brand-400 px-2 py-0.5 rounded bg-brand-500/10 border border-brand-500/20">
                      {pat.patent_number}
                    </span>
                    <button
                      onClick={() => handleDeletePatent(pat.id)}
                      className="p-1 rounded text-slate-500 hover:text-red-400 hover:bg-slate-800"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  <h3 className="text-sm font-bold text-white">{pat.title}</h3>
                  <p className="text-xs text-slate-400">{pat.inventors?.join(', ')} • {pat.publication_date || 'N/A'}</p>

                  <p className="text-xs text-slate-300 line-clamp-3 bg-slate-950/60 p-3 rounded-xl border border-slate-800">
                    {pat.abstract}
                  </p>

                  {pat.source_url && (
                    <a
                      href={pat.source_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-brand-400 hover:underline flex items-center gap-1 text-[11px] pt-1"
                    >
                      View Original USPTO/Google Record <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
