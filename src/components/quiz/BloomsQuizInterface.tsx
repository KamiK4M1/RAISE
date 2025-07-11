"use client"

import { useState, useEffect, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { 
  Brain, 
  ArrowLeft, 
  CheckCircle, 
  XCircle, 
  Clock, 
  Award,
  BookOpen,
  Target,
  Lightbulb,
  Zap,
  Star,
  TrendingUp
} from "lucide-react"

import { apiService } from "@/lib/api"
import { QuizOptions } from "@/types/api"

// Types
interface QuizQuestion {
  question_id: string
  question: string
  options: string[]
  correct_answer: string
  explanation: string
  bloom_level: string
  difficulty: string
  points: number
}

interface Quiz {
  quiz_id: string
  document_id: string
  title: string
  description: string
  questions: QuizQuestion[]
  total_points: number
  time_limit?: number
  bloom_distribution: Record<string, number>
}

interface QuizResults {
  attempt_id: string
  quiz_id: string
  score: number
  percentage: number
  total_points: number
  time_taken: number
  bloom_scores: Record<string, number>
  question_results: Array<{
    question_id: string
    question: string
    user_answer: string
    correct_answer: string
    is_correct: boolean
    points_earned: number
    points_possible: number
    bloom_level: string
    explanation: string
  }>
  recommendations: string[]
}

interface BloomsQuizInterfaceProps {
  documentId: string
  onBack?: () => void
}

// Bloom's Taxonomy configuration
const BLOOMS_CONFIG = {
  remember: {
    label: "จำ (Remember)",
    description: "การระลึกและการจำข้อเท็จจริง",
    icon: Brain,
    color: "bg-blue-500",
    lightColor: "bg-blue-50 text-blue-700",
    examples: ["นิยาม", "รายชื่อ", "วันที่", "สูตร"]
  },
  understand: {
    label: "เข้าใจ (Understand)", 
    description: "การตีความและการอธิบาย",
    icon: BookOpen,
    color: "bg-green-500",
    lightColor: "bg-green-50 text-green-700",
    examples: ["อธิบาย", "สรุป", "แปลความ", "เปรียบเทียบ"]
  },
  apply: {
    label: "ประยุกต์ (Apply)",
    description: "การนำความรู้ไปใช้ในสถานการณ์ใหม่",
    icon: Target,
    color: "bg-yellow-500", 
    lightColor: "bg-yellow-50 text-yellow-700",
    examples: ["ใช้", "แก้ปัญหา", "คำนวณ", "ดำเนินการ"]
  },
  analyze: {
    label: "วิเคราะห์ (Analyze)",
    description: "การแยกแยะและการเปรียบเทียบ",
    icon: Lightbulb,
    color: "bg-orange-500",
    lightColor: "bg-orange-50 text-orange-700", 
    examples: ["วิเคราะห์", "เปรียบเทียบ", "แยกแยะ", "ตรวจสอบ"]
  },
  evaluate: {
    label: "ประเมิน (Evaluate)",
    description: "การตัดสินใจและการวิจารณ์",
    icon: Star,
    color: "bg-purple-500",
    lightColor: "bg-purple-50 text-purple-700",
    examples: ["ประเมิน", "วิจารณ์", "ตัดสิน", "เลือก"]
  },
  create: {
    label: "สร้างสรรค์ (Create)",
    description: "การสร้างใหม่และการออกแบบ",
    icon: Zap,
    color: "bg-pink-500",
    lightColor: "bg-pink-50 text-pink-700",
    examples: ["สร้าง", "ออกแบบ", "วางแผน", "ประดิษฐ์"]
  }
}

export function BloomsQuizInterface({ documentId, onBack }: BloomsQuizInterfaceProps) {
  const [quiz, setQuiz] = useState<Quiz | null>(null)
  const [currentQuestion, setCurrentQuestion] = useState(0)
  const [selectedAnswer, setSelectedAnswer] = useState("")
  const [answers, setAnswers] = useState<string[]>([])
  const [showResults, setShowResults] = useState(false)
  const [quizResults, setQuizResults] = useState<QuizResults | null>(null)
  const [timeLeft, setTimeLeft] = useState(0)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [startTime, setStartTime] = useState(Date.now())

  const handleSubmitQuiz = useCallback(async () => {
    if (!quiz) return
    
    try {
      setSubmitting(true)
      const timeTaken = Math.floor((Date.now() - startTime) / 1000)
      
      const response = await apiService.submitQuiz(quiz.quiz_id, {
        answers,
        time_taken: timeTaken
      })
      
      if (response.success && response.data) {
        const results = response.data as unknown as QuizResults
        setQuizResults({
          ...results,
          attempt_id: results.attempt_id || '',
          bloom_scores: results.bloom_scores || {},
          recommendations: results.recommendations || [],
          question_results: (results.question_results || []).map(qr => ({
            question_id: qr.question_id || '',
            question: qr.question || '',
            user_answer: qr.user_answer || '',
            correct_answer: qr.correct_answer || '',
            is_correct: qr.is_correct || false,
            points_earned: qr.points_earned || 0,
            points_possible: qr.points_possible || 0,
            bloom_level: qr.bloom_level || '',
            explanation: qr.explanation || ''
          }))
        })
        setShowResults(true)
      } else {
        throw new Error(response.message || 'Failed to submit quiz')
      }
    } catch (error) {
      console.error('Error submitting quiz:', error)
      setError(error instanceof Error ? error.message : 'ไม่สามารถส่งคำตอบได้')
    } finally {
      setSubmitting(false)
    }
  }, [quiz, startTime, answers])

  // Generate quiz with Bloom's Taxonomy distribution
  useEffect(() => {
    const abortController = new AbortController()
    
    const loadQuiz = async () => {
      if (abortController.signal.aborted) return
      
      try {
        setLoading(true)
        setError(null)
        
        const response = await apiService.generateQuiz(documentId, {
          question_count: 15,
          bloom_distribution: {
            remember: 3,
            understand: 3,
            apply: 3,
            analyze: 2,
            evaluate: 2,
            create: 2
          },
          difficulty: "medium",
          time_limit: 1200 // 20 minutes
        } as QuizOptions)
        
        if (abortController.signal.aborted) return
        
        if (response.success && response.data) {
          setQuiz({
            ...response.data,
            description: response.data.description || ''
          })
          setTimeLeft(response.data.time_limit || 1200)
          setStartTime(Date.now())
          setAnswers(new Array(response.data.questions.length).fill(""))
        } else {
          throw new Error(response.message || 'Failed to generate quiz')
        }
      } catch (error) {
        if (abortController.signal.aborted) return
        console.error('Error generating quiz:', error)
        setError(error instanceof Error ? error.message : 'ไม่สามารถสร้างแบบทดสอบได้')
      } finally {
        if (!abortController.signal.aborted) {
          setLoading(false)
        }
      }
    }

    if (documentId) {
      loadQuiz()
    }

    return () => {
      abortController.abort()
    }
  }, [documentId])

  // Timer countdown
  useEffect(() => {
    if (timeLeft > 0 && !showResults && !loading) {
      const timer = setTimeout(() => setTimeLeft(timeLeft - 1), 1000)
      return () => clearTimeout(timer)
    } else if (timeLeft === 0 && quiz && !showResults) {
      handleSubmitQuiz()
    }
  }, [timeLeft, showResults, loading, quiz, handleSubmitQuiz])

  const handleAnswerSelect = (value: string) => {
    setSelectedAnswer(value)
    const newAnswers = [...answers]
    newAnswers[currentQuestion] = value
    setAnswers(newAnswers)
  }

  const handleNextQuestion = () => {
    if (quiz && currentQuestion < quiz.questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1)
      setSelectedAnswer(answers[currentQuestion + 1] || "")
    } else {
      handleSubmitQuiz()
    }
  }

  const handlePreviousQuestion = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(currentQuestion - 1)
      setSelectedAnswer(answers[currentQuestion - 1] || "")
    }
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, "0")}`
  }

  const getBloomConfig = (level: string) => {
    return BLOOMS_CONFIG[level as keyof typeof BLOOMS_CONFIG] || BLOOMS_CONFIG.remember
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Brain className="h-12 w-12 text-blue-600 mx-auto mb-4 animate-spin" />
          <p className="text-gray-600">กำลังสร้างแบบทดสอบตาม Bloom&apos;s Taxonomy...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <XCircle className="h-12 w-12 text-red-600 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">เกิดข้อผิดพลาด</h2>
          <p className="text-red-600 mb-4">{error}</p>
          <div className="space-x-4">
            <Button onClick={() => setError(null)}>ลองใหม่</Button>
            {onBack && (
              <Button variant="outline" onClick={onBack}>กลับ</Button>
            )}
          </div>
        </div>
      </div>
    )
  }

  if (!quiz) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <XCircle className="h-12 w-12 text-gray-600 mx-auto mb-4" />
          <p className="text-gray-600 mb-4">ไม่พบแบบทดสอบ</p>
          {onBack && (
            <Button onClick={onBack}>กลับ</Button>
          )}
        </div>
      </div>
    )
  }

  // Results view
  if (showResults && quizResults) {
    return (
      <div className="min-h-screen bg-gray-50">
        <nav className="bg-white border-b">
          <div className="container mx-auto px-4 py-4 flex items-center justify-between">
            <div className="flex items-center space-x-4">
              {onBack && (
                <Button variant="ghost" size="sm" onClick={onBack}>
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  กลับ
                </Button>
              )}
              <div className="flex items-center space-x-2">
                <Brain className="h-8 w-8 text-blue-600" />
                <span className="text-2xl font-bold text-gray-900">RAISE</span>
              </div>
            </div>
          </div>
        </nav>

        <div className="container mx-auto px-4 py-8">
          <div className="max-w-6xl mx-auto">
            {/* Overall Results */}
            <Card className="border-0 shadow-lg mb-8">
              <CardHeader className="text-center">
                <Award className="h-16 w-16 text-yellow-500 mx-auto mb-4" />
                <CardTitle className="text-3xl">ผลการทำแบบทดสอบ</CardTitle>
                <CardDescription className="text-lg">{quiz.title}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-4 gap-6 mb-8">
                  <div className="text-center p-4 bg-blue-50 rounded-lg">
                    <div className="text-4xl font-bold text-blue-600 mb-2">{quizResults.percentage}%</div>
                    <div className="text-blue-700">คะแนนรวม</div>
                  </div>
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <div className="text-4xl font-bold text-green-600 mb-2">
                      {quizResults.question_results.filter(q => q.is_correct).length}
                    </div>
                    <div className="text-green-700">ข้อที่ถูก</div>
                  </div>
                  <div className="text-center p-4 bg-red-50 rounded-lg">
                    <div className="text-4xl font-bold text-red-600 mb-2">
                      {quizResults.question_results.filter(q => !q.is_correct).length}
                    </div>
                    <div className="text-red-700">ข้อที่ผิด</div>
                  </div>
                  <div className="text-center p-4 bg-purple-50 rounded-lg">
                    <div className="text-4xl font-bold text-purple-600 mb-2">
                      {Math.floor(quizResults.time_taken / 60)}:{(quizResults.time_taken % 60).toString().padStart(2, '0')}
                    </div>
                    <div className="text-purple-700">เวลาที่ใช้</div>
                  </div>
                </div>

                {/* Bloom's Taxonomy Performance */}
                <div className="mb-8">
                  <h3 className="text-xl font-bold mb-4 flex items-center">
                    <TrendingUp className="h-5 w-5 mr-2" />
                    ผลงานตาม Bloom&apos;s Taxonomy
                  </h3>
                  <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {Object.entries(quizResults.bloom_scores).map(([level, score]) => {
                      const config = getBloomConfig(level)
                      const IconComponent = config.icon
                      return (
                        <Card key={level} className="border">
                          <CardContent className="p-4">
                            <div className="flex items-center space-x-3 mb-2">
                              <div className={`p-2 rounded-lg ${config.color}`}>
                                <IconComponent className="h-4 w-4 text-white" />
                              </div>
                              <div>
                                <div className="font-medium">{config.label}</div>
                                <div className="text-sm text-gray-500">{config.description}</div>
                              </div>
                            </div>
                            <div className="flex items-center justify-between">
                              <Progress value={score} className="flex-1 mr-3" />
                              <span className="text-lg font-bold">{Math.round(score)}%</span>
                            </div>
                          </CardContent>
                        </Card>
                      )
                    })}
                  </div>
                </div>

                {/* Recommendations */}
                {quizResults.recommendations.length > 0 && (
                  <div className="mb-8 p-6 bg-amber-50 rounded-lg border border-amber-200">
                    <h3 className="text-lg font-bold text-amber-800 mb-3">คำแนะนำสำหรับการศึกษาต่อ</h3>
                    <ul className="space-y-2">
                      {quizResults.recommendations.map((recommendation, index) => (
                        <li key={index} className="flex items-start space-x-2 text-amber-700">
                          <Lightbulb className="h-4 w-4 mt-0.5 flex-shrink-0" />
                          <span>{recommendation}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Detailed Results */}
                <div className="space-y-4">
                  <h3 className="text-xl font-bold mb-4">รายละเอียดคำตอบ</h3>
                  {quizResults.question_results.map((result, index) => {
                    const config = getBloomConfig(result.bloom_level)
                    const IconComponent = config.icon
                    return (
                      <Card key={result.question_id} className="border">
                        <CardContent className="p-6">
                          <div className="flex items-start space-x-4">
                            {result.is_correct ? (
                              <CheckCircle className="h-6 w-6 text-green-600 mt-1 flex-shrink-0" />
                            ) : (
                              <XCircle className="h-6 w-6 text-red-600 mt-1 flex-shrink-0" />
                            )}
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center justify-between mb-3">
                                <div className="flex items-center space-x-3">
                                  <span className="text-sm font-medium text-gray-500">คำถามที่ {index + 1}</span>
                                  <Badge className={config.lightColor}>
                                    <IconComponent className="h-3 w-3 mr-1" />
                                    {config.label}
                                  </Badge>
                                </div>
                                <div className="text-sm text-gray-500">
                                  {result.points_earned}/{result.points_possible} คะแนน
                                </div>
                              </div>
                              
                              <p className="font-medium text-gray-900 mb-4 leading-relaxed">
                                {result.question}
                              </p>
                              
                              <div className="space-y-3 text-sm">
                                <div>
                                  <span className="font-medium text-gray-700">คำตอบของคุณ: </span>
                                  <span className={result.is_correct ? "text-green-700 font-medium" : "text-red-700 font-medium"}>
                                    {result.user_answer || "ไม่ได้ตอบ"}
                                  </span>
                                </div>
                                
                                {!result.is_correct && (
                                  <div>
                                    <span className="font-medium text-gray-700">คำตอบที่ถูกต้อง: </span>
                                    <span className="text-green-700 font-medium">{result.correct_answer}</span>
                                  </div>
                                )}
                                
                                <div className="p-3 bg-gray-50 rounded border-l-4 border-blue-400">
                                  <span className="font-medium text-gray-700">คำอธิบาย: </span>
                                  <span className="text-gray-600">{result.explanation}</span>
                                </div>
                              </div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    )
                  })}
                </div>

                <div className="mt-8 text-center space-x-4">
                  <Button onClick={() => window.location.reload()} className="bg-blue-600 hover:bg-blue-700">
                    ทำแบบทดสอบใหม่
                  </Button>
                  {onBack && (
                    <Button variant="outline" onClick={onBack}>
                      กลับหน้าหลัก
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    )
  }

  // Quiz taking view
  const progress = ((currentQuestion + 1) / quiz.questions.length) * 100
  const currentQ = quiz.questions[currentQuestion]
  const config = getBloomConfig(currentQ.bloom_level)
  const IconComponent = config.icon

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            {onBack && (
              <Button variant="ghost" size="sm" onClick={onBack}>
                <ArrowLeft className="h-4 w-4 mr-2" />
                กลับ
              </Button>
            )}
            <div className="flex items-center space-x-2">
              <Brain className="h-8 w-8 text-blue-600" />
              <span className="text-2xl font-bold text-gray-900">RAISE</span>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 text-gray-600">
              <Clock className="h-4 w-4" />
              <span className={`font-mono text-lg ${timeLeft < 60 ? 'text-red-600' : ''}`}>
                {formatTime(timeLeft)}
              </span>
            </div>
          </div>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">{quiz.title}</h1>
            <p className="text-gray-600">แบบทดสอบที่ครอบคลุมทุกระดับตาม Bloom&apos;s Taxonomy</p>
          </div>

          {/* Progress */}
          <div className="mb-8">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm text-gray-600">ความคืบหน้า</span>
              <span className="text-sm font-medium">
                {currentQuestion + 1} / {quiz.questions.length}
              </span>
            </div>
            <Progress value={progress} className="h-3" />
          </div>

          {/* Question */}
          <Card className="border-0 shadow-lg mb-8">
            <CardHeader>
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-3">
                    <Badge className={config.lightColor}>
                      <IconComponent className="h-4 w-4 mr-2" />
                      {config.label}
                    </Badge>
                    <Badge variant="outline" className="capitalize">
                      {currentQ.difficulty}
                    </Badge>
                    <Badge variant="outline">
                      {currentQ.points} คะแนน
                    </Badge>
                  </div>
                  <CardTitle className="text-xl mb-2">คำถามที่ {currentQuestion + 1}</CardTitle>
                  <CardDescription className="text-base">{config.description}</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <h2 className="text-lg font-medium mb-6 leading-relaxed">{currentQ.question}</h2>

              <RadioGroup value={selectedAnswer} onValueChange={handleAnswerSelect}>
                <div className="space-y-4">
                  {currentQ.options.map((option, index) => (
                    <div
                      key={index}
                      className="flex items-center space-x-3 p-4 border rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      <RadioGroupItem value={option} id={`option-${index}`} />
                      <Label htmlFor={`option-${index}`} className="flex-1 cursor-pointer text-base">
                        {option}
                      </Label>
                    </div>
                  ))}
                </div>
              </RadioGroup>
            </CardContent>
          </Card>

          {/* Navigation */}
          <div className="flex justify-between">
            <Button
              variant="outline"
              onClick={handlePreviousQuestion}
              disabled={currentQuestion === 0}
              className="bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              คำถามก่อนหน้า
            </Button>

            <Button 
              onClick={handleNextQuestion} 
              disabled={!selectedAnswer || submitting}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {submitting ? (
                "กำลังส่ง..."
              ) : currentQuestion === quiz.questions.length - 1 ? (
                "ส่งคำตอบ"
              ) : (
                "คำถามถัดไป"
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}