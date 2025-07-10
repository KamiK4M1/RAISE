"use client"

import { useState, useEffect } from "react"
import { Button } from "../../components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Brain, ArrowLeft, RotateCcw, Eye, EyeOff, CheckCircle, XCircle, Clock, BookOpen } from "lucide-react"
import Link from "next/link"
import { apiService } from "@/lib/api"
import { Flashcard, FlashcardSession } from "@/types/api"
import { useAsyncApi } from "@/hooks/useApi"
import { AuthWrapper } from "@/components/providers/auth-wrpper"

export default function FlashcardsPage() {
  const [flashcards, setFlashcards] = useState<Flashcard[]>([])
  const [currentCard, setCurrentCard] = useState(0)
  const [showAnswer, setShowAnswer] = useState(false)
  const [studySession, setStudySession] = useState({
    correct: 0,
    incorrect: 0,
    total: 0,
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [sessionStartTime, setSessionStartTime] = useState(Date.now())
  const [cardStartTime, setCardStartTime] = useState(Date.now())
  
  // Load flashcards from backend
  useEffect(() => {
    const loadFlashcards = async () => {
      try {
        setLoading(true)
        const response = await apiService.getAllUserFlashcards(0, 50)
        
        if (response.success && response.data && response.data.flashcards) {
          // Filter flashcards that are due for review or randomly select some
          const allCards = response.data.flashcards
          const now = new Date()
          
          // Get cards due for review first
          const dueCards = allCards.filter(card => {
            const nextReview = new Date(card.next_review)
            return nextReview <= now
          })
          
          // If we don't have enough due cards, add some random ones
          let sessionCards = dueCards
          if (sessionCards.length < 10) {
            const remainingCards = allCards.filter(card => {
              const nextReview = new Date(card.next_review)
              return nextReview > now
            })
            const needed = Math.min(10 - sessionCards.length, remainingCards.length)
            sessionCards = [...sessionCards, ...remainingCards.slice(0, needed)]
          }
          
          setFlashcards(sessionCards.slice(0, 10))
          setCurrentCard(0)
          setShowAnswer(false)
          setSessionStartTime(Date.now())
          setCardStartTime(Date.now())
        } else {
          throw new Error(response.message || 'Failed to load flashcards')
        }
      } catch (error) {
        console.error('Error loading flashcards:', error)
        const errorMessage = error instanceof Error ? error.message : 'ไม่สามารถโหลดแฟลชการ์ดได้'
        setError(errorMessage)
      } finally {
        setLoading(false)
      }
    }

    loadFlashcards()
  }, [])

  const handleAnswer = async (difficulty: "easy" | "medium" | "hard") => {
    if (flashcards.length === 0) return
    
    const qualityMap = { easy: 5, medium: 3, hard: 1 }
    const timeSpent = Date.now() - cardStartTime
    
    try {
      const answer = {
        card_id: flashcards[currentCard].card_id,
        quality: qualityMap[difficulty],
        time_taken: timeSpent,
        user_answer: "" // Could be enhanced to capture user input
      }

      const response = await apiService.submitFlashcardAnswer(answer)
      
      if (response.success) {
        // Update session stats
        if (difficulty === "easy") {
          setStudySession((prev) => ({ ...prev, correct: prev.correct + 1, total: prev.total + 1 }))
        } else {
          setStudySession((prev) => ({ ...prev, incorrect: prev.incorrect + 1, total: prev.total + 1 }))
        }
        
        // Move to next card or show completion
        if (currentCard < flashcards.length - 1) {
          setCurrentCard(currentCard + 1)
          setShowAnswer(false)
          setCardStartTime(Date.now())
        } else {
          // End of session
          const totalTime = Date.now() - sessionStartTime
          const finalCorrect = studySession.correct + (difficulty === "easy" ? 1 : 0)
          const finalIncorrect = studySession.incorrect + (difficulty === "easy" ? 0 : 1)
          
          alert(
            `เสร็จสิ้นการทบทวน!\nถูก: ${finalCorrect}\nผิด: ${finalIncorrect}\nเวลาที่ใช้: ${Math.round(totalTime / 1000)} วินาที`
          )
        }
      }
    } catch (error) {
      console.error('Error submitting answer:', error)
      // Still allow progression even if API fails
      if (currentCard < flashcards.length - 1) {
        setCurrentCard(currentCard + 1)
        setShowAnswer(false)
        setCardStartTime(Date.now())
      }
    }
  }

  const resetSession = () => {
    setCurrentCard(0)
    setShowAnswer(false)
    setStudySession({ correct: 0, incorrect: 0, total: 0 })
    setSessionStartTime(Date.now())
    setCardStartTime(Date.now())
  }

  const progress = flashcards.length > 0 ? ((currentCard + 1) / flashcards.length) * 100 : 0
  
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">กำลังโหลดแฟลชการ์ด...</p>
        </div>
      </div>
    )
  }
  
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-6">
          <XCircle className="h-16 w-16 text-red-600 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">ไม่สามารถโหลดแฟลชการ์ดได้</h2>
          <p className="text-gray-600 mb-6">
            {error.includes('Authentication') 
              ? 'กรุณาเข้าสู่ระบบเพื่อใช้งานแฟลชการ์ด'
              : 'เกิดข้อผิดพลาดในการเชื่อมต่อกับเซิร์ฟเวอร์ กรุณาตรวจสอบการเชื่อมต่ออินเทอร์เน็ตและลองใหม่'
            }
          </p>
          <div className="space-y-3">
            <Button 
              onClick={() => {
                setError(null);
                setLoading(true);
                // Trigger reload by calling the effect
                const loadFlashcards = async () => {
                  try {
                    setLoading(true)
                    const response = await apiService.getAllUserFlashcards(0, 50)
                    
                    if (response.success && response.data && response.data.flashcards) {
                      const allCards = response.data.flashcards
                      const now = new Date()
                      
                      const dueCards = allCards.filter(card => {
                        const nextReview = new Date(card.next_review)
                        return nextReview <= now
                      })
                      
                      let sessionCards = dueCards
                      if (sessionCards.length < 10) {
                        const remainingCards = allCards.filter(card => {
                          const nextReview = new Date(card.next_review)
                          return nextReview > now
                        })
                        const needed = Math.min(10 - sessionCards.length, remainingCards.length)
                        sessionCards = [...sessionCards, ...remainingCards.slice(0, needed)]
                      }
                      
                      setFlashcards(sessionCards.slice(0, 10))
                      setCurrentCard(0)
                      setShowAnswer(false)
                      setSessionStartTime(Date.now())
                      setCardStartTime(Date.now())
                    } else {
                      throw new Error(response.message || 'Failed to load flashcards')
                    }
                  } catch (error) {
                    console.error('Error loading flashcards:', error)
                    const errorMessage = error instanceof Error ? error.message : 'ไม่สามารถโหลดแฟลชการ์ดได้'
                    setError(errorMessage)
                  } finally {
                    setLoading(false)
                  }
                }
                loadFlashcards();
              }} 
              className="bg-blue-600 hover:bg-blue-700 w-full"
            >
              <RotateCcw className="h-4 w-4 mr-2" />
              ลองใหม่
            </Button>
            {error.includes('Authentication') && (
              <Link href="/login">
                <Button variant="outline" className="w-full">
                  เข้าสู่ระบบ
                </Button>
              </Link>
            )}
            <Link href="/dashboard">
              <Button variant="outline" className="w-full">
                <ArrowLeft className="h-4 w-4 mr-2" />
                กลับหน้าหลัก
              </Button>
            </Link>
          </div>
        </div>
      </div>
    )
  }
  
  if (flashcards.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Brain className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">ไม่พบแฟลชการ์ด</h2>
          <p className="text-gray-600 mb-4">คุณยังไม่มีแฟลชการ์ด กรุณาสร้างแฟลชการ์ดก่อน</p>
          <Link href="/flashcards/generate">
            <Button className="bg-blue-600 hover:bg-blue-700">
              สร้างแฟลชการ์ด
            </Button>
          </Link>
        </div>
      </div>
    )
  }

  return (
    <AuthWrapper>
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
          <div className="flex items-center space-x-2">
            <Link href="/flashcards/quiz">
              <Button variant="outline" className="bg-white text-blue-700 border-blue-300 hover:bg-blue-50">
                <Brain className="h-4 w-4 mr-2" />
                Quiz Mode
              </Button>
            </Link>
            <Link href="/flashcards/library">
              <Button variant="outline" className="bg-white text-gray-700 border-gray-300 hover:bg-gray-50">
                <BookOpen className="h-4 w-4 mr-2" />
                คลังแฟลชการ์ด
              </Button>
            </Link>
            <Button
              variant="outline"
              onClick={resetSession}
              className="bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
            >
              <RotateCcw className="h-4 w-4 mr-2" />
              เริ่มใหม่
            </Button>
          </div>
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
                    <CardTitle className="text-lg">แฟลชการ์ด</CardTitle>
                    <CardDescription>
                      ระดับความยาก: {flashcards[currentCard].difficulty} | ทบทวนครั้งถัดไป:{" "}
                      {new Date(flashcards[currentCard].next_review).toLocaleDateString('th-TH')}
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
                  <p className="text-lg text-gray-700 leading-relaxed whitespace-pre-wrap">{flashcards[currentCard].question}</p>
                </div>

                {showAnswer && (
                  <div className="border-t pt-8">
                    <h3 className="text-xl font-bold text-blue-600 mb-4 text-center">คำตอบ</h3>
                    <p className="text-gray-700 leading-relaxed text-center whitespace-pre-wrap">{flashcards[currentCard].answer}</p>
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
    </AuthWrapper>
  )
}
