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
    <div style={{ display: 'flex', height: '100vh' }}>
      {/* Sidebar list */}
      <div style={{ width: 280, borderRight: '1px solid rgba(124,58,237,0.12)', display: 'flex', flexDirection: 'column', flexShrink: 0 }}>
        {/* Header */}
        <div style={{ padding: '20px 16px', borderBottom: '1px solid rgba(255,255,255,0.05)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h1 style={{ fontWeight: 800, fontSize: 16, color: '#f1f5f9' }}>Study Notes</h1>
            <p style={{ fontSize: 11, color: '#64748b' }}>{noteList.length} notes</p>
          </div>
          <motion.button onClick={() => setShowGenPanel(true)} whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
            style={{ width: 32, height: 32, borderRadius: 8, background: 'linear-gradient(135deg,#7c3aed,#6d28d9)', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Plus size={16} color="#fff" />
          </motion.button>
        </div>

        {/* Note list */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '8px' }}>
          {isLoading && (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 120, color: '#64748b', fontSize: 13 }}>Loading…</div>
          )}
          {!isLoading && noteList.length === 0 && (
            <div style={{ textAlign: 'center', padding: '32px 16px', color: '#64748b' }}>
              <FileText size={32} style={{ marginBottom: 8, color: '#475569' }} />
              <p style={{ fontSize: 13 }}>No notes yet.<br />Generate your first note!</p>
            </div>
          )}
          {noteList.map(note => (
            <motion.button key={note.topic} onClick={() => setSelectedTopic(note.topic)}
              whileHover={{ background: 'rgba(124,58,237,0.1)' }}
              style={{
                width: '100%', textAlign: 'left', padding: '12px', borderRadius: 10, cursor: 'pointer', marginBottom: 4,
                background: selectedTopic === note.topic ? 'rgba(124,58,237,0.15)' : 'transparent',
                border: `1px solid ${selectedTopic === note.topic ? 'rgba(124,58,237,0.4)' : 'transparent'}`,
                transition: 'all 0.15s',
              }}>
              <div style={{ fontWeight: 600, fontSize: 13, color: selectedTopic === note.topic ? '#a78bfa' : '#e2e8f0', marginBottom: 3 }}>{note.topic}</div>
              <div style={{ fontSize: 11, color: '#64748b', display: 'flex', gap: 8 }}>
                <span style={{ padding: '1px 7px', borderRadius: 99, background: 'rgba(124,58,237,0.12)', color: '#7c3aed', fontSize: 10 }}>{note.level}</span>
                {note.created_at && new Date(note.created_at).toLocaleDateString()}
              </div>
              <p style={{ fontSize: 11, color: '#475569', marginTop: 4, lineHeight: 1.4 }}>{note.preview}</p>
            </motion.button>
          ))}
        </div>
      </div>

      {/* Note viewer */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {selectedTopic && noteContent ? (
          <>
            <div style={{ padding: '16px 28px', borderBottom: '1px solid rgba(255,255,255,0.05)', display: 'flex', alignItems: 'center', gap: 12 }}>
              <BookOpen size={18} color="#7c3aed" />
              <div style={{ flex: 1 }}>
                <h2 style={{ fontWeight: 700, fontSize: 16, color: '#f1f5f9' }}>{selectedTopic}</h2>
                <div style={{ fontSize: 12, color: '#64748b' }}>{noteContent.level} · {noteContent.created_at && new Date(noteContent.created_at).toLocaleDateString()}</div>
              </div>
              <motion.button onClick={handleDownload} whileHover={{ scale: 1.05 }}
                style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '7px 14px', borderRadius: 8, border: '1px solid rgba(124,58,237,0.3)', background: 'rgba(124,58,237,0.08)', color: '#a78bfa', cursor: 'pointer', fontSize: 13, fontWeight: 500 }}>
                <Download size={14} /> Download
              </motion.button>
              <motion.button onClick={() => deleteMutation.mutate(selectedTopic)} whileHover={{ scale: 1.05 }}
                style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '7px 14px', borderRadius: 8, border: '1px solid rgba(239,68,68,0.2)', background: 'rgba(239,68,68,0.06)', color: '#fca5a5', cursor: 'pointer', fontSize: 13 }}>
                <Trash2 size={14} />
              </motion.button>
            </div>
            <div style={{ flex: 1, overflowY: 'auto', padding: '28px 36px' }} className="markdown-content">
              <ReactMarkdown>{noteContent.content}</ReactMarkdown>
            </div>
          </>
        ) : (
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b', flexDirection: 'column', gap: 12 }}>
            <FileText size={48} color="#1e293b" />
            <p style={{ fontSize: 15 }}>Select a note to view it</p>
            <p style={{ fontSize: 13, color: '#475569' }}>Or generate a new note using the + button</p>
          </div>
        )}
      </div>

      {/* Generate panel */}
      <AnimatePresence>
        {showGenPanel && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)', zIndex: 50, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
            onClick={e => e.target === e.currentTarget && setShowGenPanel(false)}>
            <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.9, opacity: 0 }}
              style={{ width: 440, padding: 32, borderRadius: 20, background: '#1a1a2e', border: '1px solid rgba(124,58,237,0.3)', boxShadow: '0 25px 60px rgba(0,0,0,0.6)' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
                <h3 style={{ fontSize: 18, fontWeight: 700, color: '#f1f5f9' }}>Generate Study Note</h3>
                <button onClick={() => setShowGenPanel(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748b' }}><X size={18} /></button>
              </div>
              <div style={{ marginBottom: 16 }}>
                <label style={{ fontSize: 13, color: '#94a3b8', fontWeight: 500, display: 'block', marginBottom: 8 }}>Topic</label>
                <select value={genTopic} onChange={e => setGenTopic(e.target.value)}
                  style={{ width: '100%', padding: '10px 12px', borderRadius: 10, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(124,58,237,0.25)', color: '#f1f5f9', fontSize: 14, outline: 'none' }}>
                  {TOPICS.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
              <div style={{ marginBottom: 24 }}>
                <label style={{ fontSize: 13, color: '#94a3b8', fontWeight: 500, display: 'block', marginBottom: 8 }}>Level</label>
                <div style={{ display: 'flex', gap: 8 }}>
                  {['Beginner', 'Intermediate', 'Advanced'].map(l => (
                    <button key={l} onClick={() => setGenLevel(l)}
                      style={{ flex: 1, padding: '8px', borderRadius: 8, border: `1px solid ${genLevel === l ? 'rgba(124,58,237,0.6)' : 'rgba(255,255,255,0.08)'}`, background: genLevel === l ? 'rgba(124,58,237,0.15)' : 'transparent', color: genLevel === l ? '#a78bfa' : '#64748b', cursor: 'pointer', fontSize: 13, fontWeight: genLevel === l ? 600 : 400 }}>
                      {l}
                    </button>
                  ))}
                </div>
              </div>
              <motion.button
                onClick={() => generateMutation.mutate({ topic: genTopic, level: genLevel })}
                disabled={generateMutation.isPending}
                whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                style={{ width: '100%', padding: '13px', borderRadius: 10, border: 'none', background: 'linear-gradient(135deg,#7c3aed,#6d28d9)', color: '#fff', fontWeight: 600, fontSize: 15, cursor: generateMutation.isPending ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, boxShadow: '0 4px 20px rgba(124,58,237,0.4)' }}>
                {generateMutation.isPending ? <><Loader2 size={16} style={{ animation: 'spin 0.8s linear infinite' }} /> Generating…</> : 'Generate Note'}
              </motion.button>
              <p style={{ textAlign: 'center', marginTop: 12, fontSize: 12, color: '#475569' }}>Uses LLM + RAG to create comprehensive study notes</p>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
      <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
    </div>
  )
}
