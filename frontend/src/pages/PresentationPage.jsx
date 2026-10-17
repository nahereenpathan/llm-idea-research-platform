import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { presentationService } from '../services/presentationService';
import { ideaService } from '../services/ideaService';
import { projectService } from '../services/projectService';
import { useProject } from '../contexts/ProjectContext';
import {
  Presentation,
  Plus,
  Trash2,
  Palette,
  Save,
  Sparkles,
  ExternalLink,
  RefreshCw,
  AlertCircle,
  FileDown
} from 'lucide-react';

const THEMES = [
  { id: 'navy_modern', name: 'Navy Modern', bg: 'bg-[#070d1e]', text: 'text-slate-100', accent: 'border-blue-500' },
  { id: 'minimalist_clean', name: 'Minimalist Clean', bg: 'bg-white', text: 'text-slate-900', accent: 'border-slate-800' },
  { id: 'academic_slate', name: 'Academic Slate', bg: 'bg-slate-100', text: 'text-slate-900', accent: 'border-teal-700' },
  { id: 'startup_cyber', name: 'Startup Cyber', bg: 'bg-[#0a0f1d]', text: 'text-purple-100', accent: 'border-purple-500' }
];

const TEMPLATES = [
  { id: 'hackathon', name: 'Hackathon Demo (10 Slides)', desc: 'High impact problem, solution, architecture, and prototype' },
  { id: 'college_project', name: 'College / Capstone Project', desc: 'Objectives, prior art, methodology, and conclusion' },
  { id: 'research_proposal', name: 'Scholarly Research Proposal', desc: 'Hypotheses, literature gap, methodology, and citations' },
  { id: 'startup_pitch', name: 'Venture Pitch Deck', desc: 'Market size, pain point, product differentiation, traction' },
  { id: 'technical', name: 'Technical Architecture Deep Dive', desc: 'Entity schemas, API design, scalability, and security' }
];

export default function PresentationPage() {
  const { id } = useParams();
  const projectId = parseInt(id);
  const { setActiveProject } = useProject();

  const [presentations, setPresentations] = useState([]);
  const [activePres, setActivePres] = useState(null);
  const [activeSlideIndex, setActiveSlideIndex] = useState(0);
  const [ideas, setIdeas] = useState([]);
  const [selectedIdeaId, setSelectedIdeaId] = useState(null);
  const [selectedTemplate, setSelectedTemplate] = useState('hackathon');
  const [selectedTheme, setSelectedTheme] = useState('navy_modern');
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [savingSlide, setSavingSlide] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);

  // Active slide editor fields
  const [slideTitle, setSlideTitle] = useState('');
  const [slideSubtitle, setSlideSubtitle] = useState('');
  const [slideBullets, setSlideBullets] = useState([]);
  const [slideLayout, setSlideLayout] = useState('bullets');

  const fetchDecks = async () => {
    try {
      setErrorMessage(null);
      const proj = await projectService.getProject(projectId);
      setActiveProject(proj);

      const ideasList = await ideaService.listIdeas(projectId);
      setIdeas(ideasList);
      const selected = ideasList.find((i) => i.is_selected) || ideasList[0];
      if (selected) setSelectedIdeaId(selected.id);

      const list = await presentationService.listPresentations(projectId);
      setPresentations(list);
      if (list.length > 0 && !activePres) {
        loadPresentation(list[0].id);
      }
    } catch (err) {
      console.error("Error loading presentations:", err);
      setErrorMessage("Failed to load presentation decks.");
    } finally {
      setLoading(false);
    }
  };

  const loadPresentation = async (presId) => {
    try {
      const full = await presentationService.getPresentation(presId);
      setActivePres(full);
      setSelectedTheme(full.theme || 'navy_modern');
      if (full.slides?.length > 0) {
        setSlideData(full.slides[0]);
        setActiveSlideIndex(0);
      }
    } catch (err) {
      console.error("Failed to load deck:", err);
    }
  };

  const setSlideData = (slide) => {
    setSlideTitle(slide.title || '');
    setSlideSubtitle(slide.subtitle || '');
    setSlideLayout(slide.layout || 'bullets');
    const bullets = slide.content_json?.bullets || [];
    setSlideBullets(bullets);
  };

  useEffect(() => {
    fetchDecks();
  }, [projectId]);

  const handleGenerateDeck = async () => {
    setGenerating(true);
    setErrorMessage(null);
    try {
      const newDeck = await presentationService.generatePresentation(projectId, {
        idea_id: selectedIdeaId,
        theme: selectedTheme,
        template_type: selectedTemplate
      });
      await fetchDecks();
      await loadPresentation(newDeck.id);
    } catch (err) {
      console.error("Failed to generate deck:", err);
      setErrorMessage("Failed to generate presentation deck. Please try again.");
    } finally {
      setGenerating(false);
    }
  };

  const handleRegenerateCurrent = async () => {
    if (!activePres) return;
    setGenerating(true);
    setErrorMessage(null);
    try {
      const regenerated = await presentationService.generatePresentation(projectId, {
        idea_id: activePres.idea_id || selectedIdeaId,
        theme: selectedTheme,
        template_type: activePres.template_type,
        title: activePres.title
      });
      await fetchDecks();
      await loadPresentation(regenerated.id);
    } catch (err) {
      console.error("Failed to refresh presentation deck:", err);
      setErrorMessage("Failed to regenerate presentation deck.");
    } finally {
      setGenerating(false);
    }
  };

  const currentSlide = activePres?.slides?.[activeSlideIndex];

  const handleSaveSlideChanges = async () => {
    if (!currentSlide) return;
    setSavingSlide(true);
    try {
      await presentationService.updateSlide(currentSlide.id, {
        title: slideTitle,
        subtitle: slideSubtitle,
        layout: slideLayout,
        content_json: {
          ...currentSlide.content_json,
          bullets: slideBullets
        }
      });
      await loadPresentation(activePres.id);
    } catch (err) {
      alert("Failed to save slide.");
    } finally {
      setSavingSlide(false);
    }
  };

  const handleAddSlide = async () => {
    if (!activePres) return;
    try {
      await presentationService.addSlide(activePres.id, {
        slide_number: (activePres.slides?.length || 0) + 1,
        layout: 'bullets',
        title: 'New Slide',
        subtitle: 'Key takeaways',
        content_json: { bullets: ['Add key discussion point here'] },
        sort_order: activePres.slides?.length || 0
      });
      await loadPresentation(activePres.id);
      setActiveSlideIndex(activePres.slides.length);
    } catch (err) {
      alert("Failed to add slide.");
    }
  };

  const handleDeleteSlide = async (slideId) => {
    if (activePres.slides.length <= 1) {
      alert("A presentation deck must have at least one slide.");
      return;
    }
    if (window.confirm("Delete this slide?")) {
      try {
        await presentationService.deleteSlide(slideId);
        await loadPresentation(activePres.id);
        setActiveSlideIndex(Math.max(0, activeSlideIndex - 1));
      } catch (err) {
        alert("Failed to delete slide.");
      }
    }
  };

  const handleThemeChange = async (themeKey) => {
    setSelectedTheme(themeKey);
    if (activePres) {
      try {
        await presentationService.updatePresentation(activePres.id, { theme: themeKey });
      } catch (err) {
        console.error("Failed to update theme:", err);
      }
    }
  };

  const downloadPptx = () => {
    if (!activePres) return;
    const url = presentationService.getExportUrl(activePres.id, 'pptx');
    window.open(url, '_blank');
  };

  if (loading) {
    return (
      <div className="py-24 text-center text-slate-400 flex flex-col items-center justify-center gap-3">
        <span className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-xs font-medium">Loading PowerPoint presentation studio...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <Presentation className="w-5 h-5 text-brand-400" /> Editable PowerPoint Presentation Studio
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Build, edit, customize themes, and export real 16:9 widescreen Microsoft PowerPoint (.pptx) decks.
          </p>
        </div>

        {activePres && (
          <div className="flex items-center gap-2 self-start sm:self-auto">
            <button
              onClick={handleRegenerateCurrent}
              disabled={generating}
              title="Regenerate all 10 slides from latest database records"
              className="px-3.5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-200 text-xs font-semibold flex items-center gap-1.5 border border-slate-700 shadow-sm transition-all disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${generating ? 'animate-spin' : ''}`} />
              {generating ? 'Regenerating...' : 'Regenerate Deck'}
            </button>

            <button
              onClick={downloadPptx}
              className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-md transition-all"
            >
              <FileDown className="w-4 h-4" /> Export Editable PPTX
            </button>
          </div>
        )}
      </div>

      {/* Error alert banner */}
      {errorMessage && (
        <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
            <span>{errorMessage}</span>
          </div>
          <button
            onClick={handleGenerateDeck}
            className="px-2.5 py-1 rounded bg-rose-500/20 hover:bg-rose-500/30 text-rose-200 text-[11px] font-semibold flex items-center gap-1"
          >
            <RefreshCw className="w-3 h-3" /> Retry
          </button>
        </div>
      )}

      {!activePres ? (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 max-w-xl mx-auto space-y-5">
          <div className="text-center space-y-1">
            <Presentation className="w-10 h-10 text-brand-400 mx-auto mb-2" />
            <h2 className="text-base font-bold text-white">Generate 10-Slide Presentation Deck</h2>
            <p className="text-xs text-slate-400">
              Select your presentation format. The platform synthesizes project problem statement, architecture, roadmap, and citations.
            </p>
          </div>

          <div className="space-y-4">
            {ideas.length > 0 && (
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Select Candidate Idea</label>
                <select
                  value={selectedIdeaId || ''}
                  onChange={(e) => setSelectedIdeaId(parseInt(e.target.value))}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-brand-500"
                >
                  {ideas.map((i) => (
                    <option key={i.id} value={i.id}>{i.title}</option>
                  ))}
                </select>
              </div>
            )}

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-2">Template Preset</label>
              <div className="space-y-2">
                {TEMPLATES.map((tmpl) => (
                  <div
                    key={tmpl.id}
                    onClick={() => setSelectedTemplate(tmpl.id)}
                    className={`p-3 rounded-xl border cursor-pointer transition-all ${
                      selectedTemplate === tmpl.id
                        ? 'bg-brand-600/15 border-brand-500/40 text-white'
                        : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'
                    }`}
                  >
                    <p className="text-xs font-semibold text-white">{tmpl.name}</p>
                    <p className="text-[10px] text-slate-400">{tmpl.desc}</p>
                  </div>
                ))}
              </div>
            </div>

            <button
              onClick={handleGenerateDeck}
              disabled={generating}
              className="w-full py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold flex items-center justify-center gap-2 shadow-md disabled:opacity-50"
            >
              {generating ? (
                <>
                  <span className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                  Generating 10-Slide Deck...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  Generate Presentation Deck
                </>
              )}
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Theme & Controls Bar */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-wrap items-center justify-between gap-4">
            {/* Theme Selector */}
            <div className="flex items-center gap-2 text-xs">
              <span className="text-slate-400 font-medium flex items-center gap-1.5">
                <Palette className="w-4 h-4 text-brand-400" /> Deck Theme:
              </span>
              <div className="flex items-center gap-1.5">
                {THEMES.map((th) => (
                  <button
                    key={th.id}
                    onClick={() => handleThemeChange(th.id)}
                    className={`px-3 py-1 rounded-lg text-xs font-semibold border transition-all ${
                      selectedTheme === th.id
                        ? 'bg-brand-600 text-white border-brand-500 shadow-sm'
                        : 'bg-slate-950 text-slate-300 border-slate-800 hover:border-slate-700'
                    }`}
                  >
                    {th.name}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={handleAddSlide}
                className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium flex items-center gap-1 border border-slate-700"
              >
                <Plus className="w-3.5 h-3.5" /> Add Slide
              </button>
              <button
                onClick={handleSaveSlideChanges}
                disabled={savingSlide}
                className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-sm"
              >
                <Save className="w-3.5 h-3.5" /> Save Slide
              </button>
            </div>
          </div>

          {/* Presentation Studio Grid: Left Thumbnails + Center Slide Canvas + Right Editor */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 min-h-[580px]">
            {/* Left Thumbnails List (3 cols) */}
            <div className="lg:col-span-3 bg-slate-900 border border-slate-800 rounded-2xl p-3 flex flex-col space-y-2 h-[580px] overflow-y-auto">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 px-1 mb-1">
                Slide Outline ({activePres.slides?.length || 0})
              </span>
              {activePres.slides?.map((slide, sIdx) => (
                <div
                  key={slide.id}
                  onClick={() => {
                    setActiveSlideIndex(sIdx);
                    setSlideData(slide);
                  }}
                  className={`p-2.5 rounded-xl cursor-pointer text-xs flex items-center justify-between border transition-all ${
                    activeSlideIndex === sIdx
                      ? 'bg-brand-600/15 border-brand-500/50 text-white font-semibold'
                      : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center gap-2 truncate">
                    <span className="font-mono text-[10px] text-brand-400 font-bold">{sIdx + 1}.</span>
                    <span className="truncate text-xs">{slide.title}</span>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteSlide(slide.id);
                    }}
                    className="p-1 text-slate-500 hover:text-red-400 opacity-60 hover:opacity-100"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </div>

            {/* Center Widescreen 16:9 Slide Canvas (6 cols) */}
            <div className="lg:col-span-6 bg-slate-900 border border-slate-800 rounded-2xl p-6 flex items-center justify-center">
              <div
                className={`w-full aspect-video rounded-xl p-8 flex flex-col justify-between shadow-2xl border transition-all ${
                  selectedTheme === 'minimalist_clean'
                    ? 'bg-white text-slate-900 border-slate-200'
                    : selectedTheme === 'academic_slate'
                    ? 'bg-slate-100 text-slate-900 border-teal-800'
                    : selectedTheme === 'startup_cyber'
                    ? 'bg-[#0a0f1d] text-purple-100 border-purple-500/40'
                    : 'bg-[#070d1e] text-slate-100 border-brand-500/30'
                }`}
              >
                <div>
                  <h2 className="text-xl md:text-2xl font-extrabold tracking-tight text-brand-400">
                    {slideTitle || 'Slide Title'}
                  </h2>
                  {slideSubtitle && (
                    <p className="text-xs text-slate-400 mt-1">{slideSubtitle}</p>
                  )}
                </div>

                {/* Two-Column vs Bullets View */}
                {currentSlide?.layout === 'two_column' ? (
                  <div className="my-auto grid grid-cols-2 gap-4 text-xs">
                    <div className="space-y-1.5 p-3 rounded-lg bg-slate-950/40 border border-slate-850">
                      {(currentSlide.content_json?.left_column || []).map((item, idx) => (
                        <div key={idx} className="flex items-start gap-1.5">
                          <span className="text-brand-400 font-bold">•</span>
                          <span>{item}</span>
                        </div>
                      ))}
                    </div>
                    <div className="space-y-1.5 p-3 rounded-lg bg-slate-950/40 border border-slate-850">
                      {(currentSlide.content_json?.right_column || []).map((item, idx) => (
                        <div key={idx} className="flex items-start gap-1.5">
                          <span className="text-brand-400 font-bold">•</span>
                          <span>{item}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="my-auto space-y-2">
                    {slideBullets.map((b, bIdx) => (
                      <div key={bIdx} className="flex items-start gap-2.5 text-xs leading-relaxed">
                        <span className="text-brand-400 font-bold">•</span>
                        <span>{b}</span>
                      </div>
                    ))}

                    {/* Citations Preview if present */}
                    {currentSlide?.content_json?.citations_data?.length > 0 && (
                      <div className="mt-2 pt-2 border-t border-slate-800 text-[10px]">
                        <span className="font-semibold text-brand-300 block mb-1">Grounded Source Citations:</span>
                        <div className="space-y-1">
                          {currentSlide.content_json.citations_data.slice(0, 3).map((cite, cIdx) => (
                            <div key={cIdx} className="flex items-center justify-between text-slate-300">
                              <span className="truncate">{cite.title}</span>
                              {cite.url && (
                                <a
                                  href={cite.url}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="text-brand-400 hover:underline flex items-center gap-0.5 ml-2 shrink-0"
                                >
                                  Source <ExternalLink className="w-2.5 h-2.5" />
                                </a>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                <div className="flex items-center justify-between text-[10px] text-slate-400 border-t border-slate-800/40 pt-2">
                  <span>IdeaLens Innovation Platform</span>
                  <span>Slide {activeSlideIndex + 1} of {activePres.slides?.length}</span>
                </div>
              </div>
            </div>

            {/* Right Slide Content Editor (3 cols) */}
            <div className="lg:col-span-3 bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col space-y-4">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Edit Slide #{activeSlideIndex + 1} Content
              </span>

              <div className="space-y-3 flex-1 overflow-y-auto text-xs pr-1">
                <div>
                  <label className="block text-[11px] font-medium text-slate-300 mb-1">Heading</label>
                  <input
                    type="text"
                    value={slideTitle}
                    onChange={(e) => setSlideTitle(e.target.value)}
                    className="w-full px-2.5 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-brand-500"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-medium text-slate-300 mb-1">Subtitle</label>
                  <input
                    type="text"
                    value={slideSubtitle}
                    onChange={(e) => setSlideSubtitle(e.target.value)}
                    className="w-full px-2.5 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-brand-500"
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-[11px] font-medium text-slate-300">Bullet Points</label>
                    <button
                      onClick={() => setSlideBullets([...slideBullets, 'New discussion point'])}
                      className="text-[10px] text-brand-400 hover:text-brand-300 font-semibold"
                    >
                      + Add Bullet
                    </button>
                  </div>
                  <div className="space-y-2">
                    {slideBullets.map((bullet, bIdx) => (
                      <div key={bIdx} className="flex items-start gap-1">
                        <textarea
                          rows={2}
                          value={bullet}
                          onChange={(e) => {
                            const copy = [...slideBullets];
                            copy[bIdx] = e.target.value;
                            setSlideBullets(copy);
                          }}
                          className="w-full p-2 bg-slate-950 border border-slate-700 rounded-lg text-xs text-slate-200 leading-tight focus:outline-none focus:border-brand-500"
                        />
                        <button
                          onClick={() => {
                            const filtered = slideBullets.filter((_, idx) => idx !== bIdx);
                            setSlideBullets(filtered);
                          }}
                          className="p-1 text-slate-500 hover:text-red-400"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <button
                onClick={handleSaveSlideChanges}
                disabled={savingSlide}
                className="w-full py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-md disabled:opacity-50"
              >
                {savingSlide ? 'Saving...' : 'Apply & Save Slide'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
