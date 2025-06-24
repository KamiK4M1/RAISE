"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Label } from "@/components/ui/label"
import { Brain, ArrowLeft, CheckCircle, XCircle, Clock, Award } from "lucide-react"
import Link from "next/link"

export default function QuizPage() {
  const [currentQuestion, setCurrentQuestion] = useState(0)
  const [selectedAnswer, setSelectedAnswer] = useState("")
  const [answers, setAnswers] = useState<string[]>([])
  const [showResults, setShowResults] = useState(false)
  const [timeLeft, setTimeLeft] = useState(300) // 5 minutes

  // Mock quiz data covering Bloom's Taxonomy levels
  const quiz = {
    title: "แบบทดสอบคณิตศาสตร์ - สมการเชิงเส้น",
    subject: "คณิตศาสตร์",
    totalTime: 300,
    questions: [
      {
        id: 1,
        question: "สมการเชิงเส้นคือสมการที่มีตัวแปรยกกำลังเท่าใด?",
        type: "multiple-choice",
        bloomLevel: "จำ (Remember)",
        options: ["กำลังศูนย์", "กำลังหนึ่ง", "กำลังสอง", "กำลังสาม"],
        correctAnswer: "กำลังหนึ่ง",
        explanation: "สมการเชิงเส้นคือสมการที่มีตัวแปรยกกำลังหนึ่ง เช่น ax + b = 0",
      },
      {
        id: 2,
        question: "จากสมการ 2x + 6 = 14 ค่าของ x เท่ากับเท่าใด?",
        type: "multiple-choice",
        bloomLevel: "เข้าใจ (Understand)",
        options: ["x = 2", "x = 4", "x = 6", "x = 8"],
        correctAnswer: "x = 4",
        explanation: "2x + 6 = 14 → 2x = 14 - 6 → 2x = 8 → x = 4",
      },
      {
        id: 3,
        question: "ถ้า 3x - 5 = 2x + 7 แล้ว x มีค่าเท่าใด?",
        type: "multiple-choice",
        bloomLevel: "ประยุกต์ (Apply)",
        options: ["x = 10", "x = 12", "x = 14", "x = 16"],
        correctAnswer: "x = 12",
        explanation: "3x - 5 = 2x + 7 → 3x - 2x = 7 + 5 → x = 12",
      },
      {
        id: 4,
        question: "เปรียบเทียบวิธีการแก้สมการ 2x + 3 = 11 และ 4x + 6 = 22 แล้วสรุปความสัมพันธ์",
        type: "multiple-choice",
        bloomLevel: "วิเคราะห์ (Analyze)",
        options: [
          "สมการที่สองเป็น 2 เท่าของสมการแรก และมีคำตอบเดียวกัน",
          "สมการทั้งสองไม่เกี่ยวข้องกัน",
          "สมการที่สองยากกว่าสมการแรก",
          "สมการแรกมีคำตอบมากกว่าสมการที่สอง",
        ],
        correctAnswer: "สมการที่สองเป็น 2 เท่าของสมการแรก และมีคำตอบเดียวกัน",
        explanation: "สมการ 4x + 6 = 22 เมื่อหารด้วย 2 จะได้ 2x + 3 = 11 ซึ่งเป็นสมการเดียวกัน",
      },
      {
        id: 5,
        question: "ประเมินความถูกต้องของข้อความ: 'สมการเชิงเส้นทุกสมการจะมีคำตอบเพียงหนึ่งเดียวเสมอ'",
        type: "multiple-choice",
        bloomLevel: "ประเมิน (Evaluate)",
        options: [
          "ถูกต้อง เพราะสมการเชิงเส้นมีคำตอบเดียว",
          "ผิด เพราะบางสมการอาจไม่มีคำตอบหรือมีคำตอบไม่จำกัด",
          "ถูกต้องเฉพาะสมการที่มี x เท่านั้น",
          "ผิด เพราะสมการเชิงเส้นมีคำตอบหลายตัวเสมอ",
        ],
        correctAnswer: "ผิด เพราะบางสมการอาจไม่มีคำตอบหรือมีคำตอบไม่จำกัด",
        explanation: "สมการเชิงเส้นอาจไม่มีคำตอบ (เช่น 2x + 1 = 2x + 3) หรือมีคำตอบไม่จำกัด (เช่น 2x + 1 = 2x + 1)",
      },
    ],
  }

  const handleAnswerSelect = (value: string) => {
    setSelectedAnswer(value)
  }

  const handleNextQuestion = () => {
    const newAnswers = [...answers]
    newAnswers[currentQuestion] = selectedAnswer
    setAnswers(newAnswers)

    if (currentQuestion < quiz.questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1)
      setSelectedAnswer("")
    } else {
      setShowResults(true)
    }

    // TODO: Send answer to Python backend
    console.log("Answer submitted:", {
      questionId: quiz.questions[currentQuestion].id,
      answer: selectedAnswer,
    })
  }

  const calculateScore = () => {
    let correct = 0
    answers.forEach((answer, index) => {
      if (answer === quiz.questions[index].correctAnswer) {
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
                <span className="text-2xl font-bold text-gray-900">AI Learning</span>
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
                <CardDescription className="text-lg">{quiz.title}</CardDescription>
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
                  {quiz.questions.map((question, index) => (
                    <Card key={question.id} className="text-left">
                      <CardContent className="p-4">
                        <div className="flex items-start space-x-3">
                          {answers[index] === question.correctAnswer ? (
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
                                <span className="font-medium">คำตอบที่ถูก:</span> {question.correctAnswer}
                              </p>
                              <p className="text-gray-600">{question.explanation}</p>
                              <p className="text-xs text-blue-600">ระดับ Bloom's Taxonomy: {question.bloomLevel}</p>
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

  const progress = ((currentQuestion + 1) / quiz.questions.length) * 100

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
            <h1 className="text-3xl font-bold text-gray-900 mb-2">{quiz.title}</h1>
            <p className="text-gray-600">แบบทดสอบที่ครอบคลุมทุกระดับตาม Bloom's Taxonomy</p>
          </div>

          {/* Progress */}
          <div className="mb-8">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm text-gray-600">ความคืบหน้า</span>
              <span className="text-sm font-medium">
                {currentQuestion + 1} / {quiz.questions.length}
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
                  <CardDescription>ระดับ: {quiz.questions[currentQuestion].bloomLevel}</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <h2 className="text-lg font-medium mb-6 leading-relaxed">{quiz.questions[currentQuestion].question}</h2>

              <RadioGroup value={selectedAnswer} onValueChange={handleAnswerSelect}>
                <div className="space-y-4">
                  {quiz.questions[currentQuestion].options.map((option, index) => (
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
              {currentQuestion === quiz.questions.length - 1 ? "ส่งคำตอบ" : "คำถามถัดไป"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
