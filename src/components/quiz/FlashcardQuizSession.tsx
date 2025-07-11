"use client"

import { useState, useEffect, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { 
  Brain, 
  ArrowLeft, 
  CheckCircle, 
  XCircle, 
  Lightbulb,
  ArrowRight,
  Timer
} from "lucide-react"
import { Flashcard } from "@/types/api"

interface FlashcardQuizSessionProps {
  flashcards: Flashcard[]
  onComplete: (results: QuizSessionResults) => void
  onExit: () => void
  timeLimit?: number
  title?: string
}

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

export function FlashcardQuizSession({ 
  flashcards, 
  onComplete, 
  onExit,
  timeLimit = 0,
  title = "Flashcard Quiz"
}: FlashcardQuizSessionProps) {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [userAnswer, setUserAnswer] = useState("")
  const [showFeedback, setShowFeedback] = useState(false)
  const [isCorrect, setIsCorrect] = useState(false)
  const [sessionResults, setSessionResults] = useState<QuizSessionResults['results']>([])
  const [startTime, ] = useState(Date.now())
  const [questionStartTime, setQuestionStartTime] = useState(Date.now())
  const [timeLeft, setTimeLeft] = useState(timeLimit)
  const [sessionEnded, setSessionEnded] = useState(false)

  const currentCard = flashcards[currentIndex]
  const isLastQuestion = currentIndex === flashcards.length - 1
  const progress = ((currentIndex + 1) / flashcards.length) * 100

  const handleSubmitAnswer = useCallback(() => {
    const questionTime = Date.now() - questionStartTime
    const correct = compareAnswers(userAnswer, currentCard.answer)
    
    setIsCorrect(correct)
    setShowFeedback(true)
    
    const result = {
      flashcard: currentCard,
      userAnswer: userAnswer,
      isCorrect: correct,
      timeTaken: questionTime
    }
    
    setSessionResults(prev => [...prev, result])
  }, [questionStartTime, userAnswer, currentCard])

  const handleTimeUp = useCallback(() => {
    if (!sessionEnded) {
      // Auto-submit current answer or mark as incorrect
      handleSubmitAnswer()
    }
  }, [sessionEnded, handleSubmitAnswer])

  // Timer effect
  useEffect(() => {
    if (timeLimit > 0 && timeLeft > 0 && !showFeedback && !sessionEnded) {
      const timer = setInterval(() => {
        setTimeLeft((prev) => {
          if (prev <= 1) {
            handleTimeUp()
            return 0
          }
          return prev - 1
        })
      }, 1000)

      return () => clearInterval(timer)
    }
  }, [timeLeft, showFeedback, sessionEnded, timeLimit, handleTimeUp])

  // Reset question start time when moving to next question
  useEffect(() => {
    setQuestionStartTime(Date.now())
  }, [currentIndex])

  const compareAnswers = (userAnswer: string, correctAnswer: string): boolean => {
    const normalize = (str: string) => str.toLowerCase().trim()
    const userNormalized = normalize(userAnswer)
    const correctNormalized = normalize(correctAnswer)
    
    // Exact match
    if (userNormalized === correctNormalized) return true
    
    // Check if user answer contains the key parts of correct answer
    const correctWords = correctNormalized.split(/\s+/).filter(word => word.length > 2)
    const userWords = userNormalized.split(/\s+/)
    
    // If most key words are present, consider it correct
    const matchingWords = correctWords.filter(word => 
      userWords.some(userWord => userWord.includes(word) || word.includes(userWord))
    )
    
    return matchingWords.length >= Math.ceil(correctWords.length * 0.7)
  }

  const handleNextQuestion = () => {
    if (isLastQuestion) {
      handleCompleteQuiz()
    } else {
      setCurrentIndex(prev => prev + 1)
      setUserAnswer("")
      setShowFeedback(false)
      setIsCorrect(false)
    }
  }

  const handleCompleteQuiz = () => {
    const totalTime = Date.now() - startTime
    const correctCount = sessionResults.filter(r => r.isCorrect).length + (isCorrect ? 1 : 0)
    const totalQuestions = flashcards.length
    const score = Math.round((correctCount / totalQuestions) * 100)
    
    const results: QuizSessionResults = {
      totalQuestions,
      correctAnswers: correctCount,
      incorrectAnswers: totalQuestions - correctCount,
      score,
      timeTaken: totalTime,
      results: sessionResults
    }
    
    setSessionEnded(true)
    onComplete(results)
  }

  const handleSkipQuestion = () => {
    setUserAnswer("")
    handleSubmitAnswer()
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, "0")}`
  }

  if (!currentCard) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <XCircle className="h-12 w-12 text-red-600 mx-auto mb-4" />
          <p className="text-red-600 mb-4">No flashcards available for quiz</p>
          <Button onClick={onExit}>Go Back</Button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation Header */}
      <nav className="bg-white border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Button variant="ghost" size="sm" onClick={onExit} className="text-gray-600 hover:text-gray-900">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Exit Quiz
            </Button>
            <div className="flex items-center space-x-2">
              <Brain className="h-8 w-8 text-blue-600" />
              <span className="text-2xl font-bold text-gray-900">RAISE</span>
            </div>
          </div>
          
          {timeLimit > 0 && (
            <div className="flex items-center space-x-2">
              <Timer className={`h-4 w-4 ${timeLeft < 60 ? 'text-red-600' : 'text-gray-600'}`} />
              <span className={`font-mono ${timeLeft < 60 ? 'text-red-600 font-bold' : 'text-gray-600'}`}>
                {formatTime(timeLeft)}
              </span>
            </div>
          )}
        </div>
      </nav>

      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">{title}</h1>
            <p className="text-gray-600">Test your knowledge with flashcard questions</p>
          </div>

          {/* Progress */}
          <div className="mb-8">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm text-gray-600">Progress</span>
              <span className="text-sm font-medium">
                {currentIndex + 1} / {flashcards.length}
              </span>
            </div>
            <Progress value={progress} className="h-2" />
          </div>

          {/* Question Card */}
          <Card className="border-0 shadow-lg mb-8">
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-xl mb-2">
                    Question {currentIndex + 1}
                  </CardTitle>
                  <div className="flex gap-2">
                    <Badge variant="outline" className="capitalize">
                      {currentCard.difficulty}
                    </Badge>
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {/* Question */}
              <div className="mb-6">
                <Label className="text-lg font-medium text-gray-900 mb-3 block">
                  {currentCard.question}
                </Label>
              </div>

              {/* Answer Input */}
              {!showFeedback ? (
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="answer" className="text-sm font-medium text-gray-700">
                      Your Answer
                    </Label>
                    <Input
                      id="answer"
                      value={userAnswer}
                      onChange={(e) => setUserAnswer(e.target.value)}
                      placeholder="Type your answer here..."
                      className="mt-1"
                      onKeyPress={(e) => {
                        if (e.key === 'Enter' && userAnswer.trim()) {
                          handleSubmitAnswer()
                        }
                      }}
                      autoFocus
                    />
                  </div>
                  <div className="flex gap-3">
                    <Button
                      onClick={handleSubmitAnswer}
                      disabled={!userAnswer.trim()}
                      className="bg-blue-600 hover:bg-blue-700"
                    >
                      Submit Answer
                    </Button>
                    <Button
                      onClick={handleSkipQuestion}
                      variant="outline"
                      className="text-gray-600"
                    >
                      Skip Question
                    </Button>
                  </div>
                </div>
              ) : (
                /* Feedback */
                <div className="space-y-6">
                  {/* Feedback Message */}
                  <div className={`p-4 rounded-lg ${isCorrect ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
                    <div className="flex items-start space-x-3">
                      {isCorrect ? (
                        <CheckCircle className="h-6 w-6 text-green-600 mt-0.5" />
                      ) : (
                        <XCircle className="h-6 w-6 text-red-600 mt-0.5" />
                      )}
                      <div className="flex-1">
                        <div className={`font-medium ${isCorrect ? 'text-green-900' : 'text-red-900'}`}>
                          {isCorrect ? 'Correct!' : 'Incorrect'}
                        </div>
                        <div className={`text-sm mt-1 ${isCorrect ? 'text-green-700' : 'text-red-700'}`}>
                          {isCorrect 
                            ? 'Great job! Your answer is correct.' 
                            : 'Don\'t worry, keep learning!'
                          }
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Answer Comparison */}
                  <div className="space-y-3">
                    <div className="p-3 bg-gray-50 rounded-lg">
                      <div className="text-sm font-medium text-gray-700 mb-1">Your Answer:</div>
                      <div className="text-gray-900">{userAnswer || "No answer provided"}</div>
                    </div>
                    
                    {!isCorrect && (
                      <div className="p-3 bg-blue-50 rounded-lg">
                        <div className="text-sm font-medium text-blue-700 mb-1 flex items-center">
                          <Lightbulb className="h-4 w-4 mr-1" />
                          Correct Answer:
                        </div>
                        <div className="text-blue-900">{currentCard.answer}</div>
                      </div>
                    )}
                  </div>

                  {/* Next Button */}
                  <div className="flex justify-end">
                    <Button
                      onClick={handleNextQuestion}
                      className="bg-blue-600 hover:bg-blue-700"
                    >
                      {isLastQuestion ? (
                        <>
                          Complete Quiz
                          <CheckCircle className="h-4 w-4 ml-2" />
                        </>
                      ) : (
                        <>
                          Next Question
                          <ArrowRight className="h-4 w-4 ml-2" />
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Quiz Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card className="text-center p-4">
              <div className="text-2xl font-bold text-blue-600">{currentIndex + 1}</div>
              <div className="text-sm text-gray-600">Current Question</div>
            </Card>
            <Card className="text-center p-4">
              <div className="text-2xl font-bold text-green-600">
                {sessionResults.filter(r => r.isCorrect).length + (showFeedback && isCorrect ? 1 : 0)}
              </div>
              <div className="text-sm text-gray-600">Correct</div>
            </Card>
            <Card className="text-center p-4">
              <div className="text-2xl font-bold text-red-600">
                {sessionResults.filter(r => !r.isCorrect).length + (showFeedback && !isCorrect ? 1 : 0)}
              </div>
              <div className="text-sm text-gray-600">Incorrect</div>
            </Card>
            <Card className="text-center p-4">
              <div className="text-2xl font-bold text-gray-600">{flashcards.length}</div>
              <div className="text-sm text-gray-600">Total Questions</div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}