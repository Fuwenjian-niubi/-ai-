// 与后端 schemas.py 对应的前端类型

export interface UserOut {
  id: number
  username: string
  role: string // 'admin' | 'user'
  created_at: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  role: string
}

export interface SessionOut {
  id: number
  title: string
  created_at: string
  updated_at: string
}

export interface KBOut {
  id: number
  name: string
  description: string
  spot: string
  created_at: string
}

export interface DocOut {
  id: number
  kb_id: number
  filename: string
  chunk_count: number
  created_at: string
}

export interface Citation {
  index: number
  source: string | null
  content: string
}

export interface QAResponse {
  answer: string
  citations: Citation[]
  skill: string
  memory_used: string[]
}

export interface SkillInfo {
  name: string
  description: string
}

// 前端内部消息模型（assistant 消息可携带引用/技能/记忆）
export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
  skill?: string
  memory_used?: string[]
  pending?: boolean // 等待后端响应的占位
}
