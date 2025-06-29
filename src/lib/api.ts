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
  
  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
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

    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  }

  // Document endpoints
  async uploadDocument(file: File): Promise<ApiResponse<{document_id: string}>> {
    return this.uploadFile('/documents/upload', file);
  }

  async getDocuments(): Promise<ApiResponse<Document[]>> {
    return this.request('/documents');
  }

  async getDocument(docId: string): Promise<ApiResponse<Document>> {
    return this.request(`/documents/${docId}`);
  }

  async deleteDocument(docId: string): Promise<ApiResponse<{document_id: string}>> {
    return this.request(`/documents/${docId}`, {
      method: 'DELETE',
    });
  }

  // Flashcard endpoints
  async generateFlashcards(docId: string, options: FlashcardOptions): Promise<ApiResponse<Flashcard[]>> {
    return this.request(`/flashcards/generate/${docId}`, {
      method: 'POST',
      body: JSON.stringify(options),
    });
  }

  async getReviewSession(docId: string, sessionSize?: number): Promise<ApiResponse<FlashcardSession>> {
    const params = sessionSize ? `?session_size=${sessionSize}` : '';
    return this.request(`/flashcards/review/${docId}${params}`);
  }

  async submitFlashcardAnswer(answer: FlashcardAnswer): Promise<ApiResponse<any>> {
    return this.request('/flashcards/answer', {
      method: 'POST',
      body: JSON.stringify(answer),
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

  async submitQuiz(quizId: string, answers: string[], timeTaken: number): Promise<ApiResponse<QuizResults>> {
    return this.request(`/quiz/${quizId}/submit`, {
      method: 'POST',
      body: JSON.stringify({
        answers,
        time_taken: timeTaken,
      }),
    });
  }

  // Chat endpoints
  async askQuestion(docId: string, question: string, sessionId?: string): Promise<ApiResponse<ChatResponse>> {
    return this.request(`/chat/${docId}`, {
      method: 'POST',
      body: JSON.stringify({
        question,
        session_id: sessionId,
      }),
    });
  }

  async getChatHistory(docId: string): Promise<ApiResponse<ChatMessage[]>> {
    return this.request(`/chat/${docId}/history`);
  }

  // Analytics endpoints
  async getUserAnalytics(days?: number): Promise<ApiResponse<UserAnalytics>> {
    const params = days ? `?days=${days}` : '';
    return this.request(`/analytics/user${params}`);
  }
}

export const apiService = new ApiService(API_BASE_URL);