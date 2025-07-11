"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Brain, BookOpen, Target, Clock, ArrowRight } from "lucide-react"
import { apiService } from "@/lib/api"
import { Document } from "@/types/api"

interface QuizSetupProps {
  onStartQuiz: (deckId: string, questionCount: number, options: Record<string, unknown>) => void
  loading?: boolean
}

export function QuizSetup({ onStartQuiz, loading = false }: QuizSetupProps) {
  const [documents, setDocuments] = useState<Document[]>([])
  const [selectedDeck, setSelectedDeck] = useState("")
  const [questionCount, setQuestionCount] = useState("10")
  const [difficulty, setDifficulty] = useState("medium")
  const [timeLimit, setTimeLimit] = useState("300") // 5 minutes default
  const [loadingDocs, setLoadingDocs] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadDocuments = async () => {
      try {
        setLoadingDocs(true)
        const response = await apiService.listDocuments()
        if (response.success && response.data) {
          // Filter only completed documents
          const completedDocs = response.data.filter(doc => 
            doc.processing_status === 'completed' || doc.status === 'completed'
          )
          setDocuments(completedDocs)
          if (completedDocs.length > 0) {
            setSelectedDeck(completedDocs[0].document_id)
          }
        } else {
          throw new Error(response.message || 'Failed to load documents')
        }
      } catch (error) {
        console.error('Error loading documents:', error)
        setError(error instanceof Error ? error.message : 'Failed to load documents')
      } finally {
        setLoadingDocs(false)
      }
    }

    loadDocuments()
  }, [])

  const handleStartQuiz = () => {
    if (!selectedDeck) {
      setError('Please select a document')
      return
    }

    const count = questionCount === "all" ? 999 : parseInt(questionCount)
    const options = {
      question_count: count,
      difficulty,
      time_limit: parseInt(timeLimit),
      bloom_distribution: {
        remember: 2,
        understand: 2, 
        apply: 2,
        analyze: 2,
        evaluate: 1,
        create: 1
      }
    }

    onStartQuiz(selectedDeck, count, options)
  }

  const questionCountOptions = [
    { value: "5", label: "5 Questions", icon: "🎯" },
    { value: "10", label: "10 Questions", icon: "📝" },
    { value: "15", label: "15 Questions", icon: "📚" },
    { value: "20", label: "20 Questions", icon: "🎓" },
    { value: "all", label: "All Available", icon: "🌟" }
  ]

  const difficultyOptions = [
    { value: "easy", label: "Easy", description: "Basic concepts and definitions", color: "text-green-600" },
    { value: "medium", label: "Medium", description: "Moderate understanding required", color: "text-yellow-600" },
    { value: "hard", label: "Hard", description: "Advanced analysis and application", color: "text-red-600" }
  ]

  const timeLimitOptions = [
    { value: "180", label: "3 minutes" },
    { value: "300", label: "5 minutes" },
    { value: "600", label: "10 minutes" },
    { value: "900", label: "15 minutes" },
    { value: "1800", label: "30 minutes" },
    { value: "0", label: "No time limit" }
  ]

  if (loadingDocs) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Brain className="h-12 w-12 text-blue-600 mx-auto mb-4 animate-spin" />
          <p className="text-gray-600">Loading your documents...</p>
        </div>
      </div>
    )
  }

  if (error && documents.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <CardTitle className="text-red-600">Error Loading Documents</CardTitle>
            <CardDescription>{error}</CardDescription>
          </CardHeader>
          <CardContent>
            <Button 
              onClick={() => window.location.reload()} 
              className="w-full"
            >
              Try Again
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (documents.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <CardTitle>No Documents Available</CardTitle>
            <CardDescription>
              You need to upload and process at least one document before you can start a quiz.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button 
              onClick={() => window.location.href = '/upload'} 
              className="w-full"
            >
              Upload Document
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="flex items-center justify-center mb-4">
              <Brain className="h-12 w-12 text-blue-600 mr-3" />
              <h1 className="text-4xl font-bold text-gray-900">Quiz Mode</h1>
            </div>
            <p className="text-lg text-gray-600">
              Test your knowledge with AI-generated questions based on your documents
            </p>
          </div>

          <div className="grid lg:grid-cols-3 gap-8">
            {/* Document Selection */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <BookOpen className="h-5 w-5 mr-2" />
                  Select Document
                </CardTitle>
                <CardDescription>
                  Choose which document you want to be quizzed on
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Select value={selectedDeck} onValueChange={setSelectedDeck}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a document" />
                  </SelectTrigger>
                  <SelectContent>
                    {documents.map((doc) => (
                      <SelectItem key={doc.document_id} value={doc.document_id}>
                        <div className="flex items-center">
                          <span className="truncate">{doc.filename}</span>
                          <span className="ml-2 text-xs text-gray-500">
                            ({(doc.file_size / 1024).toFixed(1)} KB)
                          </span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </CardContent>
            </Card>

            {/* Quiz Settings */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Target className="h-5 w-5 mr-2" />
                  Quiz Settings
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Question Count */}
                <div>
                  <Label className="text-sm font-medium mb-3 block">Number of Questions</Label>
                  <RadioGroup value={questionCount} onValueChange={setQuestionCount}>
                    {questionCountOptions.map((option) => (
                      <div key={option.value} className="flex items-center space-x-3">
                        <RadioGroupItem value={option.value} id={`count-${option.value}`} />
                        <Label htmlFor={`count-${option.value}`} className="flex-1 cursor-pointer">
                          <span className="mr-2">{option.icon}</span>
                          {option.label}
                        </Label>
                      </div>
                    ))}
                  </RadioGroup>
                </div>

                {/* Difficulty Level */}
                <div>
                  <Label className="text-sm font-medium mb-3 block">Difficulty Level</Label>
                  <RadioGroup value={difficulty} onValueChange={setDifficulty}>
                    {difficultyOptions.map((option) => (
                      <div key={option.value} className="flex items-center space-x-3">
                        <RadioGroupItem value={option.value} id={`diff-${option.value}`} />
                        <Label htmlFor={`diff-${option.value}`} className="flex-1 cursor-pointer">
                          <div>
                            <div className={`font-medium ${option.color}`}>
                              {option.label}
                            </div>
                            <div className="text-xs text-gray-500">
                              {option.description}
                            </div>
                          </div>
                        </Label>
                      </div>
                    ))}
                  </RadioGroup>
                </div>

                {/* Time Limit */}
                <div>
                  <Label className="text-sm font-medium mb-3 block">
                    <Clock className="h-4 w-4 inline mr-1" />
                    Time Limit
                  </Label>
                  <Select value={timeLimit} onValueChange={setTimeLimit}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {timeLimitOptions.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Quiz Preview */}
          {selectedDeck && (
            <Card className="mt-8">
              <CardHeader>
                <CardTitle>Quiz Preview</CardTitle>
                <CardDescription>
                  Your quiz will be generated based on the following settings
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-4 gap-4 text-center">
                  <div className="p-4 bg-blue-50 rounded-lg">
                    <BookOpen className="h-6 w-6 text-blue-600 mx-auto mb-2" />
                    <div className="font-medium text-blue-900">Document</div>
                    <div className="text-sm text-blue-700 truncate">
                      {documents.find(d => d.document_id === selectedDeck)?.filename}
                    </div>
                  </div>
                  <div className="p-4 bg-green-50 rounded-lg">
                    <Target className="h-6 w-6 text-green-600 mx-auto mb-2" />
                    <div className="font-medium text-green-900">Questions</div>
                    <div className="text-sm text-green-700">
                      {questionCount === "all" ? "All available" : `${questionCount} questions`}
                    </div>
                  </div>
                  <div className="p-4 bg-yellow-50 rounded-lg">
                    <Brain className="h-6 w-6 text-yellow-600 mx-auto mb-2" />
                    <div className="font-medium text-yellow-900">Difficulty</div>
                    <div className="text-sm text-yellow-700 capitalize">{difficulty}</div>
                  </div>
                  <div className="p-4 bg-purple-50 rounded-lg">
                    <Clock className="h-6 w-6 text-purple-600 mx-auto mb-2" />
                    <div className="font-medium text-purple-900">Time Limit</div>
                    <div className="text-sm text-purple-700">
                      {timeLimit === "0" ? "No limit" : `${Math.floor(parseInt(timeLimit) / 60)} minutes`}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Start Quiz Button */}
          <div className="mt-8 text-center">
            {error && (
              <p className="text-red-600 mb-4 text-sm">{error}</p>
            )}
            <Button
              onClick={handleStartQuiz}
              disabled={!selectedDeck || loading}
              size="lg"
              className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3"
            >
              {loading ? (
                <>
                  <Brain className="h-5 w-5 mr-2 animate-spin" />
                  Generating Quiz...
                </>
              ) : (
                <>
                  Start Quiz
                  <ArrowRight className="h-5 w-5 ml-2" />
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}