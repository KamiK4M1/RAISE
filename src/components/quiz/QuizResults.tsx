"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { 
  Award, 
  Brain, 
  CheckCircle, 
  XCircle, 
  RotateCcw,
  Home,
  TrendingUp,
  Clock,
  Target,
  Star
} from "lucide-react"
import { Flashcard } from "@/types/api"

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

interface QuizResultsProps {
  results: QuizSessionResults
  onRetry: () => void
  onBackToSetup: () => void
  title?: string
}

export function QuizResults({ 
  results, 
  onRetry, 
  onBackToSetup, 
  title = "Quiz Results" 
}: QuizResultsProps) {
  const [showDetailedResults, setShowDetailedResults] = useState(false)

  const {
    totalQuestions,
    correctAnswers,
    incorrectAnswers,
    score,
    timeTaken,
    results: questionResults
  } = results

  const averageTimePerQuestion = Math.round(timeTaken / totalQuestions / 1000)
  const passedQuiz = score >= 70

  const formatTime = (milliseconds: number) => {
    const seconds = Math.floor(milliseconds / 1000)
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`
  }

  const getScoreColor = (score: number) => {
    if (score >= 90) return "text-green-600"
    if (score >= 70) return "text-blue-600"
    if (score >= 50) return "text-yellow-600"
    return "text-red-600"
  }

  const getScoreBadge = (score: number) => {
    if (score >= 90) return { label: "Excellent", color: "bg-green-100 text-green-800" }
    if (score >= 70) return { label: "Good", color: "bg-blue-100 text-blue-800" }
    if (score >= 50) return { label: "Fair", color: "bg-yellow-100 text-yellow-800" }
    return { label: "Needs Improvement", color: "bg-red-100 text-red-800" }
  }

  const scoreBadge = getScoreBadge(score)

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="flex items-center justify-center mb-4">
              {passedQuiz ? (
                <Award className="h-16 w-16 text-yellow-500" />
              ) : (
                <Brain className="h-16 w-16 text-blue-600" />
              )}
            </div>
            <h1 className="text-4xl font-bold text-gray-900 mb-2">Quiz Complete!</h1>
            <p className="text-lg text-gray-600">{title}</p>
          </div>

          {/* Score Overview */}
          <Card className="border-0 shadow-lg mb-8">
            <CardHeader className="text-center">
              <div className={`text-6xl font-bold ${getScoreColor(score)} mb-2`}>
                {score}%
              </div>
              <Badge className={scoreBadge.color}>{scoreBadge.label}</Badge>
              <CardDescription className="text-lg mt-2">
                {passedQuiz 
                  ? "Congratulations! You passed the quiz!" 
                  : "Keep studying and try again!"
                }
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-4 gap-6">
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <CheckCircle className="h-8 w-8 text-green-600 mx-auto mb-2" />
                  <div className="text-2xl font-bold text-green-600">{correctAnswers}</div>
                  <div className="text-green-700 text-sm">Correct</div>
                </div>
                <div className="text-center p-4 bg-red-50 rounded-lg">
                  <XCircle className="h-8 w-8 text-red-600 mx-auto mb-2" />
                  <div className="text-2xl font-bold text-red-600">{incorrectAnswers}</div>
                  <div className="text-red-700 text-sm">Incorrect</div>
                </div>
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <Target className="h-8 w-8 text-blue-600 mx-auto mb-2" />
                  <div className="text-2xl font-bold text-blue-600">{totalQuestions}</div>
                  <div className="text-blue-700 text-sm">Total Questions</div>
                </div>
                <div className="text-center p-4 bg-purple-50 rounded-lg">
                  <Clock className="h-8 w-8 text-purple-600 mx-auto mb-2" />
                  <div className="text-2xl font-bold text-purple-600">{averageTimePerQuestion}s</div>
                  <div className="text-purple-700 text-sm">Avg. per Question</div>
                </div>
              </div>

              {/* Performance Breakdown */}
              <div className="mt-6">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium text-gray-700">Performance</span>
                  <span className="text-sm text-gray-600">
                    {correctAnswers} / {totalQuestions} correct
                  </span>
                </div>
                <Progress value={(correctAnswers / totalQuestions) * 100} className="h-3" />
              </div>

              {/* Time Stats */}
              <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Total Time:</span>
                  <span className="font-medium">{formatTime(timeTaken)}</span>
                </div>
                <div className="flex items-center justify-between text-sm mt-1">
                  <span className="text-gray-600">Average per Question:</span>
                  <span className="font-medium">{averageTimePerQuestion} seconds</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Action Buttons */}
          <div className="text-center mb-8">
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button
                onClick={onRetry}
                size="lg"
                className="bg-blue-600 hover:bg-blue-700"
              >
                <RotateCcw className="h-5 w-5 mr-2" />
                Try Again
              </Button>
              <Button
                onClick={onBackToSetup}
                variant="outline"
                size="lg"
                className="bg-white"
              >
                <Home className="h-5 w-5 mr-2" />
                New Quiz
              </Button>
            </div>
          </div>

          {/* Detailed Results Toggle */}
          <div className="text-center mb-6">
            <Button
              onClick={() => setShowDetailedResults(!showDetailedResults)}
              variant="ghost"
              className="text-blue-600 hover:text-blue-700"
            >
              {showDetailedResults ? "Hide" : "Show"} Detailed Results
              <TrendingUp className="h-4 w-4 ml-2" />
            </Button>
          </div>

          {/* Detailed Results */}
          {showDetailedResults && (
            <Card className="border-0 shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Star className="h-5 w-5 mr-2" />
                  Question by Question Review
                </CardTitle>
                <CardDescription>
                  Review each question to understand your performance
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {questionResults.map((result, index) => (
                    <Card key={index} className="border">
                      <CardContent className="p-4">
                        <div className="flex items-start space-x-3">
                          {result.isCorrect ? (
                            <CheckCircle className="h-5 w-5 text-green-600 mt-1 flex-shrink-0" />
                          ) : (
                            <XCircle className="h-5 w-5 text-red-600 mt-1 flex-shrink-0" />
                          )}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <p className="font-medium text-gray-900 mb-2">
                                  <span className="text-sm text-gray-500 mr-2">Q{index + 1}:</span>
                                  {result.flashcard.question}
                                </p>
                                <div className="space-y-2 text-sm">
                                  <div>
                                    <span className="font-medium text-gray-700">Your Answer: </span>
                                    <span className={result.isCorrect ? "text-green-700" : "text-red-700"}>
                                      {result.userAnswer || "No answer provided"}
                                    </span>
                                  </div>
                                  {!result.isCorrect && (
                                    <div>
                                      <span className="font-medium text-gray-700">Correct Answer: </span>
                                      <span className="text-green-700">{result.flashcard.answer}</span>
                                    </div>
                                  )}
                                </div>
                              </div>
                              <div className="flex flex-col items-end text-xs text-gray-500 ml-4">
                                <Badge variant="outline" className="mb-1 capitalize">
                                  {result.flashcard.difficulty}
                                </Badge>
                                <span>{formatTime(result.timeTaken)}</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>

                {/* Summary Stats */}
                <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-3">Summary by Difficulty</h4>
                  <div className="grid grid-cols-3 gap-4 text-center">
                    {['easy', 'medium', 'hard'].map((difficulty) => {
                      const difficultyResults = questionResults.filter(r => 
                        r.flashcard.difficulty === difficulty
                      )
                      const correct = difficultyResults.filter(r => r.isCorrect).length
                      const total = difficultyResults.length
                      const percentage = total > 0 ? Math.round((correct / total) * 100) : 0

                      return (
                        <div key={difficulty} className="p-3 bg-white rounded border">
                          <div className="text-lg font-bold text-gray-900">{percentage}%</div>
                          <div className="text-sm text-gray-600 capitalize">{difficulty}</div>
                          <div className="text-xs text-gray-500">{correct}/{total}</div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}