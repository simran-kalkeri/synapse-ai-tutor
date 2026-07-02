// All TypeScript domain types matching FastAPI Pydantic schemas

export interface User {
  id: string
  username: string
  email?: string
  display_name?: string
  avatar_url?: string
  created_at?: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface LoginRequest {
  username: string
  password: string
}

export interface TutorRequest {
  topic: string
  question: string
  level?: string
  include_voice?: boolean
  model?: string
}

export interface SourceItem {
  source: string
  page: number
  text: string
}

export interface TutorStreamEvent {
  type: 'chunk' | 'sources' | 'metadata' | 'done' | 'error'
  content?: string
  sources?: SourceItem[]
  metadata?: Record<string, unknown>
}

export interface ChatMessage {
  id: string
  topic: string
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

export interface AssessmentQuestion {
  id: number
  question: string
  options: string[]
  difficulty: 'easy' | 'intermediate' | 'hard'
  topic: string
}

export interface AssessmentResult {
  topic: string
  score: number
  max_score: number
  percentage: number
  level: string
  mastery: number
  knowledge_gaps: string[]
  correct: number
  total: number
  mistakes: string[]
}

export interface MasteryScore {
  topic: string
  mastery: number
  level: string
}

export interface StudentProfile {
  username: string
  level: string
  learning_style: string
  strong_topics: string[]
  weak_topics: string[]
  mastery_scores: Record<string, number>
  total_sessions: number
  streak_days: number
  recent_topics: string[]
}

export interface GraphNode {
  id: string
  label: string
  node_type?: string
  level?: string
  topic?: string
}

export interface GraphEdge {
  source: string
  target: string
  relation: string
}

export interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
  ready: boolean
}

export interface Note {
  topic: string
  content: string
  level: string
  created_at: string
}

export interface NoteListItem {
  topic: string
  level: string
  preview: string
  created_at: string
}

export interface RoadmapStep {
  name: string
  description: string
  status: 'locked' | 'current' | 'complete'
  order: number
  step_type: 'prerequisite' | 'gap' | 'core' | 'advanced'
  is_current: boolean
}

export interface Roadmap {
  topic: string
  level: string
  steps: RoadmapStep[]
  generated_at: string
}

export interface DashboardStats {
  total_sessions: number
  streak_days: number
  topics_studied: number
  average_mastery: number
  strongest_topic?: string
  weakest_topic?: string
}

export interface ActivityItem {
  event_type: string
  topic: string
  timestamp: string
  details?: string
}

export interface DashboardData {
  stats: DashboardStats
  recent_activity: ActivityItem[]
  mastery_by_topic: Record<string, number>
}

export const TOPICS = [
  'Neural Networks', 'CNNs', 'RNNs', 'Transformers', 'LLMs',
  'Prompt Engineering', 'Generative AI Fundamentals', 'GANs',
  'Diffusion Models', 'Fine-Tuning and RAG',
] as const

export type Topic = typeof TOPICS[number]

export const DIFFICULTY_COLORS = {
  easy: '#10b981',
  intermediate: '#f59e0b',
  hard: '#ef4444',
} as const

export const MASTERY_COLORS = {
  expert:       '#10b981',
  high:         '#06b6d4',
  moderate:     '#f59e0b',
  low:          '#ef4444',
  'not assessed': '#64748b',
} as const
