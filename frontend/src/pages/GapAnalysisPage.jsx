import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { gapService } from '../services/gapService';
import { ideaService } from '../services/ideaService';
import { projectService } from '../services/projectService';
import { useProject } from '../contexts/ProjectContext';
import {
  Split,
  Sparkles,
  ExternalLink,
  BookOpen,
  HelpCircle,
  FlaskConical,
  AlertCircle,
  Layers,
  ArrowRight
} from 'lucide-react';

export default function GapAnalysisPage() {
  const { id } = useParams();
  const projectId = parseInt(id);
  const { setActiveProject } = useProject();

  const [ideas, setIdeas] = useState([]);
  const [selectedIdeaId, setSelectedIdeaId] = useState(null);
  const [gapAnalysis, setGapAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  const fetchData = async () => {
    try {
      const proj = await projectService.getProject(projectId);
      setActiveProject(proj);

      const ideasList = await ideaService.listIdeas(projectId);
      setIdeas(ideasList);

      const active = ideasList.find((i) => i.is_selected) || ideasList[0];
      if (active) setSelectedIdeaId(active.id);

      const analyses = await gapService.getGapAnalyses(projectId);
      if (analyses.length > 0) {
        setGapAnalysis(analyses[0]);
      }
    } catch (err) {
      console.error("Error loading gap analysis:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [projectId]);

  const handleGenerate = async () => {
    if (!selectedIdeaId) return;
    setGenerating(true);
    try {
      const res = await gapService.generateGapAnalysis(projectId, selectedIdeaId);
      setGapAnalysis(res);
    } catch (err) {
      alert("Failed to generate research gap analysis.");
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="py-20 text-center text-slate-400 flex items-center justify-center gap-2">
        <span className="w-5 h-5 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
        Loading literature analysis...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <Split className="w-5 h-5 text-brand-400" /> Literature & Research Gap Analysis
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Synthesize existing academic findings, author limitations, and potential unexplored research questions.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {ideas.length > 0 && (
            <select
              value={selectedIdeaId || ''}
              onChange={(e) => setSelectedIdeaId(parseInt(e.target.value))}
              className="px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-brand-500"
            >
              {ideas.map((i) => (
                <option key={i.id} value={i.id}>
                  Idea: {i.title}
                </option>
              ))}
            </select>
          )}

          <button
            onClick={handleGenerate}
            disabled={generating || !selectedIdeaId}
            className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold flex items-center gap-2 shadow-lg shadow-brand-600/20 transition-all disabled:opacity-50 shrink-0"
          >
            {generating ? (
              <span className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
            ) : (
              <Sparkles className="w-4 h-4" />
            )}
            {gapAnalysis ? 'Regenerate Gap Report' : 'Synthesize Research Gaps'}
          </button>
        </div>
      </div>

      {/* Epistemic disclaimer notice */}
      <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-400 leading-relaxed">
        <strong className="text-slate-300">Methodological Note:</strong> Identified research gaps represent promising hypotheses for investigation based on available scholarly indexes, not definitive proof that no prior study has ever explored the concept.
      </div>

      {!gapAnalysis ? (
        <div className="text-center py-16 bg-slate-900/40 border border-dashed border-slate-800 rounded-2xl">
          <BookOpen className="w-8 h-8 text-slate-600 mx-auto mb-2" />
          <p className="text-sm font-medium text-slate-300">No Research Gap Report Generated</p>
          <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto mb-4">
            Click 'Synthesize Research Gaps' to scan saved literature, map author limitations, and generate investigation questions.
          </p>
          <button
            onClick={handleGenerate}
            disabled={!selectedIdeaId}
            className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-md"
          >
            Generate Gap Report
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Section Grid: Existing Approaches & Common Findings */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Layers className="w-4 h-4 text-blue-400" /> Existing Approaches in Prior Work
              </h3>
              <ul className="space-y-2 text-xs text-slate-300">
                {gapAnalysis.existing_approaches?.map((item, idx) => (
                  <li key={idx} className="flex items-start gap-2 bg-slate-950/50 p-2.5 rounded-xl border border-slate-800/80">
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-400 mt-1.5 shrink-0" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-emerald-400" /> Common Empirical Findings
              </h3>
              <ul className="space-y-2 text-xs text-slate-300">
                {gapAnalysis.common_findings?.map((item, idx) => (
                  <li key={idx} className="flex items-start gap-2 bg-slate-950/50 p-2.5 rounded-xl border border-slate-800/80">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 shrink-0" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Conflicting Findings & Limitations in Literature */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-amber-400" /> Conflicting or Contested Findings
              </h3>
              <ul className="space-y-2 text-xs text-slate-300">
                {gapAnalysis.conflicting_findings?.map((item, idx) => (
                  <li key={idx} className="flex items-start gap-2 bg-slate-950/50 p-2.5 rounded-xl border border-slate-800/80">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 shrink-0" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-rose-400" /> Limitations Reported by Authors
              </h3>
              <ul className="space-y-2 text-xs text-slate-300">
                {gapAnalysis.limitations_in_prior_work?.map((item, idx) => (
                  <li key={idx} className="flex items-start gap-2 bg-slate-950/50 p-2.5 rounded-xl border border-slate-800/80">
                    <span className="w-1.5 h-1.5 rounded-full bg-rose-400 mt-1.5 shrink-0" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Identified Research Gaps (Highlighted) */}
          <div className="bg-gradient-to-br from-slate-900 to-navy-900 border border-brand-500/30 rounded-2xl p-6 space-y-3 shadow-lg">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Split className="w-5 h-5 text-brand-400" /> Key Identified Research Gaps
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {gapAnalysis.identified_gaps?.map((gap, idx) => (
                <div key={idx} className="p-3.5 rounded-xl bg-slate-950/70 border border-brand-500/20 text-xs text-slate-200 leading-relaxed flex items-start gap-2.5">
                  <span className="text-brand-400 font-bold font-mono">0{idx + 1}.</span>
                  <span>{gap}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Suggested Research Questions & Proposed Evaluation Methods */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <HelpCircle className="w-4 h-4 text-purple-400" /> Suggested Research Questions
              </h3>
              <ul className="space-y-2 text-xs text-slate-300">
                {gapAnalysis.suggested_research_questions?.map((item, idx) => (
                  <li key={idx} className="p-3 rounded-xl bg-slate-950/50 border border-slate-800/80 leading-relaxed font-medium text-slate-200">
                    "{item}"
                  </li>
                ))}
              </ul>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <FlaskConical className="w-4 h-4 text-cyan-400" /> Proposed Evaluation Experiments
              </h3>
              <ul className="space-y-2 text-xs text-slate-300">
                {gapAnalysis.proposed_evaluation_methods?.map((item, idx) => (
                  <li key={idx} className="p-3 rounded-xl bg-slate-950/50 border border-slate-800/80 leading-relaxed text-slate-300">
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Verified Supporting Citations */}
          {gapAnalysis.citations?.length > 0 && (
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-brand-400" /> Supporting Scholarly & Patent Citations
              </h3>
              <div className="divide-y divide-slate-800 text-xs">
                {gapAnalysis.citations.map((cite, idx) => (
                  <div key={idx} className="py-2.5 flex items-center justify-between gap-4">
                    <div>
                      <span className="font-semibold text-slate-200">{cite.title}</span>
                      <p className="text-[11px] text-slate-400 mt-0.5">{cite.relevance_note} • ID: {cite.external_id}</p>
                    </div>
                    {cite.source_url && (
                      <a
                        href={cite.source_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-brand-400 hover:underline flex items-center gap-1 text-[11px] shrink-0"
                      >
                        Source <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
