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
  FileText,
  User,
  Calendar,
  Quote
} from 'lucide-react';

export default function ResearchWorkspace() {
  const { id } = useParams();
  const projectId = parseInt(id);
  const { setActiveProject } = useProject();

  const [activeTab, setActiveTab] = useState('search'); // 'search' or 'saved'
  const [query, setQuery] = useState('');
  const [source, setSource] = useState('openalex'); // 'openalex' or 'crossref'
  const [yearFrom, setYearFrom] = useState('');
  const [yearTo, setYearTo] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [savedPapers, setSavedPapers] = useState([]);
  const [searching, setSearching] = useState(false);
  const [summarizingId, setSummarizingId] = useState(null);
  const [editingPaper, setEditingPaper] = useState(null);
  const [noteText, setNoteText] = useState('');

  const fetchSaved = async () => {
    try {
      const proj = await projectService.getProject(projectId);
      setActiveProject(proj);
      const list = await researchService.getSavedPapers(projectId);
      setSavedPapers(list);
    } catch (err) {
      console.error("Error loading saved papers:", err);
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
      const data = await researchService.searchPapers(
        query,
        source,
        yearFrom ? parseInt(yearFrom) : null,
        yearTo ? parseInt(yearTo) : null,
        15
      );
      setSearchResults(data.results || []);
    } catch (err) {
      alert("Scholarly search encountered an error. Check network connection.");
    } finally {
      setSearching(false);
    }
  };

  const handleSavePaper = async (paper) => {
    try {
      await researchService.savePaper(projectId, {
        external_id: paper.external_id,
        source: paper.source,
        title: paper.title,
        authors: paper.authors,
        publication_year: paper.publication_year,
        publication_date: paper.publication_date,
        abstract: paper.abstract,
        doi: paper.doi,
        source_url: paper.source_url,
        citation_count: paper.citation_count || 0
      });
      await fetchSaved();
      alert("Paper saved to project reference library!");
    } catch (err) {
      alert("Failed to save paper.");
    }
  };

  const handleDeletePaper = async (paperId) => {
    if (window.confirm("Remove this paper from library?")) {
      try {
        await researchService.deletePaper(paperId);
        await fetchSaved();
      } catch (err) {
        alert("Failed to delete paper.");
      }
    }
  };

  const handleSummarize = async (paperId) => {
    setSummarizingId(paperId);
    try {
      await researchService.summarizePaper(paperId);
      await fetchSaved();
    } catch (err) {
      alert("Failed to generate summary.");
    } finally {
      setSummarizingId(null);
    }
  };

  const handleSaveNote = async () => {
    if (!editingPaper) return;
    try {
      await researchService.updatePaper(editingPaper.id, { user_notes: noteText });
      setEditingPaper(null);
      await fetchSaved();
    } catch (err) {
      alert("Failed to update notes.");
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-brand-400" /> Academic Research Workspace
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Search live scholarly literature via OpenAlex & Crossref with DOI links and verified abstracts.
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
            Saved Library ({savedPapers.length})
          </button>
        </div>
      </div>

      {/* SEARCH TAB */}
      {activeTab === 'search' && (
        <div className="space-y-6">
          {/* Query Bar */}
          <form onSubmit={handleSearch} className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-sm space-y-3">
            <div className="flex flex-col md:flex-row gap-3">
              <div className="flex-1 relative">
                <Search className="w-4 h-4 text-slate-500 absolute left-3 top-3.5" />
                <input
                  type="text"
                  required
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search papers by keyword, methodology, or title (e.g., 'attention mechanisms transformers')"
                  className="w-full pl-9 pr-3 py-2.5 bg-slate-950 border border-slate-700/80 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500"
                />
              </div>

              <div className="flex items-center gap-2">
                <select
                  value={source}
                  onChange={(e) => setSource(e.target.value)}
                  className="px-3 py-2.5 bg-slate-950 border border-slate-700/80 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-brand-500"
                >
                  <option value="openalex">OpenAlex API (Open Scholarly Works)</option>
                  <option value="crossref">Crossref Works API</option>
                </select>

                <button
                  type="submit"
                  disabled={searching}
                  className="px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold flex items-center gap-2 shadow-md disabled:opacity-50"
                >
                  {searching ? (
                    <span className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                  ) : (
                    <Search className="w-4 h-4" />
                  )}
                  Search
                </button>
              </div>
            </div>

            {/* Filters Row */}
            <div className="flex flex-wrap items-center gap-3 pt-2 border-t border-slate-800 text-xs text-slate-400">
              <span className="flex items-center gap-1 text-[11px] font-medium text-slate-300">
                <Filter className="w-3.5 h-3.5 text-brand-400" /> Filters:
              </span>
              <div className="flex items-center gap-1.5">
                <span className="text-[11px]">From Year:</span>
                <input
                  type="number"
                  placeholder="2018"
                  value={yearFrom}
                  onChange={(e) => setYearFrom(e.target.value)}
                  className="w-20 px-2 py-1 bg-slate-950 border border-slate-700 rounded-lg text-xs text-slate-200 focus:outline-none"
                />
              </div>
              <div className="flex items-center gap-1.5">
                <span className="text-[11px]">To Year:</span>
                <input
                  type="number"
                  placeholder="2026"
                  value={yearTo}
                  onChange={(e) => setYearTo(e.target.value)}
                  className="w-20 px-2 py-1 bg-slate-950 border border-slate-700 rounded-lg text-xs text-slate-200 focus:outline-none"
                />
              </div>
            </div>
          </form>

          {/* Results List */}
          {searchResults.length === 0 && !searching && (
            <div className="text-center py-12 bg-slate-900/30 border border-dashed border-slate-800 rounded-2xl">
              <BookOpen className="w-8 h-8 text-slate-600 mx-auto mb-2" />
              <p className="text-xs text-slate-400">Search scholarly papers using real official APIs above.</p>
              <p className="text-[11px] text-slate-500 mt-1">Verified titles, abstracts, DOIs, and citations are returned directly from scholarly indexers.</p>
            </div>
          )}

          <div className="space-y-4">
            {searchResults.map((paper, idx) => (
              <div key={idx} className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 hover:border-slate-700 transition-all space-y-3">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h3 className="text-sm font-bold text-white hover:text-brand-400 transition-colors">
                      {paper.title}
                    </h3>
                    <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400 mt-1">
                      <span className="flex items-center gap-1">
                        <User className="w-3.5 h-3.5 text-slate-500" />
                        {paper.authors?.length > 0 ? paper.authors.join(', ') : 'Unknown Authors'}
                      </span>
                      <span>•</span>
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3.5 h-3.5 text-slate-500" />
                        {paper.publication_year || 'Recent'}
                      </span>
                      {paper.citation_count > 0 && (
                        <>
                          <span>•</span>
                          <span className="text-brand-400 font-medium">
                            {paper.citation_count} citations
                          </span>
                        </>
                      )}
                    </div>
                  </div>

                  <button
                    onClick={() => handleSavePaper(paper)}
                    className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-brand-600 text-slate-200 hover:text-white text-xs font-medium flex items-center gap-1.5 transition-colors shrink-0"
                  >
                    <BookmarkPlus className="w-3.5 h-3.5 text-brand-400 hover:text-white" /> Save to Project
                  </button>
                </div>

                <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
                  {paper.abstract}
                </p>

                <div className="flex items-center justify-between text-xs pt-1">
                  <span className="text-[11px] text-slate-400 uppercase font-mono tracking-wider">
                    Source: {paper.source} {paper.doi ? `• DOI: ${paper.doi}` : ''}
                  </span>
                  {paper.source_url && (
                    <a
                      href={paper.source_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-brand-400 hover:underline flex items-center gap-1 text-[11px]"
                    >
                      View Original Publisher Record <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* SAVED LIBRARY TAB */}
      {activeTab === 'saved' && (
        <div className="space-y-4">
          {savedPapers.length === 0 ? (
            <div className="text-center py-16 bg-slate-900/40 border border-dashed border-slate-800 rounded-2xl">
              <BookmarkPlus className="w-8 h-8 text-slate-600 mx-auto mb-2" />
              <p className="text-sm font-medium text-slate-300">Your Reference Library is Empty</p>
              <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
                Use the Live Search tab to find relevant papers and save them here. Saved papers are automatically linked into Research Gap Analyses and reports.
              </p>
            </div>
          ) : (
            savedPapers.map((paper) => (
              <div key={paper.id} className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h3 className="text-sm font-bold text-white">{paper.title}</h3>
                    <p className="text-xs text-slate-400 mt-0.5">
                      {paper.authors?.join(', ')} • {paper.publication_year || 'N/A'} • {paper.source}
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
                      Generate AI Summary
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
                      className="p-1.5 rounded-lg bg-slate-800 hover:bg-red-500/20 text-slate-400 hover:text-red-400 text-xs"
                      title="Remove paper"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
                  {paper.abstract}
                </p>

                {/* AI Summary View */}
                {paper.ai_summary && (
                  <div className="p-3.5 rounded-xl bg-brand-500/5 border border-brand-500/20 text-xs space-y-1">
                    <div className="flex items-center gap-1.5 text-brand-400 font-semibold text-[11px]">
                      <Sparkles className="w-3.5 h-3.5" /> AI Synthesis of Abstract
                    </div>
                    <div className="text-slate-200 text-xs whitespace-pre-line leading-relaxed">
                      {paper.ai_summary}
                    </div>
                  </div>
                )}

                {/* Personal Notes */}
                {paper.user_notes && (
                  <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-xs space-y-1">
                    <span className="text-[10px] uppercase font-bold text-slate-400">Your Research Notes:</span>
                    <p className="text-slate-200">{paper.user_notes}</p>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {/* Note Edit Modal */}
      {editingPaper && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-6 space-y-4">
            <h3 className="text-sm font-bold text-white">Personal Notes on Paper</h3>
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
