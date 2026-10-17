import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ideaService } from '../services/ideaService';
import { evaluationService } from '../services/evaluationService';
import { projectService } from '../services/projectService';
import { useProject } from '../contexts/ProjectContext';
import {
  GitCompare,
  Plus,
  Trash2,
  CheckCircle2,
  Sparkles,
  Sliders,
  AlertTriangle,
  Award,
  Layers,
  ChevronDown,
  ChevronUp,
  Info,
  Check,
  Scale,
  RefreshCw,
  Lightbulb,
  ShieldAlert,
  HelpCircle,
  FlaskConical,
  BookOpen,
  ArrowRight,
  TrendingDown,
  TrendingUp,
  SlidersHorizontal
} from 'lucide-react';

const DIMENSION_CONFIG = {
  problem_significance: {
    label: 'Problem Significance',
    type: 'beneficial',
    tip: 'Urgency and economic magnitude of the pain point.'
  },
  target_user_clarity: {
    label: 'Target-User Clarity',
    type: 'beneficial',
    tip: 'Specificity of buyer persona and day-to-day workflow.'
  },
  technical_feasibility: {
    label: 'Technical Feasibility',
    type: 'beneficial',
    tip: 'Achievability using existing technology without fundamental R&D breakthroughs.'
  },
  implementation_complexity: {
    label: 'Implementation Complexity',
    type: 'frictional',
    tip: 'Raw score measures architectural friction (10 = highest complexity). Inverted in scoring so lower complexity yields higher feasibility.'
  },
  estimated_development_cost: {
    label: 'Estimated Development Cost',
    type: 'frictional',
    tip: 'Raw score measures capital requirement (10 = highest cost). Inverted in scoring so lower cost yields higher capital efficiency.'
  },
  adoption_potential: {
    label: 'Adoption & Validation Potential',
    type: 'beneficial',
    tip: 'User willingness to switch, onboarding ease, and distribution momentum.'
  },
  competitive_landscape: {
    label: 'Competitive Differentiation',
    type: 'beneficial',
    tip: 'Defensibility against existing market alternatives and substitutes.'
  },
  novelty: {
    label: 'Novelty & Prior-Work Distance',
    type: 'beneficial',
    tip: 'Degree of divergence from published literature and existing commercial products.'
  },
  security_privacy_ethics: {
    label: 'Security, Privacy & Ethics',
    type: 'beneficial',
    tip: 'Manageability of regulatory compliance (GDPR/HIPAA), attack surfaces, and ethical alignment.'
  },
  evidence_quality: {
    label: 'Evidence Quality & Confidence',
    type: 'beneficial',
    tip: 'Level of factual backing from discovery or citations vs speculative assumption.'
  }
};

export default function IdeaComparison() {
  const { id } = useParams();
  const projectId = parseInt(id);
  const { setActiveProject } = useProject();

  const [project, setProject] = useState(null);
  const [ideas, setIdeas] = useState([]);
  const [evaluations, setEvaluations] = useState([]);
  const [comparison, setComparison] = useState(null);
  const [formulaMeta, setFormulaMeta] = useState(null);
  const [loading, setLoading] = useState(true);
  const [evaluating, setEvaluating] = useState(false);
  const [evalError, setEvalError] = useState('');
  const [showIdeaModal, setShowIdeaModal] = useState(false);
  const [showWeightSliders, setShowWeightSliders] = useState(false);
  const [showMethodology, setShowMethodology] = useState(false);
  const [selectedIdeaIds, setSelectedIdeaIds] = useState([]);
  const [activeTab, setActiveTab] = useState('matrix'); // 'matrix' | 'deepdive'

  // Idea Form State
  const [ideaForm, setIdeaForm] = useState({
    title: '',
    problem_statement: '',
    proposed_solution: '',
    target_audience: '',
    industry: '',
    intended_use_case: '',
    expected_benefits: '',
    constraints: '',
    estimated_budget: '',
    technical_preferences: ''
  });
  const [formError, setFormError] = useState('');

  // Dimension Weights State
  const [weights, setWeights] = useState({
    problem_significance: 1.0,
    target_user_clarity: 1.0,
    technical_feasibility: 1.0,
    implementation_complexity: 1.0,
    estimated_development_cost: 1.0,
    adoption_potential: 1.0,
    competitive_landscape: 1.0,
    novelty: 1.0,
    security_privacy_ethics: 1.0,
    evidence_quality: 1.0
  });

  const fetchData = async () => {
    setEvalError('');
    try {
      const projData = await projectService.getProject(projectId);
      setProject(projData);
      setActiveProject(projData);

      const ideasData = await ideaService.listIdeas(projectId);
      setIdeas(ideasData);
      setSelectedIdeaIds(ideasData.map((i) => i.id));

      const evalData = await evaluationService.getEvaluation(projectId);
      setEvaluations(evalData.evaluations || []);
      setComparison(evalData.comparison || null);
      if (evalData.formula_explanation) {
        setFormulaMeta(evalData.formula_explanation);
      }
      if (evalData.comparison?.configured_weights) {
        setWeights(evalData.comparison.configured_weights);
      }
    } catch (err) {
      console.error("Error loading comparison data:", err);
      setEvalError(err.response?.data?.detail || 'Failed to load project comparison data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [projectId]);

  const handleToggleSelectIdeaForEval = (ideaId) => {
    setSelectedIdeaIds((prev) => {
      if (prev.includes(ideaId)) {
        if (prev.length === 1) return prev; // Keep at least one selected
        return prev.filter((id) => id !== ideaId);
      } else {
        if (prev.length >= 3) {
          alert('You can compare at most 3 candidate ideas at a time.');
          return prev;
        }
        return [...prev, ideaId];
      }
    });
  };

  const handleIdeaSubmit = async (e) => {
    e.preventDefault();
    setFormError('');
    if (ideas.length >= 3) {
      setFormError('A project can contain at most 3 candidate ideas for comparison.');
      return;
    }
    try {
      await ideaService.submitIdea(projectId, ideaForm);
      setShowIdeaModal(false);
      setIdeaForm({
        title: '',
        problem_statement: '',
        proposed_solution: '',
        target_audience: '',
        industry: '',
        intended_use_case: '',
        expected_benefits: '',
        constraints: '',
        estimated_budget: '',
        technical_preferences: ''
      });
      await fetchData();
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Failed to submit idea. Please verify required fields.');
    }
  };

  const handleDeleteIdea = async (ideaId) => {
    if (window.confirm('Delete this candidate idea?')) {
      try {
        await ideaService.deleteIdea(ideaId);
        await fetchData();
      } catch (err) {
        alert('Failed to delete idea.');
      }
    }
  };

  const handleSelectIdea = async (ideaId) => {
    try {
      await ideaService.selectIdea(ideaId);
      await fetchData();
    } catch (err) {
      alert('Failed to set selected idea.');
    }
  };

  const handleRunEvaluation = async () => {
    setEvaluating(true);
    setEvalError('');
    try {
      const payload = {
        idea_ids: selectedIdeaIds.length > 0 ? selectedIdeaIds : undefined,
        weights: weights
      };
      const res = await evaluationService.evaluateProject(projectId, payload);
      setEvaluations(res.evaluations || []);
      setComparison(res.comparison || null);
      if (res.formula_explanation) {
        setFormulaMeta(res.formula_explanation);
      }
    } catch (err) {
      console.error("Evaluation error:", err);
      setEvalError(err.response?.data?.detail || 'Evaluation failed. Please try again or check provider settings.');
    } finally {
      setEvaluating(false);
    }
  };

  const handleWeightChange = async (dim, val) => {
    const updated = { ...weights, [dim]: parseFloat(val) };
    setWeights(updated);
    try {
      const newComp = await evaluationService.recalculateWeights(projectId, updated);
      setComparison(newComp);
    } catch (err) {
      console.error("Failed to re-calculate recommendation:", err);
    }
  };

  const getEvaluationForIdea = (ideaId) => {
    return evaluations.find((e) => e.idea_id === ideaId);
  };

  if (loading) {
    return (
      <div className="py-24 text-center text-slate-400 flex flex-col items-center justify-center gap-3">
        <span className="w-8 h-8 border-3 border-brand-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-sm font-medium">Loading idea evaluation workspace...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
              <GitCompare className="w-5 h-5 text-brand-400" /> Multi-Idea Evaluation & Scoring Engine
            </h1>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
              {ideas.length}/3 ideas
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Project: <span className="text-slate-200 font-medium">{project?.title}</span> • 10-dimension explainable scoring with inverse cost/complexity calibration.
          </p>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          <button
            onClick={() => setShowMethodology(!showMethodology)}
            className="px-3 py-2 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-300 text-xs font-medium flex items-center gap-1.5 border border-slate-700 transition-colors"
          >
            <BookOpen className="w-3.5 h-3.5 text-brand-400" />
            {showMethodology ? 'Hide Methodology' : 'Scoring Formula'}
          </button>

          {ideas.length < 3 && (
            <button
              onClick={() => setShowIdeaModal(true)}
              className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center gap-1.5 border border-slate-700 transition-colors"
            >
              <Plus className="w-4 h-4 text-brand-400" /> Add Candidate Idea
            </button>
          )}

          {ideas.length > 0 && (
            <button
              onClick={handleRunEvaluation}
              disabled={evaluating || selectedIdeaIds.length === 0}
              className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold flex items-center gap-2 shadow-lg shadow-brand-600/20 transition-all disabled:opacity-50"
            >
              {evaluating ? (
                <>
                  <span className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                  <span>Evaluating ({selectedIdeaIds.length} ideas)...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>{evaluations.length > 0 ? `Re-Evaluate (${selectedIdeaIds.length} Selected)` : `Evaluate Ideas (${selectedIdeaIds.length} Selected)`}</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {/* Error Alert with Retry State */}
      {evalError && (
        <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/30 flex items-center justify-between gap-4 text-red-300 text-xs">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-red-400 shrink-0" />
            <div>
              <p className="font-semibold text-red-200">Evaluation Error</p>
              <p className="text-red-300/90 mt-0.5">{evalError}</p>
            </div>
          </div>
          <button
            onClick={handleRunEvaluation}
            disabled={evaluating}
            className="px-3 py-1.5 rounded-lg bg-red-500/20 hover:bg-red-500/30 text-red-200 font-semibold flex items-center gap-1.5 shrink-0 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Retry
          </button>
        </div>
      )}

      {/* Scoring Methodology & Formula Drawer */}
      {showMethodology && (
        <div className="p-5 rounded-2xl bg-slate-900 border border-brand-500/30 shadow-xl space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-brand-400" /> Deterministic Scoring Formula & Inversion Rules
            </h3>
            <span className="text-[11px] font-mono text-brand-300 bg-brand-500/10 px-2 py-0.5 rounded border border-brand-500/20">
              Normalized Range: 0–100
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-slate-300 leading-relaxed pt-2 border-t border-slate-800">
            <div className="space-y-2">
              <p className="font-semibold text-slate-200">Mathematical Definition:</p>
              <pre className="p-3 bg-slate-950 rounded-xl border border-slate-800 font-mono text-[11px] text-brand-300 overflow-x-auto">
                Composite Score = [Sum(w_i * S_eff,i) / Sum(w_i)] * 10
              </pre>
              <p className="text-[11px] text-slate-400">
                Each dimension has an effective rating <code className="text-slate-200">S_eff,i</code> on a 1.0–10.0 scale, multiplied by user priority weight <code className="text-slate-200">w_i</code>.
              </p>
            </div>

            <div className="space-y-2">
              <p className="font-semibold text-amber-300 flex items-center gap-1">
                <AlertTriangle className="w-3.5 h-3.5" /> Complexity & Cost Inversion Rule:
              </p>
              <p className="text-[11px] text-slate-300">
                To prevent high raw complexity or high costs from erroneously increasing an idea's score, <strong>Implementation Complexity</strong> and <strong>Estimated Development Cost</strong> are inverted:
              </p>
              <p className="p-2 bg-slate-950 rounded-lg border border-slate-800 font-mono text-[11px] text-amber-200">
                S_eff,i = 11.0 - Raw_Score (e.g. Raw 2.0 &rarr; Eff 9.0; Raw 9.0 &rarr; Eff 2.0)
              </p>
              <p className="text-[10px] text-slate-400">
                Ratings are diligence estimates designed to guide validation experiments, not guarantees of commercial outcome.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Candidate Ideas Submission Cards Grid */}
      {ideas.length === 0 ? (
        <div className="text-center py-20 bg-slate-900/40 border border-dashed border-slate-800 rounded-3xl">
          <Layers className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-slate-200">No Candidate Ideas Submitted Yet</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto mt-1 mb-6 leading-relaxed">
            Submit up to three candidate ideas for this research project. The platform will compare them across 10 explainable dimensions and identify the best candidate.
          </p>
          <button
            onClick={() => setShowIdeaModal(true)}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-lg shadow-brand-600/20"
          >
            <Plus className="w-4 h-4" /> Submit First Candidate Idea
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Select candidate ideas to include in evaluation:</span>
            <span className="text-[11px] text-slate-400 font-medium">
              {selectedIdeaIds.length} of {ideas.length} selected for comparison
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {ideas.map((idea, idx) => {
              const ev = getEvaluationForIdea(idea.id);
              const isWinner = comparison?.recommended_idea_id === idea.id;
              const isChecked = selectedIdeaIds.includes(idea.id);

              return (
                <div
                  key={idea.id}
                  className={`bg-slate-900/90 border rounded-2xl p-5 flex flex-col justify-between transition-all relative ${
                    isWinner
                      ? 'border-brand-500/80 shadow-lg shadow-brand-500/10'
                      : idea.is_selected
                      ? 'border-emerald-500/60'
                      : 'border-slate-800'
                  }`}
                >
                  {/* Top Bar: Selector & Badges */}
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <label className="flex items-center gap-2 cursor-pointer select-none">
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => handleToggleSelectIdeaForEval(idea.id)}
                        className="w-4 h-4 rounded bg-slate-950 border-slate-700 text-brand-600 focus:ring-brand-500"
                      />
                      <span className="text-[10px] font-bold uppercase tracking-wider text-slate-300 px-2 py-0.5 rounded bg-slate-800 border border-slate-700">
                        Candidate #{idx + 1}
                      </span>
                    </label>

                    <div className="flex items-center gap-1.5">
                      {isWinner && (
                        <span className="text-[10px] font-bold text-amber-300 bg-amber-500/15 border border-amber-500/30 px-2 py-0.5 rounded-full flex items-center gap-1">
                          <Award className="w-3 h-3" /> Top Pick
                        </span>
                      )}
                      {idea.is_selected && (
                        <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/15 border border-emerald-500/30 px-2 py-0.5 rounded-full flex items-center gap-1">
                          <Check className="w-3 h-3" /> Active Plan
                        </span>
                      )}
                      <button
                        onClick={() => handleDeleteIdea(idea.id)}
                        title="Delete candidate idea"
                        className="p-1 rounded text-slate-500 hover:text-red-400 hover:bg-slate-800 transition-colors"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>

                  {/* Idea Details */}
                  <div className="space-y-3">
                    <h3 className="text-base font-bold text-white line-clamp-1">{idea.title}</h3>

                    <div className="space-y-2 text-xs">
                      <div>
                        <span className="text-slate-400 font-medium">Problem Statement:</span>
                        <p className="text-slate-300 text-[11px] line-clamp-2 mt-0.5 leading-relaxed">{idea.problem_statement}</p>
                      </div>
                      <div>
                        <span className="text-slate-400 font-medium">Proposed Solution:</span>
                        <p className="text-slate-300 text-[11px] line-clamp-2 mt-0.5 leading-relaxed">{idea.proposed_solution}</p>
                      </div>
                      <div className="flex items-center gap-2 text-[11px] text-slate-400 pt-1 flex-wrap">
                        <span>Target: <strong className="text-slate-300">{idea.target_audience}</strong></span>
                        <span>•</span>
                        <span>Industry: <strong className="text-slate-300">{idea.industry || 'General'}</strong></span>
                      </div>
                    </div>

                    {/* Evaluation Score Pill */}
                    {ev ? (
                      <div className="mt-4 p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2.5">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-semibold text-slate-300">Composite Score</span>
                          <span className="text-base font-extrabold text-brand-400 font-mono">{ev.overall_score}/100</span>
                        </div>
                        <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                          <div
                            className="bg-gradient-to-r from-brand-600 via-brand-500 to-emerald-400 h-full rounded-full transition-all duration-500"
                            style={{ width: `${ev.overall_score}%` }}
                          />
                        </div>

                        {/* Friction Callout */}
                        <div className="pt-1 flex items-center justify-between text-[10px] text-slate-400 border-t border-slate-900">
                          <span>
                            Complexity: <strong className="text-slate-300">{ev.dimension_scores?.implementation_complexity || 7}/10</strong> (Eff: <span className="text-brand-400 font-semibold">{ev.effective_scores?.implementation_complexity || 4}/10</span>)
                          </span>
                          <span>
                            Cost: <strong className="text-slate-300">{ev.dimension_scores?.estimated_development_cost || 7}/10</strong> (Eff: <span className="text-brand-400 font-semibold">{ev.effective_scores?.estimated_development_cost || 4}/10</span>)
                          </span>
                        </div>

                        {/* Strengths & Risks Highlights */}
                        <div className="space-y-1 text-[11px] pt-1">
                          <p className="text-emerald-400 line-clamp-1 flex items-center gap-1">
                            <span className="font-semibold">+</span> {ev.strengths?.[0] || 'Clear audience'}
                          </p>
                          <p className="text-rose-400 line-clamp-1 flex items-center gap-1">
                            <span className="font-semibold">!</span> {ev.risks?.[0] || 'Adoption hurdles'}
                          </p>
                        </div>
                      </div>
                    ) : (
                      <div className="mt-4 p-3 rounded-xl bg-slate-950/40 border border-dashed border-slate-800 text-center">
                        <p className="text-[11px] text-slate-500">Not yet evaluated in current run.</p>
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="mt-5 pt-3 border-t border-slate-800 flex items-center justify-between">
                    {!idea.is_selected ? (
                      <button
                        onClick={() => handleSelectIdea(idea.id)}
                        className="text-xs text-brand-400 hover:text-brand-300 font-medium flex items-center gap-1 transition-colors"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5" /> Select for Project Roadmap
                      </button>
                    ) : (
                      <span className="text-xs text-emerald-400 font-semibold flex items-center gap-1">
                        <Check className="w-3.5 h-3.5" /> Selected Candidate
                      </span>
                    )}

                    <Link
                      to={`/projects/${projectId}/roadmap`}
                      className="text-xs text-slate-400 hover:text-white flex items-center gap-1 transition-colors"
                    >
                      Roadmap <ArrowRight className="w-3 h-3" />
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Explainable Recommendation & Transparent Rationale Box */}
      {comparison && (
        <div className={`p-6 rounded-2xl border ${
          comparison.is_tie
            ? 'bg-amber-500/5 border-amber-500/30'
            : 'bg-brand-500/5 border-brand-500/30'
        }`}>
          <div className="flex items-start gap-4">
            <div className={`w-12 h-12 rounded-2xl flex items-center justify-center shrink-0 shadow-lg ${
              comparison.is_tie ? 'bg-amber-500/20 text-amber-300' : 'bg-brand-500/20 text-brand-400'
            }`}>
              {comparison.is_tie ? <Scale className="w-6 h-6" /> : <Award className="w-6 h-6" />}
            </div>
            <div className="flex-1 space-y-2">
              <div className="flex items-center gap-3 flex-wrap">
                <h3 className="text-base font-bold text-white">
                  {comparison.is_tie ? 'Decision Dilemma: Statistical Parity / Inconclusive Margin' : 'Recommended Top Candidate'}
                </h3>
                <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full ${
                  comparison.is_tie
                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                    : 'bg-brand-500/20 text-brand-400 border border-brand-500/30'
                }`}>
                  {comparison.is_tie ? 'Margin < 2.0 pts or Evidence Unverified' : 'Deterministic Recommendation'}
                </span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">
                {comparison.recommendation_rationale}
              </p>

              {/* Trade-off Contrast Bullets */}
              {comparison.tradeoff_analysis && (comparison.tradeoff_analysis.top_advantages || comparison.tradeoff_analysis.runner_up_advantages) && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-3 border-t border-slate-800 text-xs">
                  {comparison.tradeoff_analysis.top_advantages && comparison.tradeoff_analysis.top_advantages.length > 0 && (
                    <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800">
                      <span className="font-semibold text-emerald-400 block mb-1">Top Candidate Strengths:</span>
                      <ul className="list-disc list-inside text-slate-300 text-[11px] space-y-0.5">
                        {comparison.tradeoff_analysis.top_advantages.map((adv, idx) => (
                          <li key={idx}>{adv}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {comparison.tradeoff_analysis.runner_up_advantages && comparison.tradeoff_analysis.runner_up_advantages.length > 0 && (
                    <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800">
                      <span className="font-semibold text-blue-400 block mb-1">Runner-up Counter-Advantages:</span>
                      <ul className="list-disc list-inside text-slate-300 text-[11px] space-y-0.5">
                        {comparison.tradeoff_analysis.runner_up_advantages.map((adv, idx) => (
                          <li key={idx}>{adv}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Configurable Evaluation Priority Sliders */}
      {evaluations.length > 0 && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Sliders className="w-4 h-4 text-brand-400" /> Configurable Dimension Priorities
              </h3>
              <p className="text-xs text-slate-400">
                Adjust criteria weights based on project stage (e.g., Feasibility for rapid Hackathons vs Novelty for Research Papers).
              </p>
            </div>
            <button
              onClick={() => setShowWeightSliders(!showWeightSliders)}
              className="text-xs text-brand-400 hover:text-brand-300 flex items-center gap-1 font-medium"
            >
              {showWeightSliders ? 'Hide Sliders' : 'Customize Weights'}
              {showWeightSliders ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
          </div>

          {showWeightSliders && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 pt-4 border-t border-slate-800">
              {Object.keys(DIMENSION_CONFIG).map((dimKey) => {
                const conf = DIMENSION_CONFIG[dimKey];
                return (
                  <div key={dimKey} className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80 space-y-1.5">
                    <div className="flex items-center justify-between">
                      <label className="text-[11px] font-medium text-slate-300 truncate" title={conf.tip}>
                        {conf.label}
                      </label>
                      <span className="text-[11px] font-bold text-brand-400">{weights[dimKey] || 1.0}x</span>
                    </div>
                    <input
                      type="range"
                      min="0.2"
                      max="3.0"
                      step="0.2"
                      value={weights[dimKey] || 1.0}
                      onChange={(e) => handleWeightChange(dimKey, e.target.value)}
                      className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-brand-500"
                    />
                    <span className="text-[9px] text-slate-500 block truncate">{conf.type === 'frictional' ? '(Inverted cost/complexity)' : '(Higher is better)'}</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Tab Switcher: 10-Dimension Matrix vs Deep-Dive Qualitative Breakdown */}
      {evaluations.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setActiveTab('matrix')}
                className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
                  activeTab === 'matrix'
                    ? 'bg-brand-600 text-white shadow-md shadow-brand-600/20'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                10-Dimension Score Matrix
              </button>
              <button
                onClick={() => setActiveTab('deepdive')}
                className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
                  activeTab === 'deepdive'
                    ? 'bg-brand-600 text-white shadow-md shadow-brand-600/20'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Side-by-Side Deep Dive (Assumptions & Risks)
              </button>
            </div>
          </div>

          {/* View 1: 10-Dimension Matrix */}
          {activeTab === 'matrix' && (
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                    <tr>
                      <th className="p-4 font-semibold">Evaluation Dimension</th>
                      <th className="p-4 font-semibold text-center">Priority Weight</th>
                      {ideas.map((i) => (
                        <th key={i.id} className="p-4 font-semibold text-center text-slate-200">
                          {i.title}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/70">
                    {Object.keys(DIMENSION_CONFIG).map((dimKey) => {
                      const conf = DIMENSION_CONFIG[dimKey];
                      return (
                        <tr key={dimKey} className="hover:bg-slate-800/30 transition-colors">
                          <td className="p-4 font-medium text-slate-200">
                            <div className="flex items-center gap-2">
                              <span>{conf.label}</span>
                              {conf.type === 'frictional' && (
                                <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20" title={conf.tip}>
                                  Inverted
                                </span>
                              )}
                            </div>
                            <span className="text-[10px] text-slate-400 block mt-0.5">{conf.tip}</span>
                          </td>
                          <td className="p-4 text-center text-brand-400 font-mono text-xs">
                            {weights[dimKey] || 1.0}x
                          </td>
                          {ideas.map((i) => {
                            const ev = getEvaluationForIdea(i.id);
                            const raw = ev?.dimension_scores?.[dimKey] || 0;
                            const eff = ev?.effective_scores?.[dimKey] || raw;

                            return (
                              <td key={i.id} className="p-4 text-center">
                                <div className="inline-flex flex-col items-center">
                                  <span className={`px-2.5 py-1 rounded-lg text-xs font-bold font-mono ${
                                    eff >= 8.0 ? 'bg-emerald-500/15 text-emerald-400' :
                                    eff >= 6.0 ? 'bg-blue-500/15 text-blue-400' :
                                    'bg-amber-500/15 text-amber-400'
                                  }`}>
                                    {eff.toFixed(1)}/10
                                  </span>
                                  {conf.type === 'frictional' && (
                                    <span className="text-[9px] text-slate-500 mt-0.5">
                                      Raw: {raw.toFixed(1)}
                                    </span>
                                  )}
                                </div>
                              </td>
                            );
                          })}
                        </tr>
                      );
                    })}
                    {/* Overall Row */}
                    <tr className="bg-slate-950 font-bold border-t-2 border-slate-700">
                      <td className="p-4 text-white text-sm">Overall Normalized Composite Score</td>
                      <td className="p-4 text-center text-slate-400 text-xs">0–100 Scale</td>
                      {ideas.map((i) => {
                        const ev = getEvaluationForIdea(i.id);
                        return (
                          <td key={i.id} className="p-4 text-center text-base font-extrabold text-brand-400 font-mono">
                            {ev?.overall_score || 0}/100
                          </td>
                        );
                      })}
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* View 2: Side-by-Side Deep Dive */}
          {activeTab === 'deepdive' && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {ideas.map((i) => {
                const ev = getEvaluationForIdea(i.id);
                if (!ev) return null;

                return (
                  <div key={i.id} className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 space-y-5">
                    <div>
                      <h4 className="text-sm font-bold text-white line-clamp-1">{i.title}</h4>
                      <p className="text-[11px] text-slate-400 mt-0.5">Composite Score: <strong className="text-brand-400 font-mono">{ev.overall_score}/100</strong></p>
                    </div>

                    {/* Strengths */}
                    <div className="space-y-1.5">
                      <h5 className="text-xs font-semibold text-emerald-400 flex items-center gap-1.5">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Strengths
                      </h5>
                      <ul className="text-[11px] text-slate-300 space-y-1 list-disc list-inside">
                        {ev.strengths?.map((s, idx) => (
                          <li key={idx} className="leading-relaxed">{s}</li>
                        ))}
                      </ul>
                    </div>

                    {/* Weaknesses */}
                    <div className="space-y-1.5">
                      <h5 className="text-xs font-semibold text-amber-400 flex items-center gap-1.5">
                        <AlertTriangle className="w-3.5 h-3.5" /> Weaknesses
                      </h5>
                      <ul className="text-[11px] text-slate-300 space-y-1 list-disc list-inside">
                        {ev.weaknesses?.map((w, idx) => (
                          <li key={idx} className="leading-relaxed">{w}</li>
                        ))}
                      </ul>
                    </div>

                    {/* Key Risks */}
                    <div className="space-y-1.5">
                      <h5 className="text-xs font-semibold text-rose-400 flex items-center gap-1.5">
                        <ShieldAlert className="w-3.5 h-3.5" /> Key Risks & Failure Modes
                      </h5>
                      <ul className="text-[11px] text-slate-300 space-y-1 list-disc list-inside">
                        {ev.risks?.map((r, idx) => (
                          <li key={idx} className="leading-relaxed">{r}</li>
                        ))}
                      </ul>
                    </div>

                    {/* Assumptions (Unverified Hypotheses) */}
                    <div className="space-y-1.5">
                      <h5 className="text-xs font-semibold text-purple-400 flex items-center gap-1.5">
                        <Lightbulb className="w-3.5 h-3.5" /> Key Assumptions (Unverified)
                      </h5>
                      <ul className="text-[11px] text-slate-300 space-y-1 list-disc list-inside">
                        {(ev.assumptions && ev.assumptions.length > 0) ? (
                          ev.assumptions.map((a, idx) => (
                            <li key={idx} className="leading-relaxed">{a}</li>
                          ))
                        ) : (
                          <li className="text-slate-500 italic">No explicit unverified assumptions recorded.</li>
                        )}
                      </ul>
                    </div>

                    {/* Missing Information */}
                    <div className="space-y-1.5">
                      <h5 className="text-xs font-semibold text-sky-400 flex items-center gap-1.5">
                        <HelpCircle className="w-3.5 h-3.5" /> Missing Evidence & Gaps
                      </h5>
                      <ul className="text-[11px] text-slate-300 space-y-1 list-disc list-inside">
                        {ev.missing_information?.map((m, idx) => (
                          <li key={idx} className="leading-relaxed">{m}</li>
                        ))}
                      </ul>
                    </div>

                    {/* Recommended Experiments */}
                    <div className="space-y-1.5 pt-2 border-t border-slate-800">
                      <h5 className="text-xs font-semibold text-emerald-300 flex items-center gap-1.5">
                        <FlaskConical className="w-3.5 h-3.5" /> Recommended Validation Experiments
                      </h5>
                      <ul className="text-[11px] text-slate-300 space-y-1 list-decimal list-inside">
                        {ev.recommended_experiments?.map((exp, idx) => (
                          <li key={idx} className="leading-relaxed">{exp}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Idea Submission Modal */}
      {showIdeaModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm overflow-y-auto">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl p-6 shadow-2xl my-8">
            <h2 className="text-lg font-bold text-white mb-1">Add Candidate Idea</h2>
            <p className="text-xs text-slate-400 mb-4">
              Enter the core parameters for this candidate idea ({ideas.length}/3 ideas created).
            </p>

            {formError && (
              <div className="mb-4 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span>{formError}</span>
              </div>
            )}

            <form onSubmit={handleIdeaSubmit} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Idea Title *</label>
                  <input
                    type="text"
                    required
                    value={ideaForm.title}
                    onChange={(e) => setIdeaForm({ ...ideaForm, title: e.target.value })}
                    placeholder="e.g., LoRa Smoke Sensor Mesh"
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Target Audience *</label>
                  <input
                    type="text"
                    required
                    value={ideaForm.target_audience}
                    onChange={(e) => setIdeaForm({ ...ideaForm, target_audience: e.target.value })}
                    placeholder="e.g., Forestry departments, emergency personnel"
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Problem Statement *</label>
                <textarea
                  rows={2}
                  required
                  value={ideaForm.problem_statement}
                  onChange={(e) => setIdeaForm({ ...ideaForm, problem_statement: e.target.value })}
                  placeholder="What is the critical pain point, urgency, and current inefficiency?"
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Proposed Solution *</label>
                <textarea
                  rows={2}
                  required
                  value={ideaForm.proposed_solution}
                  onChange={(e) => setIdeaForm({ ...ideaForm, proposed_solution: e.target.value })}
                  placeholder="How does your technical solution address the problem uniquely?"
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Industry / Domain</label>
                  <input
                    type="text"
                    value={ideaForm.industry}
                    onChange={(e) => setIdeaForm({ ...ideaForm, industry: e.target.value })}
                    placeholder="e.g., ClimateTech, Healthcare (optional)"
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Intended Use Case</label>
                  <input
                    type="text"
                    value={ideaForm.intended_use_case}
                    onChange={(e) => setIdeaForm({ ...ideaForm, intended_use_case: e.target.value })}
                    placeholder="e.g., Continuous perimeter monitoring (optional)"
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowIdeaModal(false)}
                  className="px-4 py-2 rounded-xl text-slate-400 hover:text-white text-xs font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-md"
                >
                  Submit Candidate Idea
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
