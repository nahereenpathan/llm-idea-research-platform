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
  CheckCircle2,
  AlertCircle,
  RotateCcw,
  ChevronLeft,
  ChevronRight,
  Eye,
  X,
  FileCheck,
  KeyRound,
  Sparkles
} from 'lucide-react';

export default function PatentSearchPage() {
  const { id } = useParams();
  const projectId = parseInt(id);
  const { setActiveProject } = useProject();

  const [activeTab, setActiveTab] = useState('search'); // 'search' or 'saved'
  const [sources, setSources] = useState([]);
  const [selectedSource, setSelectedSource] = useState('uspto');
  const [searchType, setSearchType] = useState('keyword'); // 'keyword', 'concept', 'title', 'number'
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(10);
  const [totalCount, setTotalCount] = useState(null);

  const [searchResults, setSearchResults] = useState([]);
  const [savedPatents, setSavedPatents] = useState([]);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState(null);
  const [disclaimer, setDisclaimer] = useState('');
  const [detailPatent, setDetailPatent] = useState(null);
  const [savedFilterQuery, setSavedFilterQuery] = useState('');

  const loadData = async () => {
    try {
      const proj = await projectService.getProject(projectId);
      setActiveProject(proj);
      const list = await researchService.getSavedPatents(projectId);
      setSavedPatents(list);
    } catch (err) {
      console.error("Error loading project or patents:", err);
    }

    try {
      const srcList = await researchService.getPatentSources();
      setSources(srcList);
    } catch (err) {
      console.error("Error fetching patent sources:", err);
    }
  };

  useEffect(() => {
    loadData();
  }, [projectId]);

  const executeSearch = async (targetPage = 1) => {
    if (!query.trim()) return;
    setSearching(true);
    setSearchError(null);
    setPage(targetPage);

    try {
      const data = await researchService.searchPatents(
        query.trim(),
        selectedSource,
        searchType,
        targetPage,
        limit
      );
      setSearchResults(data.results || []);
      setTotalCount(data.total_count || null);
      setDisclaimer(data.disclaimer || '');
    } catch (err) {
      const msg = err.response?.data?.detail || "Failed to search patent registry. Check provider credentials or service availability.";
      setSearchError(msg);
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    executeSearch(1);
  };

  const isPatentSaved = (patent) => {
    return savedPatents.some((p) => p.patent_number === patent.patent_number);
  };

  const handleSavePatent = async (patent) => {
    try {
      await researchService.savePatent(projectId, {
        patent_number: patent.patent_number,
        title: patent.title,
        inventors: patent.inventors || [],
        publication_date: patent.publication_date,
        filing_date: patent.filing_date,
        abstract: patent.abstract,
        status: patent.status,
        source: patent.source,
        source_url: patent.source_url,
        similarity_notes: patent.similarity_notes
      });
      const updated = await researchService.getSavedPatents(projectId);
      setSavedPatents(updated);
    } catch (err) {
      if (err.response?.status === 409) {
        alert("This patent record is already saved in your project reference library.");
      } else {
        alert("Failed to save patent record.");
      }
    }
  };

  const handleDeletePatent = async (patentId) => {
    if (window.confirm("Remove this patent record from your project library?")) {
      try {
        await researchService.deletePatent(patentId);
        const updated = await researchService.getSavedPatents(projectId);
        setSavedPatents(updated);
      } catch (err) {
        alert("Failed to delete patent.");
      }
    }
  };

  const currentSourceObj = sources.find((s) => s.id === selectedSource) || {
    id: selectedSource,
    name: selectedSource.toUpperCase(),
    requires_key: true,
    is_configured: false,
    status: 'unconfigured',
    description: 'Patent registry adapter.'
  };

  const filteredSavedPatents = savedPatents.filter((p) => {
    if (!savedFilterQuery.trim()) return true;
    const q = savedFilterQuery.toLowerCase();
    return (
      p.patent_number?.toLowerCase().includes(q) ||
      p.title?.toLowerCase().includes(q) ||
      p.abstract?.toLowerCase().includes(q) ||
      p.similarity_notes?.toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <Scale className="w-5 h-5 text-brand-400" /> Patent Prior Art Search & Analysis
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Query official patent metadata adapters (USPTO Open Data Portal & European Patent Office OPS) for prior art evidence.
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

      {/* Mandatory Legal & Epistemic Disclaimer Banner */}
      <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-200/90 flex items-start gap-3 shadow-sm">
        <ShieldAlert className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <strong className="text-amber-300 font-semibold text-xs flex items-center gap-1.5">
            Legal Notice & Prior-Art Disclaimer
          </strong>
          <p className="leading-relaxed text-[11px] text-amber-200/80">
            Automated patent searches identify technical concept overlap and potential prior art references based on retrieved metadata.
            This service does <strong>NOT</strong> establish definitive legal patentability, freedom-to-operate (FTO), non-infringement,
            or formal claims validity. Formal intellectual property diligence requires consultation with a registered patent attorney or agent.
          </p>
        </div>
      </div>

      {/* SEARCH TAB */}
      {activeTab === 'search' && (
        <div className="space-y-6">
          {/* Search Form */}
          <form onSubmit={handleSearchSubmit} className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-sm space-y-4">
            <div className="flex flex-col lg:flex-row gap-3">
              <div className="flex-1 relative">
                <Search className="w-4 h-4 text-slate-500 absolute left-3 top-3.5" />
                <input
                  type="text"
                  required
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder={
                    searchType === 'number'
                      ? "Enter patent number (e.g. 'US10289965' or 'EP3124567')"
                      : searchType === 'concept'
                      ? "Describe technical concept (e.g. 'reinforcement learning robot trajectory planning')"
                      : searchType === 'title'
                      ? "Search invention title (e.g. 'machine learning task pipeline')"
                      : "Search patent claims, title, or technical problem..."
                  }
                  className="w-full pl-9 pr-3 py-2.5 bg-slate-950 border border-slate-700/80 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500 transition-colors"
                />
              </div>

              <div className="flex flex-wrap items-center gap-2">
                {/* Search Type Selector */}
                <select
                  value={searchType}
                  onChange={(e) => setSearchType(e.target.value)}
                  className="px-3 py-2.5 bg-slate-950 border border-slate-700/80 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-brand-500"
                >
                  <option value="keyword">All Terms</option>
                  <option value="concept">Technical Concept</option>
                  <option value="title">Patent Title</option>
                  <option value="number">Patent Number</option>
                </select>

                {/* Registry Selector */}
                <select
                  value={selectedSource}
                  onChange={(e) => setSelectedSource(e.target.value)}
                  className="px-3 py-2.5 bg-slate-950 border border-slate-700/80 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-brand-500"
                >
                  <option value="uspto">USPTO Open Data Portal (US)</option>
                  <option value="epo">European Patent Office OPS (EP)</option>
                </select>

                <button
                  type="submit"
                  disabled={searching}
                  className="px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold flex items-center justify-center gap-2 shadow-md disabled:opacity-50 transition-all"
                >
                  {searching ? (
                    <span className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                  ) : (
                    <Search className="w-4 h-4" />
                  )}
                  Search Patents
                </button>
              </div>
            </div>

            {/* Provider status line */}
            <div className="flex items-center justify-between text-xs pt-1 border-t border-slate-800/80">
              <div className="flex items-center gap-2 text-slate-400 text-[11px]">
                <span className={`w-2 h-2 rounded-full ${currentSourceObj.status === 'active' ? 'bg-emerald-400' : 'bg-amber-400'}`} />
                <span className="font-medium text-slate-300">{currentSourceObj.name}:</span>
                <span>{currentSourceObj.description}</span>
              </div>
              <span className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded ${
                currentSourceObj.status === 'active' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
              }`}>
                {currentSourceObj.status === 'active' ? 'Configured' : 'Requires API Key in .env'}
              </span>
            </div>
          </form>

          {/* Configuration Hint Banner if unconfigured */}
          {currentSourceObj.status === 'unconfigured' && (
            <div className="p-4 rounded-2xl bg-slate-900 border border-amber-500/30 text-xs space-y-2">
              <div className="flex items-center gap-2 text-amber-300 font-semibold">
                <KeyRound className="w-4 h-4 text-amber-400" />
                <span>Provider Configuration Guide: {currentSourceObj.name}</span>
              </div>
              <p className="text-slate-300 text-[11px] leading-relaxed">
                Official patent registry data services require developer credentials to protect public infrastructure.
                To enable live {selectedSource.toUpperCase()} searches:
              </p>
              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 font-mono text-[11px] text-slate-300">
                {selectedSource === 'uspto' ? (
                  <>
                    <p className="text-slate-500"># In backend/.env:</p>
                    <p className="text-emerald-400">USPTO_API_KEY=your_uspto_open_data_api_key</p>
                  </>
                ) : (
                  <>
                    <p className="text-slate-500"># In backend/.env:</p>
                    <p className="text-emerald-400">EPO_CONSUMER_KEY=your_epo_consumer_key</p>
                    <p className="text-emerald-400">EPO_CONSUMER_SECRET=your_epo_consumer_secret</p>
                  </>
                )}
              </div>
              <p className="text-slate-400 text-[11px]">
                Note: Academic Research Paper search (OpenAlex and Crossref) is completely active and requires no credentials.
              </p>
            </div>
          )}

          {/* Search Error State */}
          {searchError && (
            <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/20 text-xs text-red-300 flex items-start justify-between gap-3 animate-fade-in">
              <div className="flex items-start gap-2.5">
                <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                <div>
                  <strong className="text-red-200">Search Error:</strong>
                  <p className="text-slate-300 mt-0.5">{searchError}</p>
                </div>
              </div>
              <button
                onClick={() => executeSearch(page)}
                className="px-3 py-1.5 rounded-lg bg-red-500/20 hover:bg-red-500/30 text-red-200 text-xs font-semibold flex items-center gap-1.5 shrink-0 transition-colors"
              >
                <RotateCcw className="w-3.5 h-3.5" /> Retry
              </button>
            </div>
          )}

          {/* Loading Skeleton */}
          {searching && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[1, 2, 3, 4].map((n) => (
                <div key={n} className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 space-y-3 animate-pulse">
                  <div className="h-4 bg-slate-800 rounded w-1/3" />
                  <div className="h-5 bg-slate-800 rounded w-3/4" />
                  <div className="h-16 bg-slate-950 rounded-xl" />
                </div>
              ))}
            </div>
          )}

          {/* Empty State */}
          {searchResults.length === 0 && !searching && !searchError && (
            <div className="text-center py-16 bg-slate-900/30 border border-dashed border-slate-800 rounded-2xl">
              <Scale className="w-10 h-10 text-slate-600 mx-auto mb-3" />
              <p className="text-sm font-medium text-slate-300">Patent Prior Art Search</p>
              <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
                Search official patent registries to discover prior technical concepts and evaluate novelty distance.
                Direct Google Patents and Espacenet links are indexed for complete legal file wrappers.
              </p>
            </div>
          )}

          {/* Results Header */}
          {searchResults.length > 0 && !searching && (
            <div className="flex items-center justify-between text-xs text-slate-400 px-1">
              <div>
                Showing {searchResults.length} patent documents
                {totalCount !== null && ` of ~${totalCount.toLocaleString()} indexed records`}
                <span className="text-slate-500 ml-1.5 font-mono">({selectedSource.toUpperCase()})</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[11px]">Page {page}</span>
                <button
                  onClick={() => executeSearch(page - 1)}
                  disabled={page <= 1 || searching}
                  className="p-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 disabled:opacity-40"
                  title="Previous Page"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button
                  onClick={() => executeSearch(page + 1)}
                  disabled={searching || searchResults.length < limit}
                  className="p-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 disabled:opacity-40"
                  title="Next Page"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {/* Results Grid */}
          {!searching && searchResults.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {searchResults.map((pat, idx) => {
                const saved = isPatentSaved(pat);
                return (
                  <div
                    key={idx}
                    className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 flex flex-col justify-between hover:border-slate-700 transition-all space-y-3 shadow-sm"
                  >
                    <div className="space-y-2">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-xs font-bold font-mono text-brand-400 px-2 py-0.5 rounded bg-brand-500/10 border border-brand-500/20">
                          {pat.patent_number}
                        </span>
                        <span className="text-[10px] font-medium text-emerald-400 px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20">
                          {pat.status || 'Published'}
                        </span>
                      </div>

                      <h3 className="text-sm font-bold text-white line-clamp-2 hover:text-brand-300 transition-colors">
                        {pat.title}
                      </h3>

                      <div className="flex items-center gap-2 text-xs text-slate-400">
                        <User className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                        <span className="line-clamp-1">{pat.inventors?.join(', ') || 'Official Applicant Record'}</span>
                      </div>

                      <div className="flex items-center gap-3 text-[11px] text-slate-400">
                        {pat.filing_date && <span>Filed: {pat.filing_date}</span>}
                        {pat.publication_date && <span>Pub: {pat.publication_date}</span>}
                      </div>

                      <p className="text-xs text-slate-300 line-clamp-3 bg-slate-950/60 p-3 rounded-xl border border-slate-800/80 leading-relaxed">
                        {pat.abstract}
                      </p>

                      {pat.similarity_notes && (
                        <div className="p-2.5 rounded-xl bg-brand-500/5 border border-brand-500/15 text-[11px] text-brand-300 flex items-start gap-1.5">
                          <Sparkles className="w-3.5 h-3.5 text-brand-400 shrink-0 mt-0.5" />
                          <span>{pat.similarity_notes}</span>
                        </div>
                      )}
                    </div>

                    <div className="pt-3 border-t border-slate-800 flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => setDetailPatent(pat)}
                          className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium flex items-center gap-1 transition-colors"
                        >
                          <Eye className="w-3.5 h-3.5" /> Details
                        </button>

                        {pat.source_url && (
                          <a
                            href={pat.source_url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-brand-400 hover:underline flex items-center gap-1 text-[11px]"
                          >
                            Google Patents <ExternalLink className="w-3 h-3" />
                          </a>
                        )}
                      </div>

                      <button
                        onClick={() => handleSavePatent(pat)}
                        disabled={saved}
                        className={`px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1 transition-colors ${
                          saved
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 cursor-default'
                            : 'bg-brand-600 hover:bg-brand-500 text-white shadow-sm'
                        }`}
                      >
                        {saved ? (
                          <>
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> Saved
                          </>
                        ) : (
                          <>
                            <BookmarkPlus className="w-3.5 h-3.5" /> Save
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Bottom Pagination */}
          {searchResults.length > 0 && !searching && (
            <div className="flex items-center justify-center gap-3 pt-4">
              <button
                onClick={() => executeSearch(page - 1)}
                disabled={page <= 1 || searching}
                className="px-4 py-2 rounded-xl bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 text-xs font-semibold disabled:opacity-40 flex items-center gap-1.5"
              >
                <ChevronLeft className="w-4 h-4" /> Previous Page
              </button>
              <span className="text-xs text-slate-400 font-mono px-3 py-1 rounded-lg bg-slate-950 border border-slate-800">
                Page {page}
              </span>
              <button
                onClick={() => executeSearch(page + 1)}
                disabled={searching || searchResults.length < limit}
                className="px-4 py-2 rounded-xl bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 text-xs font-semibold disabled:opacity-40 flex items-center gap-1.5"
              >
                Next Page <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      )}

      {/* SAVED PATENTS TAB */}
      {activeTab === 'saved' && (
        <div className="space-y-4">
          {savedPatents.length > 0 && (
            <div className="relative">
              <Search className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
              <input
                type="text"
                value={savedFilterQuery}
                onChange={(e) => setSavedFilterQuery(e.target.value)}
                placeholder="Filter saved patent records by number, title, or concept notes..."
                className="w-full pl-9 pr-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500"
              />
            </div>
          )}

          {savedPatents.length === 0 ? (
            <div className="text-center py-16 bg-slate-900/40 border border-dashed border-slate-800 rounded-2xl">
              <BookmarkPlus className="w-8 h-8 text-slate-600 mx-auto mb-2" />
              <p className="text-sm font-medium text-slate-300">No Saved Patents</p>
              <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
                Save relevant patent records during your prior art search to compare technical claims and include them in novelty evaluations.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredSavedPatents.map((pat) => (
                <div key={pat.id} className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold font-mono text-brand-400 px-2 py-0.5 rounded bg-brand-500/10 border border-brand-500/20">
                      {pat.patent_number}
                    </span>
                    <button
                      onClick={() => handleDeletePatent(pat.id)}
                      className="p-1 rounded text-slate-500 hover:text-red-400 hover:bg-slate-800 transition-colors"
                      title="Remove patent from library"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  <h3 className="text-sm font-bold text-white">{pat.title}</h3>
                  <p className="text-xs text-slate-400">{pat.inventors?.join(', ')} • {pat.publication_date || 'N/A'}</p>

                  <p className="text-xs text-slate-300 line-clamp-3 bg-slate-950/60 p-3 rounded-xl border border-slate-800">
                    {pat.abstract}
                  </p>

                  {pat.similarity_notes && (
                    <p className="text-[11px] text-brand-300 bg-brand-500/5 p-2 rounded-lg border border-brand-500/15">
                      {pat.similarity_notes}
                    </p>
                  )}

                  {pat.source_url && (
                    <a
                      href={pat.source_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-brand-400 hover:underline flex items-center gap-1 text-[11px] pt-1"
                    >
                      View Full File Wrapper in Google Patents <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* PATENT DETAIL MODAL */}
      {detailPatent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl p-6 space-y-4 max-h-[90vh] overflow-y-auto shadow-2xl">
            <div className="flex items-start justify-between gap-3 border-b border-slate-800 pb-3">
              <div>
                <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-brand-500/10 text-brand-400 border border-brand-500/20">
                  {detailPatent.patent_number}
                </span>
                <h2 className="text-base font-bold text-white mt-1.5">{detailPatent.title}</h2>
              </div>
              <button
                onClick={() => setDetailPatent(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs text-slate-300">
              <div>
                <strong className="text-slate-400">Inventors / Assignees:</strong>
                <p className="text-white mt-0.5">{detailPatent.inventors?.join(', ') || 'Official Applicant'}</p>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800">
                  <span className="text-[10px] text-slate-500 uppercase block font-semibold">Publication Date</span>
                  <span className="text-white font-medium">{detailPatent.publication_date || 'N/A'}</span>
                </div>
                <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800">
                  <span className="text-[10px] text-slate-500 uppercase block font-semibold">Filing Date</span>
                  <span className="text-white font-medium">{detailPatent.filing_date || 'N/A'}</span>
                </div>
                <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800">
                  <span className="text-[10px] text-slate-500 uppercase block font-semibold">Status</span>
                  <span className="text-emerald-400 font-medium">{detailPatent.status || 'Published'}</span>
                </div>
              </div>

              {detailPatent.similarity_notes && (
                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-1">
                  <strong className="text-brand-400 text-[11px] block">Observed Concept Overlap:</strong>
                  <p className="text-slate-200">{detailPatent.similarity_notes}</p>
                </div>
              )}

              <div>
                <strong className="text-slate-400">Bibliographic Abstract:</strong>
                <p className="text-slate-200 leading-relaxed bg-slate-950 p-3.5 rounded-xl border border-slate-800 mt-1 max-h-60 overflow-y-auto">
                  {detailPatent.abstract}
                </p>
              </div>
            </div>

            <div className="flex items-center justify-between pt-3 border-t border-slate-800">
              {detailPatent.source_url ? (
                <a
                  href={detailPatent.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-brand-400 hover:underline flex items-center gap-1 text-xs"
                >
                  View Claims on Google Patents <ExternalLink className="w-3.5 h-3.5" />
                </a>
              ) : <div />}
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setDetailPatent(null)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
                >
                  Close
                </button>
                {!isPatentSaved(detailPatent) && (
                  <button
                    onClick={() => {
                      handleSavePatent(detailPatent);
                      setDetailPatent(null);
                    }}
                    className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow"
                  >
                    <BookmarkPlus className="w-3.5 h-3.5" /> Save to Library
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
