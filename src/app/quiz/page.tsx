"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Label } from "@/components/ui/label"
import { Brain, ArrowLeft, CheckCircle, XCircle, Clock, Award } from "lucide-react"
import Link from "next/link"
import { apiService } from "@/lib/api"
import { Quiz, QuizQuestion, QuizResults } from "@/types/api"

export default function QuizPage() {
  const [quiz, setQuiz] = useState<Quiz | null>(null)
  const [currentQuestion, setCurrentQuestion] = useState(0)
  const [selectedAnswer, setSelectedAnswer] = useState("")
  const [answers, setAnswers] = useState<string[]>([])
  const [showResults, setShowResults] = useState(false)
  const [quizResults, setQuizResults] = useState<QuizResults | null>(null)
  const [timeLeft, setTimeLeft] = useState(300) // 5 minutes
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [startTime, setStartTime] = useState(Date.now())
  
  // Get document ID from URL or use default for demo
  const documentId = "demo-document" // This should come from router params in real app

  useEffect(() => {
    const loadQuiz = async () => {
      try {
        setLoading(true);
        const response = await apiService.generateQuiz(documentId, { question_count: 5, bloom_distribution: {}, difficulty: 'medium' });
        if (response.success && response.data) {
          setQuiz(response.data);
          setTimeLeft(response.data.time_limit || 300);
          setStartTime(Date.now());
        } else {
          throw new Error(response.message || 'Failed to load quiz');
        }
      } catch (error) {
        console.error('Error loading quiz:', error);
        const errorMessage = error instanceof Error ? error.message : 'ไม่สามารถโหลดแบบทดสอบได้';
        setError(errorMessage);
      } finally {
        setLoading(false);
      }
    };

    loadQuiz();
  }, [documentId]);

  const handleAnswerSelect = (value: string) => {
    setSelectedAnswer(value)
  }

  const handleNextQuestion = async () => {
    const newAnswers = [...answers];
    newAnswers[currentQuestion] = selectedAnswer;
    setAnswers(newAnswers);

    if (quiz && currentQuestion < quiz.questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
      setSelectedAnswer("");
    } else if (quiz) {
      const timeTaken = (Date.now() - startTime) / 1000;
      const response = await apiService.submitQuiz(quiz.quiz_id, newAnswers, timeTaken);
      if(response.success && response.data) {
        setQuizResults(response.data);
      }
      setShowResults(true);
    }
  };

  const calculateScore = () => {
    if (!quiz) return { correct: 0, total: 0, percentage: 0 }
    let correct = 0
    answers.forEach((answer, index) => {
      if (answer === quiz.questions[index].correct_answer) {
        correct++
      }
    })
    return { correct, total: quiz.questions.length, percentage: Math.round((correct / quiz.questions.length) * 100) }
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, "0")}`
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Brain className="h-12 w-12 text-blue-600 mx-auto mb-4 animate-spin" />
          <p className="text-gray-600">กำลังโหลดแบบทดสอบ...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <XCircle className="h-12 w-12 text-red-600 mx-auto mb-4" />
          <p className="text-red-600 mb-4">{error}</p>
          <Link href="/dashboard">
            <Button>กลับหน้าหลัก</Button>
          </Link>
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
          <Link href="/dashboard">
            <Button>กลับหน้าหลัก</Button>
          </Link>
        </div>
      </div>
    )
  }

  if (showResults) {
    const score = calculateScore()
    return (
      <div className="min-h-screen bg-gray-50">
        <nav className="bg-white border-b">
          <div className="container mx-auto px-4 py-4 flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link href="/dashboard">
                <Button variant="ghost" size="sm" className="text-gray-600 hover:text-gray-900">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  กลับ
                </Button>
              </Link>
              <div className="flex items-center space-x-2">
                <Brain className="h-8 w-8 text-blue-600" />
                <span className="text-2xl font-bold text-gray-900">RAISE</span>
              </div>
            </div>
          </div>
        </nav>

        <div className="container mx-auto px-4 py-8">
          <div className="max-w-4xl mx-auto">
            <Card className="border-0 shadow-lg text-center">
              <CardHeader>
                <Award className="h-16 w-16 text-yellow-500 mx-auto mb-4" />
                <CardTitle className="text-3xl">ผลการทำแบบทดสอบ</CardTitle>
                <CardDescription className="text-lg">{quiz?.title}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-3 gap-6 mb-8">
                  <div className="text-center">
                    <div className="text-4xl font-bold text-green-600 mb-2">{score.correct}</div>
                    <div className="text-gray-600">ข้อที่ถูก</div>
                  </div>
                  <div className="text-center">
                    <div className="text-4xl font-bold text-red-600 mb-2">{score.total - score.correct}</div>
                    <div className="text-gray-600">ข้อที่ผิด</div>
                  </div>
                  <div className="text-center">
                    <div className="text-4xl font-bold text-blue-600 mb-2">{score.percentage}%</div>
                    <div className="text-gray-600">คะแนนรวม</div>
                  </div>
                </div>

                <div className="space-y-4">
                  {quiz?.questions.map((question, index) => (
                    <Card key={question.question_id} className="text-left">
                      <CardContent className="p-4">
                        <div className="flex items-start space-x-3">
                          {answers[index] === question.correct_answer ? (
                            <CheckCircle className="h-5 w-5 text-green-600 mt-1 flex-shrink-0" />
                          ) : (
                            <XCircle className="h-5 w-5 text-red-600 mt-1 flex-shrink-0" />
                          )}
                          <div className="flex-1">
                            <p className="font-medium mb-2">{question.question}</p>
                            <div className="text-sm space-y-1">
                              <p>
                                <span className="font-medium">คำตอบของคุณ:</span> {answers[index] || "ไม่ได้ตอบ"}
                              </p>
                              <p>
                                <span className="font-medium">คำตอบที่ถูก:</span> {question.correct_answer}
                              </p>
                              <p className="text-gray-600">{question.explanation}</p>
                              <p className="text-xs text-blue-600">ระดับ Bloom's Taxonomy: {question.bloom_level}</p>
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>

                <div className="mt-8 space-x-4">
                  <Link href="/quiz">
                    <Button className="bg-blue-600 hover:bg-blue-700">ทำแบบทดสอบใหม่</Button>
                  </Link>
                  <Link href="/dashboard">
                    <Button variant="outline" className="bg-white text-gray-700 border-gray-300 hover:bg-gray-50">
                      กลับหน้าหลัก
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    )
  }

  const progress = quiz ? ((currentQuestion + 1) / quiz.questions.length) * 100 : 0

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Link href="/dashboard">
              <Button variant="ghost" size="sm" className="text-gray-600 hover:text-gray-900">
                <ArrowLeft className="h-4 w-4 mr-2" />
                กลับ
              </Button>
            </Link>
            <div className="flex items-center space-x-2">
              <Brain className="h-8 w-8 text-blue-600" />
              <span className="text-2xl font-bold text-gray-900">AI Learning</span>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 text-gray-600">
              <Clock className="h-4 w-4" />
              <span className="font-mono">{formatTime(timeLeft)}</span>
            </div>
          </div>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">{quiz?.title}</h1>
            <p className="text-gray-600">แบบทดสอบที่ครอบคลุมทุกระดับตาม Bloom's Taxonomy</p>
          </div>

          {/* Progress */}
          <div className="mb-8">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm text-gray-600">ความคืบหน้า</span>
              <span className="text-sm font-medium">
                {currentQuestion + 1} / {quiz?.questions.length || 0}
              </span>
            </div>
            <Progress value={progress} className="h-2" />
          </div>

          {/* Question */}
          <Card className="border-0 shadow-lg mb-8">
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-xl mb-2">คำถามที่ {currentQuestion + 1}</CardTitle>
                  <CardDescription>ระดับ: {quiz?.questions[currentQuestion]?.bloom_level}</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <h2 className="text-lg font-medium mb-6 leading-relaxed">{quiz?.questions[currentQuestion]?.question}</h2>

              <RadioGroup value={selectedAnswer} onValueChange={handleAnswerSelect}>
                <div className="space-y-4">
                  {quiz?.questions[currentQuestion]?.options.map((option, index) => (
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
              disabled={currentQuestion === 0}
              className="bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
            >
              คำถามก่อนหน้า
            </Button>

            <Button onClick={handleNextQuestion} disabled={!selectedAnswer} className="bg-blue-600 hover:bg-blue-700">
              {quiz && currentQuestion === quiz.questions.length - 1 ? "ส่งคำตอบ" : "คำถามถัดไป"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
