"use client"

import { useFlashcardQuiz } from "@/hooks/useFlashcardQuiz"
import { QuizSetup } from "@/components/quiz/QuizSetup"
import { FlashcardQuizSession } from "@/components/quiz/FlashcardQuizSession"
import { QuizResults } from "@/components/quiz/QuizResults"
import { Brain, XCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import { AuthWrapper } from "@/components/providers/auth-wrpper"

export default function FlashcardQuizPage() {
  const {
    // State
    loading,
    generatingQuiz,
    error,
    flashcards,
    quizMode,
    sessionResults,
    quizOptions,
    
    // Actions
    startQuiz,
    resetQuiz,
    completeQuiz,
    exitQuiz,
    goToSetup,
    clearError
  } = useFlashcardQuiz()

  // Handle retry quiz (same settings)
  const handleRetryQuiz = () => {
    if (sessionResults && quizOptions) {
      goToSetup()
    }
  }

  // Error state
  if (error && quizMode === 'setup') {
    return (
      <AuthWrapper>
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <XCircle className="h-12 w-12 text-red-600 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Quiz Error</h2>
          <p className="text-red-600 mb-4">{error}</p>
          <div className="space-x-4">
            <Button onClick={clearError}>Try Again</Button>
            <Link href="/flashcards">
              <Button variant="outline">Back to Flashcards</Button>
            </Link>
          </div>
        </div>
        </div>
      </AuthWrapper>
    )
  }

  // Render based on quiz mode
  switch (quizMode) {
    case 'setup':
      return (
        <AuthWrapper>
          <QuizSetup
            onStartQuiz={startQuiz}
            loading={generatingQuiz}
          />
        </AuthWrapper>
      )

    case 'session':
      if (flashcards.length === 0) {
        return (
          <AuthWrapper>
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
            <div className="text-center">
              <Brain className="h-12 w-12 text-blue-600 mx-auto mb-4 animate-spin" />
              <p className="text-gray-600">Preparing your quiz...</p>
            </div>
            </div>
          </AuthWrapper>
        )
      }

      return (
        <AuthWrapper>
          <FlashcardQuizSession
            flashcards={flashcards}
            onComplete={completeQuiz}
            onExit={exitQuiz}
            timeLimit={quizOptions?.time_limit}
            title="Flashcard Quiz"
          />
        </AuthWrapper>
      )

    case 'results':
      if (!sessionResults) {
        return (
          <AuthWrapper>
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
            <div className="text-center">
              <XCircle className="h-12 w-12 text-gray-600 mx-auto mb-4" />
              <p className="text-gray-600 mb-4">No results available</p>
              <Button onClick={goToSetup}>Start New Quiz</Button>
            </div>
            </div>
          </AuthWrapper>
        )
      }

      return (
        <AuthWrapper>
          <QuizResults
            results={sessionResults}
            onRetry={handleRetryQuiz}
            onBackToSetup={resetQuiz}
            title="Flashcard Quiz Results"
          />
        </AuthWrapper>
      )

    default:
      return (
        <AuthWrapper>
          <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="text-center">
            <Brain className="h-12 w-12 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-600 mb-4">Something went wrong</p>
            <Button onClick={resetQuiz}>Reset Quiz</Button>
          </div>
          </div>
        </AuthWrapper>
      )
  }
}