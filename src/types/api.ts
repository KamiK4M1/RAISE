export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  message: string;
  timestamp: string;
}

export interface ApiError {
  success: false;
  error: {
    code: string;
    message: string;
    details?: string;
  };
  timestamp: string;
}

export interface Document {
  document_id: string;
  filename: string;
  file_type: string;
  file_size: number;
  processing_status?: 'pending' | 'processing' | 'completed' | 'failed';
  status?: 'pending' | 'processing' | 'completed' | 'failed';
  processed_at?: string;
  created_at: string;
  chunk_count?: number;
  tags?: string[];
  summary?: string;
  version?: number;
}

export interface Flashcard {
  card_id: string;
  document_id: string;
  question: string;
  answer: string;
  difficulty: 'easy' | 'medium' | 'hard';
  ease_factor: number;
  interval: number;
  next_review: string;
  review_count: number;
}

export interface FlashcardSession {
  session_id: string;
  cards: Flashcard[];
  total_cards: number;
  new_cards: number;
  review_cards: number;
}

export interface FlashcardAnswer {
  card_id: string;
  quality: number;
  time_taken: number;
  user_answer: string;
}

export interface FlashcardOptions {
  bloom_level?: string;
  difficulty?: string;
  count?: number;
}

export interface Quiz {
  quiz_id: string;
  document_id: string;
  title: string;
  description?: string;
  questions: QuizQuestion[];
  total_points: number;
  time_limit?: number;
  attempts_allowed: number;
  bloom_distribution: Record<string, number>;
}

export interface QuizQuestion {
  question_id: string;
  question: string;
  options: string[];
  correct_answer: string;
  explanation: string;
  bloom_level: string;
  difficulty: string;
  points: number;
}

export interface QuizOptions {
  question_count: number;
  bloom_distribution: Record<string, number>;
  difficulty: string;
  time_limit?: number;
}

export interface QuizResults {
  quiz_id: string;
  score: number;
  total_points: number;
  percentage: number;
  time_taken: number;
  correct_answers: number;
  incorrect_answers: number;
  bloom_performance: Record<string, number>;
  question_results: Array<{
    question_id: string;
    correct: boolean;
    user_answer: string;
    correct_answer: string;
    points_earned: number;
  }>;
}

export interface ChatMessage {
  chat_id: string;
  session_id?: string;
  document_id: string;
  question: string;
  answer: string;
  sources: Array<{
    chunk_id: string;
    text: string;
    similarity: number;
  }>;
  confidence: number;
  created_at: string;
}

export interface ChatResponse {
  answer: string;
  sources: Array<{
    chunk_id: string;
    text: string;
    similarity: number;
  }>;
  confidence: number;
  session_id?: string;
  response_time?: number;
  sources_count?: number;
  total_chunks_found?: number;
}

export interface ChatSession {
  session_id: string;
  document_id: string;
  document_title: string;
  message_count: number;
  created_at: string;
  last_activity: string;
}

export interface UserAnalytics {
  user_id: string;
  period_days: number;
  flashcard_stats: {
    total_reviews: number;
    average_quality: number;
    retention_rate: number;
    streak_days: number;
    cards_mastered: number;
  };
  quiz_stats: {
    total_attempts: number;
    average_score: number;
    improvement_rate: number;
    bloom_strengths: string[];
    bloom_weaknesses: string[];
    bloom_averages: Record<string, number>;
    bloom_scores: Record<string, number>;
  };
  chat_stats: {
    total_questions: number;
    average_confidence: number;
    topics_explored: number;
    engagement_level: string;
  };
  study_patterns: {
    total_study_time: number;
    average_session_length: number;
    most_active_day: string;
    most_active_hour: number;
    consistency_score: number;
    weekly_activity: Array<{
      day: string;
      hours_studied: number;
    }>;
  };
  learning_progress: {
    total_documents_studied: number;
    learning_velocity: number;
    mastery_level: string;
    recent_performance: number[];
  };
  recommendations: Array<{
    type: string;
    title: string;
    description: string;
    priority: string;
    created_at: string;
  }>;
}