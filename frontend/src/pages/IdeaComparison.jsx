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
  Scale
} from 'lucide-react';

const DIMENSION_LABELS = {
  problem_significance: 'Problem Significance',
  target_user_clarity: 'Target-User Clarity',
  technical_feasibility: 'Technical Feasibility',
  implementation_complexity: 'Implementation Simplicity',
  estimated_development_cost: 'Capital Efficiency',
  adoption_potential: 'Adoption Potential',
  competitive_landscape: 'Competitive Differentiation',
  novelty: 'Novelty & Prior Work Distance',
  security_privacy_ethics: 'Security, Privacy & Ethics',
  evidence_quality: 'Evidence Quality & Confidence'
};

export default function IdeaComparison() {
  const { id } = useParams();
  const projectId = parseInt(id);
  const { setActiveProject } = useProject();

  const [project, setProject] = useState(null);
  const [ideas, setIdeas] = useState([]);
  const [evaluations, setEvaluations] = useState([]);
  const [comparison, setComparison] = useState(null);
  const [loading, setLoading] = useState(true);
  const [evaluating, setEvaluating] = useState(false);
  const [showIdeaModal, setShowIdeaModal] = useState(false);
  const [showWeightSliders, setShowWeightSliders] = useState(false);

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
    try {
      const projData = await projectService.getProject(projectId);
      setProject(projData);
      setActiveProject(projData);

      const ideasData = await ideaService.listIdeas(projectId);
      setIdeas(ideasData);

      const evalData = await evaluationService.getEvaluation(projectId);
      setEvaluations(evalData.evaluations || []);
      setComparison(evalData.comparison || null);
      if (evalData.comparison?.configured_weights) {
        setWeights(evalData.comparison.configured_weights);
      }
    } catch (err) {
      console.error("Error loading comparison data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [projectId]);

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
      setFormError(err.response?.data?.detail || 'Failed to submit idea. Please verify fields.');
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
    try {
      const res = await evaluationService.evaluateProject(projectId);
      setEvaluations(res.evaluations || []);
      setComparison(res.comparison || null);
    } catch (err) {
      alert(err.response?.data?.detail || 'Evaluation failed.');
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
      <div className="py-20 text-center text-slate-400 flex items-center justify-center gap-2">
        <span className="w-5 h-5 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
        Loading idea workspace...
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
              <GitCompare className="w-5 h-5 text-brand-400" /> Multi-Idea Comparison & Dilemma Solver
            </h1>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
              {ideas.length}/3 ideas
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Project: <span className="text-slate-200 font-medium">{project?.title}</span> • Submit up to 3 candidate ideas for side-by-side 10-dimension evaluation.
          </p>
        </div>

        <div className="flex items-center gap-3">
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
              disabled={evaluating}
              className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold flex items-center gap-2 shadow-lg shadow-brand-600/20 transition-all disabled:opacity-50"
            >
              {evaluating ? (
                <span className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
              ) : (
                <Sparkles className="w-4 h-4" />
              )}
              {evaluations.length > 0 ? 'Re-Evaluate Ideas' : 'Evaluate Ideas (10 Dimensions)'}
            </button>
          )}
        </div>
      </div>

      {/* Candidate Ideas Submission Cards Grid */}
      {ideas.length === 0 ? (
        <div className="text-center py-16 bg-slate-900/40 border border-dashed border-slate-800 rounded-2xl">
          <Layers className="w-10 h-10 text-slate-600 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-slate-200">No Ideas Submitted Yet</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto mt-1 mb-5">
            Submit your first idea candidate below. You can compare up to three alternatives side-by-side.
          </p>
          <button
            onClick={() => setShowIdeaModal(true)}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-md"
          >
            <Plus className="w-4 h-4" /> Submit First Idea
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {ideas.map((idea, idx) => {
            const ev = getEvaluationForIdea(idea.id);
            const isWinner = comparison?.recommended_idea_id === idea.id;

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
                {/* Badges */}
                <div className="flex items-center justify-between gap-2 mb-3">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 px-2 py-0.5 rounded bg-slate-800 border border-slate-700">
                    Candidate #{idx + 1}
                  </span>

                  <div className="flex items-center gap-2">
                    {isWinner && (
                      <span className="text-[10px] font-bold text-amber-300 bg-amber-500/15 border border-amber-500/30 px-2 py-0.5 rounded-full flex items-center gap-1">
                        <Award className="w-3 h-3" /> Top Recommended
                      </span>
                    )}
                    {idea.is_selected && (
                      <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/15 border border-emerald-500/30 px-2 py-0.5 rounded-full flex items-center gap-1">
                        <Check className="w-3 h-3" /> Active Plan
                      </span>
                    )}
                    <button
                      onClick={() => handleDeleteIdea(idea.id)}
                      title="Delete idea"
                      className="p-1 rounded text-slate-500 hover:text-red-400 hover:bg-slate-800"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                {/* Idea Details */}
                <div className="space-y-3">
                  <h3 className="text-base font-bold text-white line-clamp-1">{idea.title}</h3>

                  <div className="space-y-1.5 text-xs">
                    <div>
                      <span className="text-slate-400 font-medium">Problem:</span>
                      <p className="text-slate-300 text-[11px] line-clamp-2 mt-0.5 leading-relaxed">{idea.problem_statement}</p>
                    </div>
                    <div>
                      <span className="text-slate-400 font-medium">Proposed Solution:</span>
                      <p className="text-slate-300 text-[11px] line-clamp-2 mt-0.5 leading-relaxed">{idea.proposed_solution}</p>
                    </div>
                    <div className="flex items-center gap-2 text-[11px] text-slate-400 pt-1">
                      <span>Target: <strong className="text-slate-300">{idea.target_audience}</strong></span>
                      <span>•</span>
                      <span>Industry: <strong className="text-slate-300">{idea.industry}</strong></span>
                    </div>
                  </div>

                  {/* Evaluation Score Pill */}
                  {ev && (
                    <div className="mt-4 p-3 rounded-xl bg-slate-950/80 border border-slate-800">
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="text-xs font-semibold text-slate-300">Composite Score</span>
                        <span className="text-sm font-extrabold text-brand-400">{ev.overall_score}/100</span>
                      </div>
                      <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                        <div
                          className="bg-gradient-to-r from-brand-600 to-brand-400 h-full rounded-full transition-all"
                          style={{ width: `${ev.overall_score}%` }}
                        />
                      </div>

                      {/* Mini strengths & risks */}
                      <div className="mt-3 space-y-1.5 text-[11px]">
                        <p className="text-emerald-400 line-clamp-1">
                          <strong>+ Strength:</strong> {ev.strengths?.[0] || 'Clear audience'}
                        </p>
                        <p className="text-amber-400 line-clamp-1">
                          <strong>! Risk:</strong> {ev.risks?.[0] || 'Adoption hurdles'}
                        </p>
                      </div>
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="mt-5 pt-3 border-t border-slate-800 flex items-center justify-between">
                  {!idea.is_selected ? (
                    <button
                      onClick={() => handleSelectIdea(idea.id)}
                      className="text-xs text-brand-400 hover:text-brand-300 font-medium flex items-center gap-1"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" /> Select for Next Steps
                    </button>
                  ) : (
                    <span className="text-xs text-emerald-400 font-medium flex items-center gap-1">
                      <Check className="w-3.5 h-3.5" /> Selected Candidate
                    </span>
                  )}

                  <Link
                    to={`/projects/${projectId}/roadmap`}
                    className="text-xs text-slate-400 hover:text-white"
                  >
                    View Roadmap &rarr;
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Explainable Recommendation & Transparent Rationale Box */}
      {comparison && (
        <div className={`p-6 rounded-2xl border ${
          comparison.is_tie
            ? 'bg-amber-500/5 border-amber-500/20'
            : 'bg-brand-500/5 border-brand-500/20'
        }`}>
          <div className="flex items-start gap-4">
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
              comparison.is_tie ? 'bg-amber-500/20 text-amber-300' : 'bg-brand-500/20 text-brand-400'
            }`}>
              {comparison.is_tie ? <Scale className="w-5 h-5" /> : <Award className="w-5 h-5" />}
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-3">
                <h3 className="text-base font-bold text-white">
                  {comparison.is_tie ? 'Decision Dilemma: Statistical Parity / Tie' : 'Best-Idea Recommendation'}
                </h3>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                  comparison.is_tie
                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                    : 'bg-brand-500/20 text-brand-400 border border-brand-500/30'
                }`}>
                  {comparison.is_tie ? 'Tie / Close Margin (< 2.0 pts)' : 'Transparent Recommendation'}
                </span>
              </div>
              <p className="text-xs text-slate-300 mt-2 leading-relaxed">
                {comparison.recommendation_rationale}
              </p>
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
                <Sliders className="w-4 h-4 text-brand-400" /> Transparent Weight Configuration
              </h3>
              <p className="text-xs text-slate-400">
                Adjust dimension priorities according to your project's current maturity (e.g., Feasibility for Hackathons vs Novelty for Academia).
              </p>
            </div>
            <button
              onClick={() => setShowWeightSliders(!showWeightSliders)}
              className="text-xs text-brand-400 hover:text-brand-300 flex items-center gap-1 font-medium"
            >
              {showWeightSliders ? 'Hide Sliders' : 'Customize Priorities'}
              {showWeightSliders ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
          </div>

          {showWeightSliders && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 pt-4 border-t border-slate-800">
              {Object.keys(DIMENSION_LABELS).map((dimKey) => (
                <div key={dimKey} className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80 space-y-1.5">
                  <div className="flex items-center justify-between">
                    <label className="text-[11px] font-medium text-slate-300 truncate" title={DIMENSION_LABELS[dimKey]}>
                      {DIMENSION_LABELS[dimKey]}
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
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 10-Dimension Side-by-Side Breakdown Table */}
      {evaluations.length > 0 && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden">
          <div className="p-5 border-b border-slate-800">
            <h3 className="text-sm font-bold text-white">10-Dimension Comparative Matrix</h3>
            <p className="text-xs text-slate-400">Granular dimension scores (1 to 10 scale) for all submitted candidates.</p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                <tr>
                  <th className="p-4 font-semibold">Evaluation Dimension</th>
                  <th className="p-4 font-semibold text-center">Weight</th>
                  {ideas.map((i) => (
                    <th key={i.id} className="p-4 font-semibold text-center text-slate-200">
                      {i.title}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/70">
                {Object.keys(DIMENSION_LABELS).map((dimKey) => (
                  <tr key={dimKey} className="hover:bg-slate-800/30 transition-colors">
                    <td className="p-4 font-medium text-slate-200 flex items-center gap-2">
                      {DIMENSION_LABELS[dimKey]}
                    </td>
                    <td className="p-4 text-center text-brand-400 font-mono text-xs">
                      {weights[dimKey] || 1.0}x
                    </td>
                    {ideas.map((i) => {
                      const ev = getEvaluationForIdea(i.id);
                      const score = ev?.dimension_scores?.[dimKey] || 0;
                      return (
                        <td key={i.id} className="p-4 text-center">
                          <span className={`inline-block px-2.5 py-1 rounded-lg text-xs font-bold font-mono ${
                            score >= 8.0 ? 'bg-emerald-500/15 text-emerald-400' :
                            score >= 6.0 ? 'bg-blue-500/15 text-blue-400' :
                            'bg-amber-500/15 text-amber-400'
                          }`}>
                            {score.toFixed(1)}/10
                          </span>
                        </td>
                      );
                    })}
                  </tr>
                ))}
                {/* Composite Row */}
                <tr className="bg-slate-950/80 font-bold border-t-2 border-slate-700">
                  <td className="p-4 text-white text-sm">Overall Composite Score</td>
                  <td className="p-4 text-center text-slate-400 text-xs">Normalized</td>
                  {ideas.map((i) => {
                    const ev = getEvaluationForIdea(i.id);
                    return (
                      <td key={i.id} className="p-4 text-center text-sm font-extrabold text-brand-400">
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

      {/* Idea Submission Modal */}
      {showIdeaModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm overflow-y-auto">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl p-6 shadow-2xl my-8">
            <h2 className="text-lg font-bold text-white mb-1">Submit Candidate Idea ({ideas.length + 1}/3)</h2>
            <p className="text-xs text-slate-400 mb-4">
              Enter concrete details for this candidate idea. The 10-dimension diligence engine will analyze its feasibility.
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
                    placeholder="e.g., Autonomous Wildfire Detection Mesh"
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Industry / Domain *</label>
                  <input
                    type="text"
                    required
                    value={ideaForm.industry}
                    onChange={(e) => setIdeaForm({ ...ideaForm, industry: e.target.value })}
                    placeholder="e.g., ClimateTech, Healthcare, DevOps"
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
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Intended Use Case *</label>
                  <input
                    type="text"
                    required
                    value={ideaForm.intended_use_case}
                    onChange={(e) => setIdeaForm({ ...ideaForm, intended_use_case: e.target.value })}
                    placeholder="e.g., Continuous perimeter infrared sensor sweep"
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Expected Benefits & Outcomes *</label>
                <textarea
                  rows={2}
                  required
                  value={ideaForm.expected_benefits}
                  onChange={(e) => setIdeaForm({ ...ideaForm, expected_benefits: e.target.value })}
                  placeholder="Quantifiable or qualitative advantages (e.g., 80% earlier smoke detection)"
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="block text-[11px] font-medium text-slate-400 mb-1">Technical Preferences</label>
                  <input
                    type="text"
                    value={ideaForm.technical_preferences}
                    onChange={(e) => setIdeaForm({ ...ideaForm, technical_preferences: e.target.value })}
                    placeholder="e.g., LoRaWAN, Python"
                    className="w-full px-3 py-1.5 bg-slate-950 border border-slate-700 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-medium text-slate-400 mb-1">Budget / Scope</label>
                  <input
                    type="text"
                    value={ideaForm.estimated_budget}
                    onChange={(e) => setIdeaForm({ ...ideaForm, estimated_budget: e.target.value })}
                    placeholder="e.g., < $10k MVP"
                    className="w-full px-3 py-1.5 bg-slate-950 border border-slate-700 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-medium text-slate-400 mb-1">Key Constraints</label>
                  <input
                    type="text"
                    value={ideaForm.constraints}
                    onChange={(e) => setIdeaForm({ ...ideaForm, constraints: e.target.value })}
                    placeholder="e.g., Off-grid battery life"
                    className="w-full px-3 py-1.5 bg-slate-950 border border-slate-700 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500"
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
