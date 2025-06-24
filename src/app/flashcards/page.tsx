"use client"

import { useState } from "react"
import { Button } from "../../components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Brain, ArrowLeft, RotateCcw, Eye, EyeOff, CheckCircle, XCircle, Clock } from "lucide-react"
import Link from "next/link"

export default function FlashcardsPage() {
  const [currentCard, setCurrentCard] = useState(0)
  const [showAnswer, setShowAnswer] = useState(false)
  const [studySession, setStudySession] = useState({
    correct: 0,
    incorrect: 0,
    total: 0,
  })

  // Mock flashcards data
  const flashcards = [
    {
      id: 1,
      question: "สมการเชิงเส้นคืออะไร?",
      answer: "สมการเชิงเส้นคือสมการที่มีตัวแปรยกกำลังหนึ่ง และสามารถเขียนในรูป ax + b = 0 โดยที่ a และ b เป็นค่าคงที่ และ a ≠ 0",
      difficulty: "ง่าย",
      nextReview: "2024-01-15",
      subject: "คณิตศาสตร์",
    },
    {
      id: 2,
      question: "กฎของนิวตันข้อที่ 1 คืออะไร?",
      answer:
        "กฎของนิวตันข้อที่ 1 หรือกฎความเฉื่อย กล่าวว่า วัตถุที่อยู่นิ่งจะอยู่นิ่งต่อไป และวัตถุที่เคลื่อนที่จะเคลื่อนที่ด้วยความเร็วคงที่ในแนวเส้นตรง เว้นแต่จะมีแรงภายนอกมากระทำ",
      difficulty: "ปานกลาง",
      nextReview: "2024-01-16",
      subject: "ฟิสิกส์",
    },
    {
      id: 3,
      question: "โครงสร้างของอะตอมประกอบด้วยอะไรบ้าง?",
      answer:
        "อะตอมประกอบด้วย 3 ส่วนหลัก คือ 1) นิวเคลียส (ประกอบด้วยโปรตอนและนิวตรอน) 2) อิเล็กตรอนที่โคจรรอบนิวเคลียส 3) พื้นที่ว่างระหว่างนิวเคลียสกับอิเล็กตรอน",
      difficulty: "ยาก",
      nextReview: "2024-01-17",
      subject: "เคมี",
    },
  ]

  const handleAnswer = (difficulty: "easy" | "medium" | "hard") => {
    if (difficulty === "easy") {
      setStudySession((prev) => ({ ...prev, correct: prev.correct + 1, total: prev.total + 1 }))
    } else {
      setStudySession((prev) => ({ ...prev, incorrect: prev.incorrect + 1, total: prev.total + 1 }))
    }

    // Move to next card
    if (currentCard < flashcards.length - 1) {
      setCurrentCard(currentCard + 1)
      setShowAnswer(false)
    } else {
      // End of session
      alert(
        `เสร็จสิ้นการทบทวน!\nถูก: ${studySession.correct + (difficulty === "easy" ? 1 : 0)}\nผิด: ${studySession.incorrect + (difficulty === "easy" ? 0 : 1)}`,
      )
    }

    // TODO: Send to Python backend for spaced repetition algorithm
    console.log("Answer recorded:", { cardId: flashcards[currentCard].id, difficulty })
  }

  const resetSession = () => {
    setCurrentCard(0)
    setShowAnswer(false)
    setStudySession({ correct: 0, incorrect: 0, total: 0 })
  }

  const progress = ((currentCard + 1) / flashcards.length) * 100

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
          <Button
            variant="outline"
            onClick={resetSession}
            className="bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
          >
            <RotateCcw className="h-4 w-4 mr-2" />
            เริ่มใหม่
          </Button>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">แฟลชการ์ดอัจฉริยะ</h1>
            <p className="text-gray-600">ทบทวนความรู้ด้วยระบบ Spaced Repetition เพื่อเพิ่มประสิทธิภาพการจำ</p>
          </div>

          {/* Progress */}
          <div className="mb-8">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm text-gray-600">ความคืบหน้า</span>
              <span className="text-sm font-medium">
                {currentCard + 1} / {flashcards.length}
              </span>
            </div>
            <Progress value={progress} className="h-2" />
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-4 mb-8"></div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-4 mb-8">
            <Card className="border-0 shadow-sm">
              <CardContent className="p-4 text-center">
                <CheckCircle className="h-8 w-8 text-green-600 mx-auto mb-2" />
                <p className="text-2xl font-bold text-green-600">{studySession.correct}</p>
                <p className="text-sm text-gray-600">ถูก</p>
              </CardContent>
            </Card>

            <Card className="border-0 shadow-sm">
              <CardContent className="p-4 text-center">
                <XCircle className="h-8 w-8 text-red-600 mx-auto mb-2" />
                <p className="text-2xl font-bold text-red-600">{studySession.incorrect}</p>
                <p className="text-sm text-gray-600">ผิด</p>
              </CardContent>
            </Card>

            <Card className="border-0 shadow-sm">
              <CardContent className="p-4 text-center">
                <Clock className="h-8 w-8 text-blue-600 mx-auto mb-2" />
                <p className="text-2xl font-bold text-blue-600">{studySession.total}</p>
                <p className="text-sm text-gray-600">รวม</p>
              </CardContent>
            </Card>
          </div>

          {/* Flashcard */}
          <div className="mb-8">
            <Card className="border-0 shadow-lg min-h-[400px]">
              <CardHeader>
                <div className="flex justify-between items-center">
                  <div>
                    <CardTitle className="text-lg">{flashcards[currentCard].subject}</CardTitle>
                    <CardDescription>
                      ระดับความยาก: {flashcards[currentCard].difficulty} | ทบทวนครั้งถัดไป:{" "}
                      {flashcards[currentCard].nextReview}
                    </CardDescription>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowAnswer(!showAnswer)}
                    className="bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
                  >
                    {showAnswer ? <EyeOff className="h-4 w-4 mr-2" /> : <Eye className="h-4 w-4 mr-2" />}
                    {showAnswer ? "ซ่อนคำตอบ" : "แสดงคำตอบ"}
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="flex-1 flex flex-col justify-center">
                <div className="text-center mb-8">
                  <h2 className="text-2xl font-bold text-gray-900 mb-4">คำถาม</h2>
                  <p className="text-lg text-gray-700 leading-relaxed">{flashcards[currentCard].question}</p>
                </div>

                {showAnswer && (
                  <div className="border-t pt-8">
                    <h3 className="text-xl font-bold text-blue-600 mb-4 text-center">คำตอบ</h3>
                    <p className="text-gray-700 leading-relaxed text-center">{flashcards[currentCard].answer}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Answer Buttons */}
          {showAnswer && (
            <div className="grid grid-cols-3 gap-4">
              <Button
                onClick={() => handleAnswer("hard")}
                variant="outline"
                className="bg-red-50 text-red-700 border-red-200 hover:bg-red-100 py-6"
              >
                <div className="text-center">
                  <XCircle className="h-6 w-6 mx-auto mb-2" />
                  <div className="font-semibold">ยาก</div>
                  <div className="text-sm opacity-75">ทบทวนใน 1 วัน</div>
                </div>
              </Button>

              <Button
                onClick={() => handleAnswer("medium")}
                variant="outline"
                className="bg-yellow-50 text-yellow-700 border-yellow-200 hover:bg-yellow-100 py-6"
              >
                <div className="text-center">
                  <Clock className="h-6 w-6 mx-auto mb-2" />
                  <div className="font-semibold">ปานกลาง</div>
                  <div className="text-sm opacity-75">ทบทวนใน 3 วัน</div>
                </div>
              </Button>

              <Button
                onClick={() => handleAnswer("easy")}
                variant="outline"
                className="bg-green-50 text-green-700 border-green-200 hover:bg-green-100 py-6"
              >
                <div className="text-center">
                  <CheckCircle className="h-6 w-6 mx-auto mb-2" />
                  <div className="font-semibold">ง่าย</div>
                  <div className="text-sm opacity-75">ทบทวนใน 7 วัน</div>
                </div>
              </Button>
            </div>
          )}

          {!showAnswer && (
            <div className="text-center">
              <p className="text-gray-600 mb-4">คิดคำตอบแล้วคลิกเพื่อดูคำตอบ</p>
              <Button
                onClick={() => setShowAnswer(true)}
                className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3"
              >
                แสดงคำตอบ
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
