import {
  ApiResponse,
  ApiError,
  Document,
  Flashcard,
  FlashcardSession,
  FlashcardAnswer,
  FlashcardOptions,
  Quiz,
  QuizOptions,
  QuizResults,
  ChatResponse,
  ChatMessage,
  UserAnalytics
} from '@/types/api';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiService {
  private baseURL: string;
  private authToken: string | null = null;
  
  constructor(baseURL: string) {
    this.baseURL = baseURL;
    // Try to get token from localStorage on initialization
    if (typeof window !== 'undefined') {
      this.authToken = localStorage.getItem('auth_token');
    }
  }

  setAuthToken(token: string | null) {
    this.authToken = token;
    if (typeof window !== 'undefined') {
      if (token) {
        localStorage.setItem('auth_token', token);
      } else {
        localStorage.removeItem('auth_token');
      }
    }
  }

  getAuthToken(): string | null {
    return this.authToken;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint.startsWith('/api') ? '' : '/api'}${endpoint}`;
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...options.headers as Record<string, string>,
    };

    // Add authentication header if token is available
    if (this.authToken) {
      headers['Authorization'] = `Bearer ${this.authToken}`;
    }
    
    const config: RequestInit = {
      headers,
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        // Handle authentication errors
        if (response.status === 401) {
          this.setAuthToken(null);
          if (typeof window !== 'undefined') {
            window.location.href = '/login';
          }
          throw new Error('Authentication required. Please log in again.');
        }
        
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  private async uploadFile(endpoint: string, file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);

    const headers: Record<string, string> = {};
    
    // Add authentication header if token is available
    if (this.authToken) {
      headers['Authorization'] = `Bearer ${this.authToken}`;
    }
    console.log(`Uploading file to ${this.baseURL}${endpoint.startsWith('/api') ? '' : '/api'}${endpoint}`);
    const response = await fetch(`${this.baseURL}${endpoint.startsWith('/api') ? '' : '/api'}${endpoint}`, {
      method: 'POST',
      headers,
      body: formData,
    });

    if (!response.ok) {
      // Handle authentication errors
      if (response.status === 401) {
        this.setAuthToken(null);
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
        throw new Error('Authentication required. Please log in again.');
      }
      
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  }

  // Authentication endpoints
  async login(email: string, password: string): Promise<ApiResponse<{access_token: string, user: any}>> {
    const response = await this.request<ApiResponse<{access_token: string, user: any}>>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    
    // Store the token after successful login
    if (response.success && response.data?.access_token) {
      this.setAuthToken(response.data.access_token);
    }
    
    return response;
  }

  async register(email: string, password: string, name: string): Promise<ApiResponse<{access_token: string, user: any}>> {
    const response = await this.request<ApiResponse<{access_token: string, user: any}>>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, name }),
    });
    
    // Store the token after successful registration
    if (response.success && response.data?.access_token) {
      this.setAuthToken(response.data.access_token);
    }
    
    return response;
  }

  async logout(): Promise<void> {
    this.setAuthToken(null);
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
  }

  async getCurrentUser(): Promise<ApiResponse<any>> {
    return this.request('/auth/me');
  }

  // Document endpoints
  async uploadDocument(file: File): Promise<ApiResponse<{document_id: string}>> {
    return this.uploadFile('/documents/upload', file);
  }

  async listDocuments(): Promise<ApiResponse<Document[]>> {
    return this.request('/documents/list');
  }

  async getDocument(docId: string): Promise<ApiResponse<Document>> {
    return this.request(`/documents/${docId}`);
  }

  async deleteDocument(docId: string): Promise<ApiResponse<{document_id: string}>> {
    return this.request(`/documents/${docId}`, {
      method: 'DELETE',
    });
  }

  async reprocessDocument(docId: string): Promise<ApiResponse<any>> {
    return this.request(`/documents/${docId}/process`, {
      method: 'POST',
    });
  }

  async getDocumentStats(docId: string): Promise<ApiResponse<any>> {
    return this.request(`/documents/${docId}/stats`);
  }

  async searchDocument(docId: string, query: string): Promise<ApiResponse<any>> {
    return this.request(`/documents/${docId}/search`, {
      method: 'POST',
      body: JSON.stringify({ query }),
    });
  }

  // Flashcard endpoints
  async generateFlashcards(docId: string, options: FlashcardOptions): Promise<ApiResponse<Flashcard[]>> {
    return this.request(`/flashcards/generate/${docId}`, {
      method: 'POST',
      body: JSON.stringify(options),
    });
  }

  async generateFlashcardsFromTopic(topic: string, count: number = 10, difficulty: string = 'medium'): Promise<ApiResponse<Flashcard[]>> {
    return this.request('/flashcards/generate-from-topic', {
      method: 'POST',
      body: JSON.stringify({
        topic,
        count,
        difficulty
      }),
    });
  }

  async getReviewSession(docId: string, sessionSize?: number): Promise<ApiResponse<FlashcardSession>> {
    const params = sessionSize ? `?session_size=${sessionSize}` : '';
    return this.request(`/flashcards/session/${docId}${params}`);
  }

  async submitFlashcardAnswer(answer: FlashcardAnswer): Promise<ApiResponse<any>> {
    return this.request('/flashcards/answer', {
      method: 'POST',
      body: JSON.stringify(answer),
    });
  }

  async getReviewSchedule(docId: string): Promise<ApiResponse<any>> {
    return this.request(`/flashcards/review-schedule/${docId}`);
  }

  async getFlashcardStats(docId: string): Promise<ApiResponse<any>> {
    return this.request(`/flashcards/stats/${docId}`);
  }

  async resetFlashcard(cardId: string): Promise<ApiResponse<any>> {
    return this.request(`/flashcards/${cardId}/reset`, {
      method: 'POST',
    });
  }

  async deleteFlashcard(cardId: string): Promise<ApiResponse<any>> {
    return this.request(`/flashcards/${cardId}`, {
      method: 'DELETE',
    });
  }

  async getAllUserFlashcards(skip: number = 0, limit: number = 50): Promise<ApiResponse<any>> {
    return this.request(`/flashcards/all?skip=${skip}&limit=${limit}`);
  }

  async getFlashcardsByDocument(docId: string, skip: number = 0, limit: number = 50): Promise<ApiResponse<any>> {
    return this.request(`/flashcards/by-document/${docId}?skip=${skip}&limit=${limit}`);
  }

  async getDueFlashcards(limit: number = 20): Promise<ApiResponse<any>> {
    return this.request(`/flashcards/due?limit=${limit}`);
  }

  async getFlashcardTopics(): Promise<ApiResponse<any>> {
    return this.request('/flashcards/topics');
  }

  async submitBatchAnswers(answers: FlashcardAnswer[]): Promise<ApiResponse<any>> {
    return this.request('/flashcards/batch-answer', {
      method: 'POST',
      body: JSON.stringify({ answers }),
    });
  }

  // Quiz endpoints
  async generateQuiz(docId: string, options: QuizOptions): Promise<ApiResponse<Quiz>> {
    return this.request(`/quiz/generate/${docId}`, {
      method: 'POST',
      body: JSON.stringify(options),
    });
  }

  async getQuiz(quizId: string): Promise<ApiResponse<Quiz>> {
    return this.request(`/quiz/${quizId}`);
  }

  async deleteQuiz(quizId: string): Promise<ApiResponse<any>> {
    return this.request(`/quiz/${quizId}`, {
      method: 'DELETE',
    });
  }

  async submitQuiz(quizId: string, answers: string[], timeTaken: number): Promise<ApiResponse<QuizResults>> {
    return this.request(`/quiz/${quizId}/submit`, {
      method: 'POST',
      body: JSON.stringify({
        answers,
        time_taken: timeTaken,
      }),
    });
  }

  async getQuizResults(quizId: string, attemptId: string): Promise<ApiResponse<QuizResults>> {
    return this.request(`/quiz/${quizId}/results/${attemptId}`);
  }

  async getQuizHistory(docId: string): Promise<ApiResponse<any>> {
    return this.request(`/quiz/history/${docId}`);
  }

  async getUserQuizHistory(): Promise<ApiResponse<any>> {
    return this.request('/quiz/user/history');
  }

  async getQuizAnalytics(quizId: string): Promise<ApiResponse<any>> {
    return this.request(`/quiz/${quizId}/analytics`);
  }

  async getQuestionsByDifficulty(quizId: string, level: string): Promise<ApiResponse<any>> {
    return this.request(`/quiz/${quizId}/difficulty/${level}`);
  }

  async getQuestionsByBloomLevel(quizId: string, level: string): Promise<ApiResponse<any>> {
    return this.request(`/quiz/${quizId}/bloom/${level}`);
  }

  // Chat endpoints
  async askQuestion(question: string, sessionId?: string): Promise<ApiResponse<ChatResponse>> {
    return this.request('/chat/ask', {
      method: 'POST',
      body: JSON.stringify({
        question,
        session_id: sessionId,
      }),
    });
  }

  async searchDocuments(query: string, docIds?: string[]): Promise<ApiResponse<any>> {
    return this.request('/chat/search', {
      method: 'POST',
      body: JSON.stringify({ query, doc_ids: docIds }),
    });
  }

  async askQuestionStream(question: string, sessionId?: string): Promise<ApiResponse<any>> {
    return this.request('/chat/ask-stream', {
      method: 'POST',
      body: JSON.stringify({ question, session_id: sessionId }),
    });
  }

  async getSimilarQuestions(question: string): Promise<ApiResponse<any>> {
    return this.request(`/chat/similar-questions?question=${question}`);
  }

  async getRagStatistics(): Promise<ApiResponse<any>> {
    return this.request('/chat/stats');
  }

  async healthCheck(): Promise<ApiResponse<any>> {
    return this.request('/chat/health');
  }

  // Analytics endpoints
  async getUserAnalytics(): Promise<ApiResponse<UserAnalytics>> {
    return this.request('/analytics/user');
  }

  async getDocumentAnalytics(docId: string): Promise<ApiResponse<any>> {
    return this.request(`/analytics/document/${docId}`);
  }

  async getLearningProgress(): Promise<ApiResponse<any>> {
    return this.request('/analytics/progress');
  }

  async getStudyRecommendations(): Promise<ApiResponse<any>> {
    return this.request('/analytics/recommendations');
  }

  async getSystemAnalytics(): Promise<ApiResponse<any>> {
    return this.request('/analytics/system');
  }

  async trackLearningSession(session: any): Promise<ApiResponse<any>> {
    return this.request('/analytics/track-session', {
      method: 'POST',
      body: JSON.stringify(session),
    });
  }

  async getRecentActivity(limit?: number): Promise<ApiResponse<any>> {
    const params = limit ? `?limit=${limit}` : '';
    return this.request(`/analytics/recent-activity${params}`);
  }
  // Default endpoints
  async getRoot(): Promise<ApiResponse<any>> {
    return this.request('/');
  }

  async getHealth(): Promise<ApiResponse<any>> {
    return this.request('/health');
  }

  async getApiInfo(): Promise<ApiResponse<any>> {
    return this.request('/api/info');
  }
}

export const apiService = new ApiService(API_BASE_URL);