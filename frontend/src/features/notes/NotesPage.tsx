import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import ReactMarkdown from 'react-markdown'
import { FileText, Plus, Trash2, Download, X, Loader2, BookOpen } from 'lucide-react'
import { notesApi } from '@/lib/api'
import { TOPICS } from '@/types'
import type { NoteListItem } from '@/types'

export default function NotesPage() {
  const qc = useQueryClient()
  const [selectedTopic, setSelectedTopic] = useState<string | null>(null)
  const [generating, setGenerating]       = useState<string | null>(null)
  const [showGenPanel, setShowGenPanel]   = useState(false)
  const [genTopic, setGenTopic]           = useState<string>(TOPICS[0])
  const [genLevel, setGenLevel]           = useState('Intermediate')

  const { data: noteList = [], isLoading } = useQuery<NoteListItem[]>({
    queryKey: ['notes-list'],
    queryFn:  () => notesApi.list().then(r => r.data),
    staleTime: 30_000,
  })

  const { data: noteContent } = useQuery({
    queryKey: ['note', selectedTopic],
    queryFn:  () => selectedTopic ? notesApi.get(selectedTopic).then(r => r.data) : null,
    enabled:  !!selectedTopic,
    staleTime: 60_000,
  })

  const generateMutation = useMutation({
    mutationFn: (body: { topic: string; level: string }) => notesApi.generate(body).then(r => r.data),
    onMutate:   ({ topic }) => setGenerating(topic),
    onSettled:  () => { setGenerating(null); setShowGenPanel(false) },
    onSuccess:  () => { qc.invalidateQueries({ queryKey: ['notes-list'] }); qc.invalidateQueries({ queryKey: ['note'] }) },
  })

  const deleteMutation = useMutation({
    mutationFn: (topic: string) => notesApi.delete(topic),
    onSuccess:  () => {
      qc.invalidateQueries({ queryKey: ['notes-list'] })
      setSelectedTopic(null)
    },
  })

  const handleDownload = () => {
    if (!noteContent) return
    const blob = new Blob([noteContent.content], { type: 'text/markdown' })
    const url  = URL.createObjectURL(blob)
    const a    = Object.assign(document.createElement('a'), { href: url, download: `${selectedTopic}.md` })
    a.click(); URL.revokeObjectURL(url)
  }

  return (
    <div style={{ display: 'flex', height: '100vh', background: 'var(--bg-base)' }}>
      {/* Sidebar list */}
      <div style={{ width: 320, borderRight: '1px solid var(--border-subtle)', background: 'var(--bg-elevated)', display: 'flex', flexDirection: 'column', flexShrink: 0, zIndex: 10 }}>
        {/* Header */}
        <div style={{ padding: '24px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h1 style={{ fontWeight: 600, fontSize: 18, color: 'var(--text-primary)', letterSpacing: '-0.01em', marginBottom: 2 }}>Study Notes</h1>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{noteList.length} notes</p>
          </div>
          <motion.button onClick={() => setShowGenPanel(true)} whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
            style={{ width: 36, height: 36, borderRadius: 10, background: 'var(--primary)', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: 'var(--shadow-sm)' }}>
            <Plus size={18} color="#fff" />
          </motion.button>
        </div>

        {/* Note list */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '16px' }}>
          {isLoading && (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 120, color: 'var(--text-secondary)', fontSize: 14, fontWeight: 500 }}>Loading notes…</div>
          )}
          {!isLoading && noteList.length === 0 && (
            <div style={{ textAlign: 'center', padding: '48px 16px', color: 'var(--text-muted)' }}>
              <FileText size={36} style={{ marginBottom: 16, color: 'var(--border-subtle)' }} />
              <p style={{ fontSize: 14, fontWeight: 500 }}>No notes yet.<br />Generate your first note!</p>
            </div>
          )}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {noteList.map(note => {
              const isSelected = selectedTopic === note.topic;
              return (
                <motion.button key={note.topic} onClick={() => setSelectedTopic(note.topic)}
                  whileHover={!isSelected ? { background: 'var(--bg-hover)' } : undefined}
                  style={{
                    width: '100%', textAlign: 'left', padding: '16px', borderRadius: 12, cursor: 'pointer',
                    background: isSelected ? 'var(--primary-subtle)' : 'transparent',
                    border: `1px solid ${isSelected ? 'var(--primary-subtle)' : 'transparent'}`,
                    transition: 'all 0.15s ease', display: 'flex', flexDirection: 'column', gap: 6,
                  }}>
                  <div style={{ fontWeight: 600, fontSize: 14, color: isSelected ? 'var(--primary)' : 'var(--text-primary)', letterSpacing: '-0.01em' }}>{note.topic}</div>
                  <div style={{ fontSize: 12, color: isSelected ? 'var(--primary)' : 'var(--text-secondary)', display: 'flex', gap: 8, alignItems: 'center', opacity: isSelected ? 0.9 : 1 }}>
                    <span style={{ padding: '2px 8px', borderRadius: 99, background: isSelected ? 'rgba(255,255,255,0.2)' : 'var(--bg-surface)', fontWeight: 500 }}>{note.level}</span>
                    {note.created_at && new Date(note.created_at).toLocaleDateString()}
                  </div>
                  <p style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.4, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>{note.preview}</p>
                </motion.button>
              )
            })}
          </div>
        </div>
      </div>

      {/* Note viewer */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', background: 'var(--bg-base)' }}>
        {selectedTopic && noteContent ? (
          <>
            <div style={{ padding: '24px 32px', borderBottom: '1px solid var(--border-subtle)', background: 'var(--bg-elevated)', display: 'flex', alignItems: 'center', gap: 16 }}>
              <div style={{ width: 40, height: 40, borderRadius: 10, background: 'var(--primary-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <BookOpen size={20} color="var(--primary)" />
              </div>
              <div style={{ flex: 1 }}>
                <h2 style={{ fontWeight: 600, fontSize: 18, color: 'var(--text-primary)', letterSpacing: '-0.01em', marginBottom: 4 }}>{selectedTopic}</h2>
                <div style={{ fontSize: 13, color: 'var(--text-secondary)', fontWeight: 500 }}>{noteContent.level} · {noteContent.created_at && new Date(noteContent.created_at).toLocaleDateString()}</div>
              </div>
              <div style={{ display: 'flex', gap: 12 }}>
                <motion.button onClick={handleDownload} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                  style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 16px', borderRadius: 10, border: '1px solid var(--border-subtle)', background: 'var(--bg-surface)', color: 'var(--text-primary)', cursor: 'pointer', fontSize: 14, fontWeight: 500 }}>
                  <Download size={16} /> Download
                </motion.button>
                <motion.button onClick={() => deleteMutation.mutate(selectedTopic)} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                  style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 16px', borderRadius: 10, border: '1px solid var(--danger)', background: 'var(--danger-subtle)', color: 'var(--danger)', cursor: 'pointer', fontSize: 14, fontWeight: 500 }}>
                  <Trash2 size={16} /> Delete
                </motion.button>
              </div>
            </div>
            <div style={{ flex: 1, overflowY: 'auto', padding: '40px 48px' }}>
              <div className="markdown-content" style={{ maxWidth: 800, margin: '0 auto', background: 'var(--bg-elevated)', padding: '40px', borderRadius: 20, boxShadow: 'var(--shadow-sm)', border: '1px solid var(--border-subtle)' }}>
                <ReactMarkdown>{noteContent.content}</ReactMarkdown>
              </div>
            </div>
          </>
        ) : (
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', flexDirection: 'column', gap: 16 }}>
            <div style={{ width: 64, height: 64, borderRadius: 16, background: 'var(--bg-surface)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <FileText size={32} color="var(--border-subtle)" />
            </div>
            <div style={{ textAlign: 'center' }}>
              <p style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8 }}>Select a note to view</p>
              <p style={{ fontSize: 14, color: 'var(--text-muted)' }}>Or generate a new note using the + button in the sidebar</p>
            </div>
          </div>
        )}
      </div>

      {/* Generate panel */}
      <AnimatePresence>
        {showGenPanel && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', backdropFilter: 'blur(8px)', zIndex: 50, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
            onClick={e => e.target === e.currentTarget && setShowGenPanel(false)}>
            <motion.div initial={{ scale: 0.95, opacity: 0, y: 20 }} animate={{ scale: 1, opacity: 1, y: 0 }} exit={{ scale: 0.95, opacity: 0, y: 20 }}
              style={{ width: 440, padding: 32, borderRadius: 24, background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', boxShadow: 'var(--shadow-md)' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
                <h3 style={{ fontSize: 20, fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '-0.01em' }}>Generate Study Note</h3>
                <button onClick={() => setShowGenPanel(false)} style={{ background: 'var(--bg-surface)', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', width: 32, height: 32, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><X size={16} /></button>
              </div>
              <div style={{ marginBottom: 20 }}>
                <label style={{ fontSize: 14, color: 'var(--text-secondary)', fontWeight: 500, display: 'block', marginBottom: 8 }}>Topic</label>
                <select value={genTopic} onChange={e => setGenTopic(e.target.value)}
                  style={{ width: '100%', padding: '12px 16px', borderRadius: 12, background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', color: 'var(--text-primary)', fontSize: 15, outline: 'none', fontWeight: 500 }}>
                  {TOPICS.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
              <div style={{ marginBottom: 32 }}>
                <label style={{ fontSize: 14, color: 'var(--text-secondary)', fontWeight: 500, display: 'block', marginBottom: 8 }}>Difficulty Level</label>
                <div style={{ display: 'flex', gap: 10 }}>
                  {['Beginner', 'Intermediate', 'Advanced'].map(l => {
                    const isSelected = genLevel === l;
                    return (
                      <button key={l} onClick={() => setGenLevel(l)}
                        style={{ flex: 1, padding: '10px', borderRadius: 10, border: `1px solid ${isSelected ? 'var(--primary)' : 'var(--border-subtle)'}`, background: isSelected ? 'var(--primary-subtle)' : 'var(--bg-surface)', color: isSelected ? 'var(--primary)' : 'var(--text-secondary)', cursor: 'pointer', fontSize: 14, fontWeight: isSelected ? 600 : 500, transition: 'all 0.15s ease' }}>
                        {l}
                      </button>
                    )
                  })}
                </div>
              </div>
              <motion.button
                onClick={() => generateMutation.mutate({ topic: genTopic, level: genLevel })}
                disabled={generateMutation.isPending}
                whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                style={{ width: '100%', padding: '14px', borderRadius: 12, border: 'none', background: 'var(--text-primary)', color: 'var(--bg-base)', fontWeight: 600, fontSize: 15, cursor: generateMutation.isPending ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
                {generateMutation.isPending ? <><Loader2 size={18} style={{ animation: 'spin 0.8s linear infinite' }} /> Generating…</> : 'Generate Note'}
              </motion.button>
              <p style={{ textAlign: 'center', marginTop: 16, fontSize: 13, color: 'var(--text-muted)' }}>Uses LLM + RAG to create comprehensive study notes</p>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
