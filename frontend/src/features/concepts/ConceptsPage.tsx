/**
 * ConceptsPage — Visual concept explorer for each AI/ML topic.
 * Shows key concepts as interactive cards with descriptions, analogies,
 * and links to the tutor for deep dives. Replaces the old visual_engine feature.
 */
import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { Brain, ChevronRight, X, BookOpen, Lightbulb, Zap, ArrowRight, BookMarked } from 'lucide-react'
import { useUIStore } from '@/store/uiStore'
import { TOPICS } from '@/types'

// ── Concept data per topic ────────────────────────────────────────────────────

const CONCEPT_DB: Record<string, { name: string; emoji: string; summary: string; analogy: string; difficulty: 'beginner' | 'intermediate' | 'advanced'; tags: string[] }[]> = {
  'Neural Networks': [
    { name: 'Perceptrons', emoji: '🔵', summary: 'The simplest neural unit — takes inputs, applies weights, outputs a signal via an activation function.', analogy: 'Like a light switch: receives electrical signals and decides whether to turn on.', difficulty: 'beginner', tags: ['foundational', 'unit'] },
    { name: 'Backpropagation', emoji: '🔄', summary: 'Algorithm that computes gradients by propagating error backward through the network to update weights.', analogy: 'Like tracking who made a mistake in an assembly line and telling each worker to adjust.', difficulty: 'intermediate', tags: ['training', 'optimization'] },
    { name: 'Activation Functions', emoji: '⚡', summary: 'Non-linear functions (ReLU, Sigmoid, Tanh) that allow networks to learn complex patterns.', analogy: 'Like a bouncer at a club — decides what signal gets through.', difficulty: 'beginner', tags: ['nonlinearity', 'core'] },
    { name: 'Gradient Descent', emoji: '⛷️', summary: 'Iterative optimization that nudges weights in the direction that reduces loss.', analogy: 'Like descending a foggy mountain by always stepping downhill.', difficulty: 'intermediate', tags: ['optimization', 'training'] },
    { name: 'Overfitting', emoji: '🎯', summary: 'When a model memorizes training data but fails to generalize to new examples.', analogy: 'Like a student who memorizes answers but can\'t solve new problems.', difficulty: 'beginner', tags: ['generalization', 'pitfall'] },
    { name: 'Batch Normalization', emoji: '📊', summary: 'Normalizes layer inputs to stabilize and accelerate training.', analogy: 'Like tuning instruments before a concert so they all play in harmony.', difficulty: 'advanced', tags: ['training', 'stability'] },
  ],
  'Transformers': [
    { name: 'Self-Attention', emoji: '👁️', summary: 'Mechanism that lets each token look at all other tokens to compute context-aware representations.', analogy: 'Like reading a sentence and noticing which words are most related to each other.', difficulty: 'intermediate', tags: ['core', 'attention'] },
    { name: 'Multi-Head Attention', emoji: '🎭', summary: 'Multiple attention heads run in parallel, each learning different relationship patterns.', analogy: 'Like having multiple readers each highlighting different themes in a text.', difficulty: 'intermediate', tags: ['attention', 'parallel'] },
    { name: 'Positional Encoding', emoji: '📍', summary: 'Injects word order information into token embeddings since attention is order-agnostic.', analogy: 'Like numbering the pages of a shuffled book so you know where each page belongs.', difficulty: 'intermediate', tags: ['encoding', 'sequence'] },
    { name: 'Feed-Forward Network', emoji: '➡️', summary: 'A small MLP applied independently to each token after the attention layer.', analogy: 'Like each student processing their own notes after a group discussion.', difficulty: 'beginner', tags: ['ffn', 'core'] },
    { name: 'Layer Normalization', emoji: '⚖️', summary: 'Normalizes activations within a transformer layer to improve training stability.', analogy: 'Like a teacher recalibrating scores after each test to maintain fair grading.', difficulty: 'intermediate', tags: ['normalization', 'stability'] },
  ],
  'LLMs': [
    { name: 'Token Prediction', emoji: '🎲', summary: 'LLMs are trained to predict the next token given previous tokens — from this simple task all abilities emerge.', analogy: 'Like autocomplete on steroids, trained on the entire internet.', difficulty: 'beginner', tags: ['pretraining', 'core'] },
    { name: 'Scaling Laws', emoji: '📈', summary: 'Performance improves predictably with more parameters, data, and compute.', analogy: 'Like knowing exactly how much stronger a muscle gets with each workout.', difficulty: 'advanced', tags: ['research', 'scaling'] },
    { name: 'RLHF', emoji: '🎯', summary: 'Reinforcement Learning from Human Feedback — fine-tunes LLMs to be helpful, harmless, and honest.', analogy: 'Like a student who gets grades from human teachers rather than automated tests.', difficulty: 'advanced', tags: ['alignment', 'finetuning'] },
    { name: 'Emergent Abilities', emoji: '✨', summary: 'Capabilities that appear suddenly at large scales — not seen in smaller models.', analogy: 'Like water: H2O molecules don\'t individually flow, but enough of them together does.', difficulty: 'advanced', tags: ['scaling', 'research'] },
    { name: 'Context Window', emoji: '🪟', summary: 'The maximum number of tokens a model can process at once. Limits memory of past conversation.', analogy: 'Like short-term memory — you can only hold so many things in mind at once.', difficulty: 'beginner', tags: ['core', 'limits'] },
  ],
  'CNNs': [
    { name: 'Convolution Operation', emoji: '🔍', summary: 'A filter slides over an image detecting local patterns like edges, textures, and shapes.', analogy: 'Like a magnifying glass scanning a photo looking for specific patterns.', difficulty: 'beginner', tags: ['core', 'operation'] },
    { name: 'Pooling Layers', emoji: '🗜️', summary: 'Downsamples feature maps by taking max or average of regions, reducing spatial dimensions.', analogy: 'Like summarizing a book chapter into key bullet points.', difficulty: 'beginner', tags: ['downsampling', 'core'] },
    { name: 'Feature Maps', emoji: '🗺️', summary: 'Outputs of convolutional filters — each map represents a different detected feature.', analogy: 'Like multiple X-ray images each showing a different internal structure.', difficulty: 'intermediate', tags: ['features', 'output'] },
    { name: 'Transfer Learning', emoji: '🔄', summary: 'Reusing a pre-trained CNN\'s learned features for a new task with minimal extra training.', analogy: 'Like hiring an expert photographer to do graphic design — most skills transfer.', difficulty: 'intermediate', tags: ['practical', 'efficiency'] },
  ],
  'Diffusion Models': [
    { name: 'Forward Diffusion', emoji: '🌫️', summary: 'Gradually adds Gaussian noise to an image over T timesteps until it becomes pure noise.', analogy: 'Like slowly adding milk to coffee until you can\'t taste coffee anymore.', difficulty: 'intermediate', tags: ['process', 'noise'] },
    { name: 'Reverse Process', emoji: '🎨', summary: 'The model learns to denoise step-by-step, gradually recovering a clean image from noise.', analogy: 'Like a sculptor revealing a statue by chipping away at marble.', difficulty: 'intermediate', tags: ['generation', 'core'] },
    { name: 'Score Matching', emoji: '📐', summary: 'Trains the model to predict the gradient of the data distribution, pointing toward clean data.', analogy: 'Like GPS telling you which direction to walk, not the destination itself.', difficulty: 'advanced', tags: ['training', 'math'] },
    { name: 'Latent Diffusion', emoji: '🗜️', summary: 'Runs diffusion in a compressed latent space (not pixel space) for efficiency — used by Stable Diffusion.', analogy: 'Like doing a jigsaw puzzle with smaller, simplified pieces before revealing the full image.', difficulty: 'advanced', tags: ['efficiency', 'sdxl'] },
  ],
  'GANs': [
    { name: 'Generator', emoji: '🎭', summary: 'Produces fake data samples trying to fool the discriminator.', analogy: 'Like a forger creating counterfeit paintings trying to fool an art expert.', difficulty: 'beginner', tags: ['core', 'architecture'] },
    { name: 'Discriminator', emoji: '🕵️', summary: 'Classifies whether inputs are real or generated. Trained in tandem with the generator.', analogy: 'Like the art expert learning to spot fakes while the forger gets better.', difficulty: 'beginner', tags: ['core', 'architecture'] },
    { name: 'Adversarial Training', emoji: '⚔️', summary: 'Generator and discriminator compete — a minimax game that drives both to improve.', analogy: 'Like an arms race where both sides keep upgrading their technology.', difficulty: 'intermediate', tags: ['training', 'game-theory'] },
    { name: 'Mode Collapse', emoji: '💥', summary: 'The generator gets stuck producing limited variety, finding a loophole to fool the discriminator.', analogy: 'Like a student who memorizes one essay and submits it for every assignment.', difficulty: 'advanced', tags: ['pitfall', 'training'] },
  ],
  'Fine-Tuning and RAG': [
    { name: 'LoRA', emoji: '🔧', summary: 'Low-Rank Adaptation: injects small trainable matrices into frozen model weights for cheap fine-tuning.', analogy: 'Like attaching adjustable clip-on lenses to fixed glasses instead of buying new glasses.', difficulty: 'intermediate', tags: ['efficiency', 'finetuning'] },
    { name: 'Retrieval Pipeline', emoji: '🔍', summary: 'Fetches relevant document chunks from a vector store to augment the LLM\'s context at inference time.', analogy: 'Like an open-book exam where you look up relevant pages before answering.', difficulty: 'intermediate', tags: ['rag', 'core'] },
    { name: 'Vector Embeddings', emoji: '📐', summary: 'Dense numerical representations of text that capture semantic meaning for similarity search.', analogy: 'Like coordinates on a map — similar meanings are geographically close.', difficulty: 'beginner', tags: ['embeddings', 'search'] },
    { name: 'Chunking Strategies', emoji: '✂️', summary: 'Methods for splitting documents (fixed-size, semantic, sentence-window) to optimize retrieval quality.', analogy: 'Like deciding how big to cut bites of food — too big you choke, too small you lose flavor.', difficulty: 'intermediate', tags: ['rag', 'practical'] },
    { name: 'Reranking', emoji: '🏆', summary: 'A second-pass model rescores retrieved chunks for relevance before passing to the LLM.', analogy: 'Like a hiring manager shortlisting CVs before the CEO does final interviews.', difficulty: 'advanced', tags: ['rag', 'quality'] },
  ],
  'Prompt Engineering': [
    { name: 'Zero-Shot Prompting', emoji: '🎯', summary: 'Asking the model to perform a task without any examples — just a clear instruction.', analogy: 'Like telling someone to cook a meal with only a recipe description, no demo.', difficulty: 'beginner', tags: ['technique', 'prompting'] },
    { name: 'Chain-of-Thought', emoji: '🔗', summary: 'Asking the model to reason step-by-step before giving the final answer. Dramatically improves accuracy.', analogy: 'Like asking someone to show their work in math — the process reveals (and fixes) errors.', difficulty: 'intermediate', tags: ['reasoning', 'technique'] },
    { name: 'Few-Shot Learning', emoji: '📋', summary: 'Providing 2–5 examples in the prompt so the model learns the pattern from context.', analogy: 'Like giving 3 example sentences before asking someone to continue the style.', difficulty: 'beginner', tags: ['technique', 'examples'] },
    { name: 'System Prompts', emoji: '⚙️', summary: 'Instructions given before the user message that define the model\'s persona, rules, and behavior.', analogy: 'Like a job description that an employee reads before starting work.', difficulty: 'beginner', tags: ['prompting', 'control'] },
  ],
}

// Fallback concepts for topics without explicit entries
const DEFAULT_CONCEPTS = (topic: string) => [
  { name: `${topic} Fundamentals`, emoji: '📚', summary: `Core foundational principles of ${topic}.`, analogy: 'Like the alphabet before you can read.', difficulty: 'beginner' as const, tags: ['core'] },
  { name: 'Key Architectures', emoji: '🏗️', summary: `The most important model architectures used in ${topic}.`, analogy: 'Like the blueprints of the most important buildings in a city.', difficulty: 'intermediate' as const, tags: ['architecture'] },
  { name: 'Training Process', emoji: '🏋️', summary: `How models in ${topic} are trained end-to-end.`, analogy: 'Like a sports training regime — repetition, feedback, refinement.', difficulty: 'intermediate' as const, tags: ['training'] },
]

const DIFF_COLORS = {
  beginner:     { bg: 'var(--success-subtle)',  border: 'var(--success)',  text: 'var(--success)' },
  intermediate: { bg: 'var(--warning-subtle)',  border: 'var(--warning)',  text: 'var(--warning)' },
  advanced:     { bg: 'var(--danger-subtle)',   border: 'var(--danger)',   text: 'var(--danger)' },
}

// ── Concept Card ──────────────────────────────────────────────────────────────
function ConceptCard({
  concept,
  index,
  onSelect,
}: {
  concept: typeof CONCEPT_DB['Neural Networks'][0]
  index: number
  onSelect: () => void
}) {
  const diff = DIFF_COLORS[concept.difficulty]
  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04 }}
      whileHover={{ y: -4, boxShadow: 'var(--shadow-md)' }}
      onClick={onSelect}
      style={{
        padding: '24px', borderRadius: 20, cursor: 'pointer',
        background: 'var(--bg-elevated)',
        border: '1px solid var(--border-subtle)',
        boxShadow: 'var(--shadow-sm)',
        transition: 'all 0.2s ease',
        display: 'flex', flexDirection: 'column', gap: 16,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <div style={{
          width: 44, height: 44, borderRadius: 12, fontSize: 22,
          background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
        }}>
          {concept.emoji}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontWeight: 600, fontSize: 16, color: 'var(--text-primary)', marginBottom: 4, letterSpacing: '-0.01em' }}>{concept.name}</div>
          <span style={{
            fontSize: 10, fontWeight: 600, padding: '3px 8px', borderRadius: 8,
            background: diff.bg, color: diff.text,
            textTransform: 'uppercase', letterSpacing: '0.04em',
          }}>
            {concept.difficulty}
          </span>
        </div>
        <ChevronRight size={18} color="var(--border-subtle)" />
      </div>
      <p style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.5, margin: 0 }}>
        {concept.summary}
      </p>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {concept.tags.map(tag => (
          <span key={tag} style={{
            fontSize: 11, padding: '4px 10px', borderRadius: 99,
            background: 'var(--bg-surface)', color: 'var(--text-secondary)',
            fontWeight: 500, border: '1px solid var(--border-subtle)'
          }}>#{tag}</span>
        ))}
      </div>
    </motion.div>
  )
}

// ── Concept Detail Drawer ─────────────────────────────────────────────────────
function ConceptDrawer({
  concept,
  topic,
  onClose,
}: {
  concept: typeof CONCEPT_DB['Neural Networks'][0] | null
  topic: string
  onClose: () => void
}) {
  const navigate  = useNavigate()
  const { setCurrentTopic } = useUIStore()

  if (!concept) return null
  const diff = DIFF_COLORS[concept.difficulty]

  const goToTutor = () => {
    setCurrentTopic(topic)
    navigate('/tutor')
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)',
        backdropFilter: 'blur(8px)', zIndex: 1000,
        display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24,
      }}
    >
      <motion.div
        initial={{ scale: 0.95, opacity: 0, y: 20 }}
        animate={{ scale: 1, opacity: 1, y: 0 }}
        exit={{ scale: 0.95, opacity: 0, y: 20 }}
        onClick={e => e.stopPropagation()}
        style={{
          background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)',
          borderRadius: 24, padding: '40px', maxWidth: 600, width: '100%',
          boxShadow: 'var(--shadow-md)',
        }}
      >
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 16, marginBottom: 32 }}>
          <div style={{
            width: 64, height: 64, borderRadius: 16, fontSize: 32,
            background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
          }}>
            {concept.emoji}
          </div>
          <div style={{ flex: 1, paddingTop: 4 }}>
            <h2 style={{ fontSize: '24px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8, letterSpacing: '-0.02em' }}>{concept.name}</h2>
            <span style={{
              fontSize: 11, fontWeight: 600, padding: '4px 10px', borderRadius: 8,
              background: diff.bg, color: diff.text,
              textTransform: 'uppercase', letterSpacing: '0.04em',
            }}>
              {concept.difficulty}
            </span>
          </div>
          <button onClick={onClose} style={{ background: 'var(--bg-surface)', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', padding: 8, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <X size={18} />
          </button>
        </div>

        {/* Summary */}
        <div style={{ marginBottom: 28 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12, color: 'var(--primary)', fontWeight: 600, fontSize: 14 }}>
            <BookOpen size={16} /> What is it?
          </div>
          <p style={{ fontSize: 15, color: 'var(--text-secondary)', lineHeight: 1.6, margin: 0 }}>{concept.summary}</p>
        </div>

        {/* Analogy */}
        <div style={{
          padding: '20px', borderRadius: 16, marginBottom: 32,
          background: 'var(--warning-subtle)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12, color: 'var(--warning)', fontWeight: 600, fontSize: 14 }}>
            <Lightbulb size={16} /> Analogy
          </div>
          <p style={{ fontSize: 15, color: 'var(--text-primary)', lineHeight: 1.6, margin: 0, fontStyle: 'italic' }}>"{concept.analogy}"</p>
        </div>

        {/* Tags */}
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 32 }}>
          {concept.tags.map(tag => (
            <span key={tag} style={{
              fontSize: 12, padding: '6px 12px', borderRadius: 99,
              background: 'var(--bg-surface)', color: 'var(--text-secondary)',
              border: '1px solid var(--border-subtle)', fontWeight: 500,
            }}>#{tag}</span>
          ))}
        </div>

        {/* CTA */}
        <motion.button
          whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
          onClick={goToTutor}
          style={{
            width: '100%', padding: '16px', borderRadius: 16, border: 'none',
            background: 'var(--text-primary)',
            color: 'var(--bg-base)', fontWeight: 600, fontSize: 15, cursor: 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
            transition: 'opacity 0.2s'
          }}
        >
          <Zap size={18} /> Ask AI Tutor to explain this
          <ArrowRight size={18} />
        </motion.button>
      </motion.div>
    </motion.div>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export default function ConceptsPage() {
  const { currentTopic, setCurrentTopic } = useUIStore()
  const [activeTopic, setActiveTopic] = useState(currentTopic || TOPICS[0])
  const [selectedConcept, setSelectedConcept] = useState<typeof CONCEPT_DB['Neural Networks'][0] | null>(null)
  const [filter, setFilter] = useState<'all' | 'beginner' | 'intermediate' | 'advanced'>('all')

  const concepts = CONCEPT_DB[activeTopic] ?? DEFAULT_CONCEPTS(activeTopic)
  const filtered = filter === 'all' ? concepts : concepts.filter(c => c.difficulty === filter)

  return (
    <div style={{ padding: '40px 48px', maxWidth: 1200, margin: '0 auto', width: '100%', boxSizing: 'border-box' }}>
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} style={{ marginBottom: 40 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 12 }}>
          <div style={{
            width: 48, height: 48, borderRadius: 16,
            background: 'var(--text-primary)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: 'var(--shadow-sm)'
          }}>
            <BookMarked size={24} color="var(--bg-base)" />
          </div>
          <h1 style={{ fontSize: '28px', fontWeight: 600, color: 'var(--text-primary)', margin: 0, letterSpacing: '-0.02em' }}>
            Concept Explorer
          </h1>
        </div>
        <p style={{ color: 'var(--text-secondary)', fontSize: 15, margin: 0, fontWeight: 500 }}>
          Browse key concepts for each topic — click any card for an in-depth breakdown and analogy.
        </p>
      </motion.div>

      {/* Topic selector strip */}
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 32 }}>
        {TOPICS.map(t => {
          const isActive = activeTopic === t;
          return (
            <motion.button
              key={t}
              whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
              onClick={() => { setActiveTopic(t); setCurrentTopic(t); setSelectedConcept(null) }}
              style={{
                padding: '10px 16px', borderRadius: 12, fontSize: 14, fontWeight: 500,
                cursor: 'pointer', border: `1px solid ${isActive ? 'var(--primary)' : 'var(--border-subtle)'}`,
                background: isActive ? 'var(--primary-subtle)' : 'var(--bg-surface)',
                color: isActive ? 'var(--primary)' : 'var(--text-secondary)',
                transition: 'all 0.15s ease', boxShadow: isActive ? '0 0 0 1px var(--primary-subtle)' : 'none'
              }}
            >
              {t}
            </motion.button>
          )
        })}
      </div>

      {/* Difficulty filter */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 32, alignItems: 'center', flexWrap: 'wrap' }}>
        <span style={{ fontSize: 13, color: 'var(--text-secondary)', fontWeight: 600, marginRight: 4 }}>Filter:</span>
        {(['all', 'beginner', 'intermediate', 'advanced'] as const).map(d => {
          const isSelected = filter === d;
          return (
            <button
              key={d}
              onClick={() => setFilter(d)}
              style={{
                padding: '8px 16px', borderRadius: 12, fontSize: 13, fontWeight: 500,
                cursor: 'pointer', border: `1px solid ${isSelected ? 'var(--text-primary)' : 'var(--border-subtle)'}`,
                background: isSelected ? 'var(--text-primary)' : 'var(--bg-surface)',
                color: isSelected ? 'var(--bg-base)' : 'var(--text-secondary)',
                transition: 'all 0.15s ease', textTransform: 'capitalize',
              }}
            >
              {d}
            </button>
          )
        })}
        <span style={{ marginLeft: 'auto', fontSize: 13, color: 'var(--text-muted)', fontWeight: 500 }}>
          {filtered.length} concept{filtered.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Concept grid */}
      <motion.div
        key={activeTopic + filter}
        initial={{ opacity: 0 }} animate={{ opacity: 1 }}
        style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 24 }}
      >
        {filtered.map((concept, i) => (
          <ConceptCard
            key={concept.name}
            concept={concept}
            index={i}
            onSelect={() => setSelectedConcept(concept)}
          />
        ))}
      </motion.div>

      {/* Detail drawer */}
      <AnimatePresence>
        {selectedConcept && (
          <ConceptDrawer
            concept={selectedConcept}
            topic={activeTopic}
            onClose={() => setSelectedConcept(null)}
          />
        )}
      </AnimatePresence>
    </div>
  )
}
