import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { researchService } from '../services/researchService';
import { projectService } from '../services/projectService';
import { useProject } from '../contexts/ProjectContext';
import {
  BookOpen,
  Search,
  BookmarkPlus,
  ExternalLink,
  Sparkles,
  Trash2,
  Edit3,
  CheckCircle2,
  Filter,
  User,
  Calendar,
  AlertCircle,
  RotateCcw,
  ChevronLeft,
  ChevronRight,
  Info,
  Copy,
  Check,
  X,
  History,
  ShieldCheck,
  Eye
} from 'lucide-react';

export default function ResearchWorkspace() {
  const { id } = useParams();
  const projectId = parseInt(id);
  const { setActiveProject } = useProject();

  const [activeTab, setActiveTab] = useState('search'); // 'search' or 'saved'
  const [sources, setSources] = useState([]);
  const [selectedSource, setSelectedSource] = useState('openalex');
  const [searchType, setSearchType] = useState('keyword'); // 'keyword', 'title', 'author', 'doi'
  const [query, setQuery] = useState('');
  const [yearFrom, setYearFrom] = useState('');
  const [yearTo, setYearTo] = useState('');
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(10);
  const [totalCount, setTotalCount] = useState(null);

  const [searchResults, setSearchResults] = useState([]);
  const [savedPapers, setSavedPapers] = useState([]);
  const [searchHistory, setSearchHistory] = useState([]);

  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState(null);
  const [summarizingId, setSummarizingId] = useState(null);
  const [editingPaper, setEditingPaper] = useState(null);
  const [noteText, setNoteText] = useState('');
  const [detailPaper, setDetailPaper] = useState(null);
  const [copiedDoi, setCopiedDoi] = useState(false);
  const [savedFilterQuery, setSavedFilterQuery] = useState('');

  // Fetch sources and saved papers
  const loadInitialData = async () => {
    try {
      const proj = await projectService.getProject(projectId);
      setActiveProject(proj);
      const list = await researchService.getSavedPapers(projectId);
      setSavedPapers(list);
    } catch (err) {
      console.error("Error loading project or papers:", err);
    }

    try {
      const srcList = await researchService.getPaperSources();
      setSources(srcList);
    } catch (err) {
      console.error("Error fetching paper sources:", err);
    }

    // Load search history from local storage
    try {
      const stored = localStorage.getItem('idealens_paper_search_history');
      if (stored) {
        setSearchHistory(JSON.parse(stored).slice(0, 5));
      }
    } catch (e) {
      console.error("Failed to parse history", e);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, [projectId]);

  const saveToHistory = (newQuery) => {
    const trimmed = newQuery.trim();
    if (!trimmed) return;
    const updated = [trimmed, ...searchHistory.filter((q) => q.toLowerCase() !== trimmed.toLowerCase())].slice(0, 5);
    setSearchHistory(updated);
    try {
      localStorage.setItem('idealens_paper_search_history', JSON.stringify(updated));
    } catch (e) {
      console.error("Failed to store history", e);
    }
  };

  const executeSearch = async (targetPage = 1) => {
    if (!query.trim()) return;
    setSearching(true);
    setSearchError(null);
    setPage(targetPage);

    try {
      const data = await researchService.searchPapers(
        query.trim(),
        selectedSource,
        yearFrom ? parseInt(yearFrom) : null,
        yearTo ? parseInt(yearTo) : null,
        searchType,
        targetPage,
        limit
      );
      setSearchResults(data.results || []);
      setTotalCount(data.total_count || null);
      saveToHistory(query);
    } catch (err) {
      const msg = err.response?.data?.detail || "Scholarly search encountered an error. Check network connection or API status.";
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

  const isPaperSaved = (paper) => {
    return savedPapers.some((p) => {
      if (paper.external_id && p.external_id === paper.external_id) return true;
      if (paper.doi && p.doi === paper.doi) return true;
      if (paper.title && p.title.toLowerCase() === paper.title.toLowerCase()) return true;
      return false;
    });
  };

  const handleSavePaper = async (paper) => {
    try {
      await researchService.savePaper(projectId, {
        external_id: paper.external_id,
        source: paper.source,
        title: paper.title,
        authors: paper.authors || [],
        publication_year: paper.publication_year,
        publication_date: paper.publication_date,
        abstract: paper.abstract,
        doi: paper.doi,
        source_url: paper.source_url,
        venue: paper.venue,
        citation_count: paper.citation_count || 0,
        is_open_access: paper.is_open_access || false
      });
      const updated = await researchService.getSavedPapers(projectId);
      setSavedPapers(updated);
    } catch (err) {
      if (err.response?.status === 409) {
        alert("Paper is already saved in this project library.");
      } else {
        alert("Failed to save paper. Please try again.");
      }
    }
  };

  const handleDeletePaper = async (paperId) => {
    if (window.confirm("Remove this paper from your project reference library?")) {
      try {
        await researchService.deletePaper(paperId);
        const updated = await researchService.getSavedPapers(projectId);
        setSavedPapers(updated);
      } catch (err) {
        alert("Failed to delete paper.");
      }
    }
  };

  const handleSummarize = async (paperId) => {
    setSummarizingId(paperId);
    try {
      await researchService.summarizePaper(paperId);
      const updated = await researchService.getSavedPapers(projectId);
      setSavedPapers(updated);
    } catch (err) {
      const msg = err.response?.data?.detail || "Failed to generate AI summary.";
      alert(msg);
    } finally {
      setSummarizingId(null);
    }
  };

  const handleSaveNote = async () => {
    if (!editingPaper) return;
    try {
      await researchService.updatePaper(editingPaper.id, { user_notes: noteText });
      setEditingPaper(null);
      const updated = await researchService.getSavedPapers(projectId);
      setSavedPapers(updated);
    } catch (err) {
      alert("Failed to update notes.");
    }
  };

  const handleCopyDoi = (doiText) => {
    if (!doiText) return;
    navigator.clipboard.writeText(doiText);
    setCopiedDoi(true);
    setTimeout(() => setCopiedDoi(false), 2000);
  };

  const filteredSavedPapers = savedPapers.filter((p) => {
    if (!savedFilterQuery.trim()) return true;
    const q = savedFilterQuery.toLowerCase();
    return (
      p.title?.toLowerCase().includes(q) ||
      p.abstract?.toLowerCase().includes(q) ||
      p.authors?.some((a) => a.toLowerCase().includes(q))
    );
  });

  const currentSourceObj = sources.find((s) => s.id === selectedSource) || {
    id: selectedSource,
    name: selectedSource.toUpperCase(),
    requires_key: false,
    is_configured: true,
    status: 'active',
    description: 'Scholarly literature provider.'
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-brand-400" /> Academic Research Paper Search
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real multi-provider academic search (OpenAlex & Crossref without credentials, IEEE Xplore configured).
          </p>
        </div>

        {/* Tab switch */}
        <div className="flex bg-slate-900 border border-slate-800 p-1 rounded-xl self-start sm:self-auto">
          <button
            onClick={() => setActiveTab('search')}
            className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'search' ? 'bg-brand-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Live Search
          </button>
          <button
            onClick={() => setActiveTab('saved')}
            className={`px-4 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
              activeTab === 'saved' ? 'bg-brand-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Project Library ({savedPapers.length})
          </button>
        </div>
      </div>

      {/* SEARCH TAB */}
      {activeTab === 'search' && (
        <div className="space-y-6">
          {/* Query & Filter Form */}
          <form onSubmit={handleSearchSubmit} className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-sm space-y-4">
            {/* Top row: search input + source selector + search type + search button */}
            <div className="flex flex-col lg:flex-row gap-3">
              <div className="flex-1 relative">
                <Search className="w-4 h-4 text-slate-500 absolute left-3 top-3.5" />
                <input
                  type="text"
                  required
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder={
                    searchType === 'doi'
                      ? "Enter DOI (e.g. '10.48550/arXiv.1706.03762')"
                      : searchType === 'author'
                      ? "Enter author name (e.g. 'Vaswani' or 'Bengio')"
                      : searchType === 'title'
                      ? "Enter paper title keywords (e.g. 'Attention is All You Need')"
                      : "Search papers by keyword, methodology, or problem domain..."
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
                  <option value="keyword">All Keywords</option>
                  <option value="title">Paper Title</option>
                  <option value="author">Author Name</option>
                  <option value="doi">DOI Identifier</option>
                </select>

                {/* Provider Selector with status badge */}
                <select
                  value={selectedSource}
                  onChange={(e) => setSelectedSource(e.target.value)}
                  className="px-3 py-2.5 bg-slate-950 border border-slate-700/80 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-brand-500"
                >
                  <option value="openalex">OpenAlex (250M+ Works • Free)</option>
                  <option value="crossref">Crossref (150M+ Records • Free)</option>
                  <option value="ieee">IEEE Xplore (Requires API Key)</option>
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
                  Search Papers
                </button>
              </div>
            </div>

            {/* Provider info pill */}
            <div className="flex flex-wrap items-center justify-between gap-3 text-xs pt-1 border-t border-slate-800/80">
              <div className="flex items-center gap-2 text-slate-400 text-[11px]">
                <span className={`w-2 h-2 rounded-full ${currentSourceObj.status === 'active' ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
                <span className="font-medium text-slate-300">{currentSourceObj.name}:</span>
                <span>{currentSourceObj.description}</span>
              </div>

              {/* Year filters */}
              <div className="flex items-center gap-3">
                <span className="flex items-center gap-1 text-[11px] font-medium text-slate-300">
                  <Filter className="w-3.5 h-3.5 text-brand-400" /> Publication Year:
                </span>
                <input
                  type="number"
                  placeholder="From (e.g. 2018)"
                  value={yearFrom}
                  onChange={(e) => setYearFrom(e.target.value)}
                  className="w-24 px-2 py-1 bg-slate-950 border border-slate-700 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-brand-500"
                />
                <span className="text-slate-600">-</span>
                <input
                  type="number"
                  placeholder="To (e.g. 2026)"
                  value={yearTo}
                  onChange={(e) => setYearTo(e.target.value)}
                  className="w-24 px-2 py-1 bg-slate-950 border border-slate-700 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-brand-500"
                />
                {(yearFrom || yearTo) && (
                  <button
                    type="button"
                    onClick={() => { setYearFrom(''); setYearTo(''); }}
                    className="text-[10px] text-slate-500 hover:text-slate-300"
                  >
                    Clear
                  </button>
                )}
              </div>
            </div>

            {/* Search History Chips */}
            {searchHistory.length > 0 && (
              <div className="flex items-center gap-2 pt-1 flex-wrap text-xs">
                <span className="flex items-center gap-1 text-[10px] font-medium text-slate-500 uppercase tracking-wider">
                  <History className="w-3 h-3" /> Recent:
                </span>
                {searchHistory.map((item, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => {
                      setQuery(item);
                      // Trigger search immediately with selected history query
                      setTimeout(() => {
                        researchService.searchPapers(item, selectedSource, yearFrom ? parseInt(yearFrom) : null, yearTo ? parseInt(yearTo) : null, searchType, 1, limit)
                          .then((data) => {
                            setSearchResults(data.results || []);
                            setTotalCount(data.total_count || null);
                            setPage(1);
                          })
                          .catch((err) => setSearchError(err.response?.data?.detail || "Search failed."));
                      }, 50);
                    }}
                    className="px-2.5 py-0.5 rounded-full bg-slate-800/80 hover:bg-slate-700 text-slate-300 text-[11px] transition-colors"
                  >
                    {item}
                  </button>
                ))}
              </div>
            )}
          </form>

          {/* Error & Retry State */}
          {searchError && (
            <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/20 text-xs text-red-300 flex items-start justify-between gap-3 animate-fade-in">
              <div className="flex items-start gap-2.5">
                <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                <div>
                  <strong className="text-red-200">Search Failed:</strong>
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
            <div className="space-y-4">
              {[1, 2, 3].map((n) => (
                <div key={n} className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 space-y-3 animate-pulse">
                  <div className="h-5 bg-slate-800 rounded w-3/4" />
                  <div className="h-3 bg-slate-800/60 rounded w-1/2" />
                  <div className="h-14 bg-slate-950 rounded-xl" />
                </div>
              ))}
            </div>
          )}

          {/* Empty State */}
          {searchResults.length === 0 && !searching && !searchError && (
            <div className="text-center py-16 bg-slate-900/30 border border-dashed border-slate-800 rounded-2xl">
              <BookOpen className="w-10 h-10 text-slate-600 mx-auto mb-3" />
              <p className="text-sm font-medium text-slate-300">Live Academic Research Paper Search</p>
              <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
                Search verified scholarly publications across OpenAlex and Crossref. Discover real DOIs, verified abstracts, and citation counts without mock data.
              </p>
            </div>
          )}

          {/* Results Summary & Pagination Header */}
          {searchResults.length > 0 && !searching && (
            <div className="flex items-center justify-between text-xs text-slate-400 px-1">
              <div>
                Showing {searchResults.length} results
                {totalCount !== null && ` of ~${totalCount.toLocaleString()} indexed records`}
                <span className="text-slate-500 ml-1.5 font-mono">({selectedSource})</span>
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

          {/* Results List */}
          {!searching && searchResults.length > 0 && (
            <div className="space-y-4">
              {searchResults.map((paper, idx) => {
                const saved = isPaperSaved(paper);
                return (
                  <div
                    key={idx}
                    className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 hover:border-slate-700 transition-all space-y-3 shadow-sm"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="space-y-1 flex-1">
                        <h3 className="text-sm font-bold text-white hover:text-brand-300 transition-colors leading-snug">
                          {paper.title}
                        </h3>

                        <div className="flex flex-wrap items-center gap-2 text-xs text-slate-400 pt-0.5">
                          <span className="flex items-center gap-1 text-slate-300">
                            <User className="w-3.5 h-3.5 text-slate-500" />
                            {paper.authors && paper.authors.length > 0
                              ? paper.authors.slice(0, 3).join(', ') + (paper.authors.length > 3 ? ` +${paper.authors.length - 3} more` : '')
                              : 'Unknown Authors'}
                          </span>
                          <span>•</span>
                          <span className="flex items-center gap-1">
                            <Calendar className="w-3.5 h-3.5 text-slate-500" />
                            {paper.publication_year || 'Recent'}
                          </span>
                          {paper.venue && (
                            <>
                              <span>•</span>
                              <span className="text-slate-400 truncate max-w-xs">{paper.venue}</span>
                            </>
                          )}
                          {paper.citation_count > 0 && (
                            <>
                              <span>•</span>
                              <span className="px-2 py-0.5 rounded-full bg-brand-500/10 border border-brand-500/20 text-brand-400 font-medium text-[10px]">
                                {paper.citation_count.toLocaleString()} citations
                              </span>
                            </>
                          )}
                          {paper.is_open_access && (
                            <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-medium text-[10px] flex items-center gap-1">
                              <ShieldCheck className="w-3 h-3" /> Open Access
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center gap-2 shrink-0">
                        <button
                          onClick={() => setDetailPaper(paper)}
                          className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs font-medium flex items-center gap-1 transition-colors"
                          title="View Full Metadata Details"
                        >
                          <Eye className="w-3.5 h-3.5" /> Details
                        </button>

                        <button
                          onClick={() => handleSavePaper(paper)}
                          disabled={saved}
                          className={`px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-colors ${
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
                              <BookmarkPlus className="w-3.5 h-3.5" /> Save to Project
                            </>
                          )}
                        </button>
                      </div>
                    </div>

                    {/* Abstract Section with explicit unavailability notice */}
                    <div className="bg-slate-950/70 p-3.5 rounded-xl border border-slate-800/80 text-xs">
                      {paper.has_abstract === false || paper.abstract?.includes("Abstract not provided") ? (
                        <div className="flex items-center gap-2 text-slate-500 italic text-[11px]">
                          <Info className="w-3.5 h-3.5 text-slate-600 shrink-0" />
                          Abstract was not provided in this publisher's open index metadata. View the original publisher link for full text.
                        </div>
                      ) : (
                        <p className="text-slate-300 leading-relaxed line-clamp-3 hover:line-clamp-none transition-all">
                          {paper.abstract}
                        </p>
                      )}
                    </div>

                    {/* Bottom Metadata & Links */}
                    <div className="flex items-center justify-between text-xs pt-1 border-t border-slate-800/50">
                      <span className="text-[11px] text-slate-400 font-mono">
                        Source: {paper.source.toUpperCase()} {paper.doi ? `• DOI: ${paper.doi}` : ''}
                      </span>
                      {paper.source_url && (
                        <a
                          href={paper.source_url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-brand-400 hover:underline flex items-center gap-1 text-[11px]"
                        >
                          View Official Publisher Work <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Bottom Pagination Controls */}
          {searchResults.length > 0 && !searching && (
            <div className="flex items-center justify-center gap-3 pt-4">
              <button
                onClick={() => executeSearch(page - 1)}
                disabled={page <= 1 || searching}
                className="px-4 py-2 rounded-xl bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 text-xs font-semibold disabled:opacity-40 flex items-center gap-1.5 transition-colors"
              >
                <ChevronLeft className="w-4 h-4" /> Previous Page
              </button>
              <span className="text-xs text-slate-400 font-mono px-3 py-1 rounded-lg bg-slate-950 border border-slate-800">
                Page {page}
              </span>
              <button
                onClick={() => executeSearch(page + 1)}
                disabled={searching || searchResults.length < limit}
                className="px-4 py-2 rounded-xl bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 text-xs font-semibold disabled:opacity-40 flex items-center gap-1.5 transition-colors"
              >
                Next Page <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      )}

      {/* SAVED LIBRARY TAB */}
      {activeTab === 'saved' && (
        <div className="space-y-4">
          {/* Library Search Bar */}
          {savedPapers.length > 0 && (
            <div className="relative">
              <Search className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
              <input
                type="text"
                value={savedFilterQuery}
                onChange={(e) => setSavedFilterQuery(e.target.value)}
                placeholder="Filter saved papers by title, author, or keyword..."
                className="w-full pl-9 pr-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500"
              />
            </div>
          )}

          {savedPapers.length === 0 ? (
            <div className="text-center py-16 bg-slate-900/40 border border-dashed border-slate-800 rounded-2xl">
              <BookmarkPlus className="w-8 h-8 text-slate-600 mx-auto mb-2" />
              <p className="text-sm font-medium text-slate-300">Your Project Reference Library is Empty</p>
              <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
                Use the Live Search tab to find relevant papers and save them here. Saved papers are securely linked to your project and used in gap analyses and executive reports.
              </p>
            </div>
          ) : (
            filteredSavedPapers.map((paper) => (
              <div key={paper.id} className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="space-y-1">
                    <h3 className="text-sm font-bold text-white">{paper.title}</h3>
                    <p className="text-xs text-slate-400">
                      {paper.authors?.join(', ')} • {paper.publication_year || 'N/A'} • {paper.source?.toUpperCase()}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      onClick={() => handleSummarize(paper.id)}
                      disabled={summarizingId === paper.id}
                      className="px-3 py-1.5 rounded-lg bg-brand-500/10 hover:bg-brand-500/20 text-brand-400 text-xs font-semibold flex items-center gap-1.5 border border-brand-500/20 transition-colors disabled:opacity-50"
                    >
                      {summarizingId === paper.id ? (
                        <span className="w-3.5 h-3.5 border-2 border-brand-400 border-t-transparent rounded-full animate-spin" />
                      ) : (
                        <Sparkles className="w-3.5 h-3.5" />
                      )}
                      AI Abstract Synthesis
                    </button>
                    <button
                      onClick={() => {
                        setEditingPaper(paper);
                        setNoteText(paper.user_notes || '');
                      }}
                      className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs"
                      title="Add or edit personal research notes"
                    >
                      <Edit3 className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => handleDeletePaper(paper.id)}
                      className="p-1.5 rounded-lg bg-slate-800 hover:bg-red-500/20 text-slate-400 hover:text-red-400 text-xs transition-colors"
                      title="Remove paper from project library"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80 text-xs text-slate-300 leading-relaxed">
                  {paper.abstract}
                </div>

                {/* AI Summary View */}
                {paper.ai_summary && (
                  <div className="p-3.5 rounded-xl bg-brand-500/5 border border-brand-500/20 text-xs space-y-1">
                    <div className="flex items-center gap-1.5 text-brand-400 font-semibold text-[11px]">
                      <Sparkles className="w-3.5 h-3.5" /> AI Synthesis of Abstract:
                    </div>
                    <div className="text-slate-200 text-xs whitespace-pre-line leading-relaxed">
                      {paper.ai_summary}
                    </div>
                  </div>
                )}

                {/* Personal Notes */}
                {paper.user_notes && (
                  <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-xs space-y-1">
                    <span className="text-[10px] uppercase font-bold text-slate-400">Personal Project Notes:</span>
                    <p className="text-slate-200">{paper.user_notes}</p>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {/* PAPER DETAIL MODAL */}
      {detailPaper && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl p-6 space-y-4 max-h-[90vh] overflow-y-auto shadow-2xl">
            <div className="flex items-start justify-between gap-3 border-b border-slate-800 pb-3">
              <div>
                <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-brand-500/10 text-brand-400 border border-brand-500/20">
                  {detailPaper.source} scholarly record
                </span>
                <h2 className="text-base font-bold text-white mt-1.5">{detailPaper.title}</h2>
              </div>
              <button
                onClick={() => setDetailPaper(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs text-slate-300">
              <div>
                <strong className="text-slate-400">Authors:</strong>
                <p className="text-white mt-0.5">{detailPaper.authors?.join(', ') || 'Unknown'}</p>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800">
                  <span className="text-[10px] text-slate-500 uppercase block font-semibold">Publication Year</span>
                  <span className="text-white font-medium">{detailPaper.publication_year || 'N/A'}</span>
                </div>
                <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800">
                  <span className="text-[10px] text-slate-500 uppercase block font-semibold">Citations</span>
                  <span className="text-white font-medium">{detailPaper.citation_count?.toLocaleString() || 0}</span>
                </div>
                <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800">
                  <span className="text-[10px] text-slate-500 uppercase block font-semibold">Open Access</span>
                  <span className={detailPaper.is_open_access ? 'text-emerald-400 font-medium' : 'text-slate-400'}>
                    {detailPaper.is_open_access ? 'Yes (Public)' : 'Subscription / Closed'}
                  </span>
                </div>
              </div>

              {detailPaper.venue && (
                <div>
                  <strong className="text-slate-400">Publication Venue:</strong>
                  <p className="text-white mt-0.5">{detailPaper.venue}</p>
                </div>
              )}

              {detailPaper.doi && (
                <div className="flex items-center justify-between bg-slate-950 p-2.5 rounded-xl border border-slate-800">
                  <div>
                    <strong className="text-slate-400 text-[11px]">Digital Object Identifier (DOI):</strong>
                    <p className="text-brand-400 font-mono text-[11px] select-all">{detailPaper.doi}</p>
                  </div>
                  <button
                    onClick={() => handleCopyDoi(detailPaper.doi)}
                    className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs flex items-center gap-1 transition-colors"
                  >
                    {copiedDoi ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    {copiedDoi ? 'Copied' : 'Copy DOI'}
                  </button>
                </div>
              )}

              <div>
                <strong className="text-slate-400">Abstract:</strong>
                <p className="text-slate-200 leading-relaxed bg-slate-950 p-3.5 rounded-xl border border-slate-800 mt-1 max-h-60 overflow-y-auto">
                  {detailPaper.abstract}
                </p>
              </div>
            </div>

            <div className="flex items-center justify-between pt-3 border-t border-slate-800">
              {detailPaper.source_url ? (
                <a
                  href={detailPaper.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-brand-400 hover:underline flex items-center gap-1 text-xs"
                >
                  Open External Publisher Page <ExternalLink className="w-3.5 h-3.5" />
                </a>
              ) : <div />}
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setDetailPaper(null)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
                >
                  Close
                </button>
                {!isPaperSaved(detailPaper) && (
                  <button
                    onClick={() => {
                      handleSavePaper(detailPaper);
                      setDetailPaper(null);
                    }}
                    className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow"
                  >
                    <BookmarkPlus className="w-3.5 h-3.5" /> Save to Project
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Note Edit Modal */}
      {editingPaper && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-6 space-y-4">
            <h3 className="text-sm font-bold text-white">Personal Research Notes</h3>
            <p className="text-xs text-slate-400 line-clamp-1">{editingPaper.title}</p>
            <textarea
              rows={4}
              value={noteText}
              onChange={(e) => setNoteText(e.target.value)}
              placeholder="Record hypotheses, methodology critiques, or relevance to your project..."
              className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500"
            />
            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                onClick={() => setEditingPaper(null)}
                className="px-3 py-1.5 text-xs text-slate-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveNote}
                className="px-4 py-1.5 rounded-lg bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold"
              >
                Save Notes
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
