"use client"

import { useState, useCallback } from "react"
import { apiService } from "@/lib/api"
import { Flashcard, FlashcardOptions } from "@/types/api"

interface QuizSessionResults {
  totalQuestions: number
  correctAnswers: number
  incorrectAnswers: number
  score: number
  timeTaken: number
  results: Array<{
    flashcard: Flashcard
    userAnswer: string
    isCorrect: boolean
    timeTaken: number
  }>
}

interface UseFlashcardQuizState {
  // Loading states
  loading: boolean
  generatingQuiz: boolean
  
  // Error handling
  error: string | null
  
  // Quiz data
  flashcards: Flashcard[]
  currentQuizId: string | null
  
  // Quiz session state
  quizMode: 'setup' | 'session' | 'results'
  sessionResults: QuizSessionResults | null
  
  // Quiz configuration
  selectedDeckId: string | null
  quizOptions: Record<string, unknown> | null
}

interface UseFlashcardQuizActions {
  // Setup actions
  startQuiz: (deckId: string, questionCount: number, options: Record<string, unknown>) => Promise<void>
  resetQuiz: () => void
  
  // Session actions
  completeQuiz: (results: QuizSessionResults) => void
  exitQuiz: () => void
  
  // Navigation actions
  goToSetup: () => void
  goToSession: () => void
  goToResults: () => void
  
  // Error handling
  clearError: () => void
}

export function useFlashcardQuiz(): UseFlashcardQuizState & UseFlashcardQuizActions {
  const [state, setState] = useState<UseFlashcardQuizState>({
    loading: false,
    generatingQuiz: false,
    error: null,
    flashcards: [],
    currentQuizId: null,
    quizMode: 'setup',
    sessionResults: null,
    selectedDeckId: null,
    quizOptions: null
  })

  const updateState = useCallback((updates: Partial<UseFlashcardQuizState>) => {
    setState(prev => ({ ...prev, ...updates }))
  }, [])

  const clearError = useCallback(() => {
    updateState({ error: null })
  }, [updateState])

  const resetQuiz = useCallback(() => {
    updateState({
      loading: false,
      generatingQuiz: false,
      error: null,
      flashcards: [],
      currentQuizId: null,
      quizMode: 'setup',
      sessionResults: null,
      selectedDeckId: null,
      quizOptions: null
    })
  }, [updateState])

  const startQuiz = useCallback(async (deckId: string, questionCount: number, options: Record<string, unknown>) => {
    try {
      updateState({ 
        generatingQuiz: true, 
        error: null,
        selectedDeckId: deckId,
        quizOptions: options
      })

      // Generate flashcards for the quiz
      const flashcardOptions: FlashcardOptions = {
        count: questionCount,
        difficulty: String(options.difficulty) || 'medium',
        bloom_level: typeof options.bloom_level === 'string' ? options.bloom_level : undefined
      }

      console.log('Generating flashcards with options:', flashcardOptions)
      
      const response = await apiService.generateFlashcards(deckId, flashcardOptions)
      
      if (!response.success || !response.data) {
        throw new Error(response.message || 'Failed to generate flashcards')
      }

      const flashcards = response.data
      
      if (flashcards.length === 0) {
        throw new Error('No flashcards were generated. Please check the document content.')
      }

      // Shuffle flashcards for random order
      const shuffledFlashcards = [...flashcards].sort(() => Math.random() - 0.5)
      
      // Limit to requested count
      const quizFlashcards = shuffledFlashcards.slice(0, questionCount === 999 ? flashcards.length : questionCount)

      console.log(`Generated ${quizFlashcards.length} flashcards for quiz`)

      updateState({
        flashcards: quizFlashcards,
        currentQuizId: `flashcard-quiz-${Date.now()}`,
        quizMode: 'session',
        generatingQuiz: false
      })
    } catch (error) {
      console.error('Error starting quiz:', error)
      updateState({
        error: error instanceof Error ? error.message : 'Failed to start quiz',
        generatingQuiz: false
      })
    }
  }, [updateState])

  const completeQuiz = useCallback((results: QuizSessionResults) => {
    updateState({
      sessionResults: results,
      quizMode: 'results'
    })
  }, [updateState])

  const exitQuiz = useCallback(() => {
    updateState({
      quizMode: 'setup'
    })
  }, [updateState])

  const goToSetup = useCallback(() => {
    updateState({ quizMode: 'setup' })
  }, [updateState])

  const goToSession = useCallback(() => {
    if (state.flashcards.length > 0) {
      updateState({ quizMode: 'session' })
    }
  }, [updateState, state.flashcards.length])

  const goToResults = useCallback(() => {
    if (state.sessionResults) {
      updateState({ quizMode: 'results' })
    }
  }, [updateState, state.sessionResults])

  return {
    // State
    ...state,
    
    // Actions
    startQuiz,
    resetQuiz,
    completeQuiz,
    exitQuiz,
    goToSetup,
    goToSession,
    goToResults,
    clearError
  }
}