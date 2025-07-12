"use client"

import { useState, useEffect } from "react"
import { Button } from "../../components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Brain, ArrowLeft, RotateCcw, Eye, EyeOff, CheckCircle, XCircle, Clock, BookOpen, Star } from "lucide-react"
import Link from "next/link"
import { apiService } from "@/lib/api"
import { Flashcard } from "@/types/api"
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
        
        if (response.success && response.data && Array.isArray((response.data as { flashcards?: Flashcard[] }).flashcards)) {
          // Filter flashcards that are due for review or randomly select some
          const allCards = (response.data as { flashcards: Flashcard[] }).flashcards
          const now = new Date()
          
          // Get cards due for review first
          const dueCards = allCards.filter((card: Flashcard) => {
            const nextReview = new Date(card.next_review)
            return nextReview <= now
          })
          
          // If we don't have enough due cards, add some random ones
          let sessionCards = dueCards
          if (sessionCards.length < 10) {
            const remainingCards = allCards.filter((card: Flashcard) => {
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

  const handleAnswer = async (quality: number) => {
    if (flashcards.length === 0) return
    
    const timeSpent = Math.round((Date.now() - cardStartTime) / 1000)
    const isCorrect = quality >= 3
    
    try {
      const answer = {
        card_id: flashcards[currentCard].card_id,
        quality: quality,
        time_taken: timeSpent,
        is_correct: isCorrect,
        user_answer: ""
      }

      const response = await apiService.submitFlashcardAnswer(answer)
      
      if (response.success) {
        // Update session stats
        if (isCorrect) {
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
          const totalTime = Math.round((Date.now() - sessionStartTime) / 1000)
          const finalCorrect = studySession.correct + (isCorrect ? 1 : 0)
          const finalIncorrect = studySession.incorrect + (isCorrect ? 0 : 1)
          const accuracy = Math.round((finalCorrect / (finalCorrect + finalIncorrect)) * 100)
          
          alert(
            `🎉 เสร็จสิ้นการทบทวน!\n\n` +
            `✅ ถูก: ${finalCorrect} ข้อ\n` +
            `❌ ผิด: ${finalIncorrect} ข้อ\n` +
            `📊 ความแม่นยำ: ${accuracy}%\n` +
            `⏱️ เวลาที่ใช้: ${Math.floor(totalTime / 60)} นาที ${totalTime % 60} วินาที\n\n` +
            `ระบบ SM-2 จะปรับช่วงเวลาทบทวนให้เหมาะสมกับความสามารถของคุณ`
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

  const getQualityLabel = (quality: number) => {
    switch (quality) {
      case 0: return { text: "ลืมหมด", desc: "ไม่จำได้เลย", color: "text-red-800", bg: "bg-red-100", border: "border-red-300" }
      case 1: return { text: "ผิด (ง่าย)", desc: "ตอบผิดแต่คำตอบดูง่าย", color: "text-red-700", bg: "bg-red-50", border: "border-red-200" }
      case 2: return { text: "ผิด (ยาก)", desc: "ตอบผิดและคำตอบดูยาก", color: "text-orange-700", bg: "bg-orange-50", border: "border-orange-200" }
      case 3: return { text: "ถูก (ยาก)", desc: "ตอบถูกแต่ใช้เวลานาน", color: "text-yellow-700", bg: "bg-yellow-50", border: "border-yellow-200" }
      case 4: return { text: "ถูก (ลังเล)", desc: "ตอบถูกแต่ลังเลเล็กน้อย", color: "text-green-700", bg: "bg-green-50", border: "border-green-200" }
      case 5: return { text: "ถูก (แม่นยำ)", desc: "ตอบถูกทันทีและมั่นใจ", color: "text-green-800", bg: "bg-green-100", border: "border-green-300" }
      default: return { text: "ไม่ทราบ", desc: "", color: "text-gray-700", bg: "bg-gray-50", border: "border-gray-200" }
    }
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
                window.location.reload();
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
            <p className="text-gray-600">ทบทวนความรู้ด้วยระบบ Spaced Repetition Algorithm (SM-2) เพื่อเพิ่มประสิทธิภาพการจำ</p>
            <div className="mt-2 p-3 bg-blue-50 rounded-lg border border-blue-200">
              <p className="text-sm text-blue-800">
                <Star className="h-4 w-4 inline mr-1" />
                <strong>SM-2 Algorithm:</strong> ระบบจะปรับช่วงเวลาทบทวนตามการประเมินความยากง่าย (Quality 0-5) 
                โดยใช้สูตร I(n) = I(n-1) × EF เพื่อหาช่วงเวลาที่เหมาะสมที่สุด
              </p>
            </div>
          </div>

          {/* Progress */}
          <div className="mb-8">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm text-gray-600">ความคืบหน้า</span>
              <span className="text-sm font-medium">
                {currentCard + 1} / {flashcards.length}
              </span>
            </div>
            <Progress value={progress} className="h-3" />
          </div>

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
                      ระดับความยาก: {flashcards[currentCard].difficulty} | 
                      EF: {flashcards[currentCard].ease_factor?.toFixed(2) || '2.50'} | 
                      ช่วงเวลา: {flashcards[currentCard].interval || 1} วัน | 
                      ทบทวนครั้งถัดไป: {new Date(flashcards[currentCard].next_review).toLocaleDateString('th-TH')}
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

          {/* SM-2 Quality Rating Buttons */}
          {showAnswer && (
            <div className="space-y-4">
              <div className="text-center mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">ประเมินความยากง่ายในการจำ (SM-2 Quality Scale)</h3>
                <p className="text-sm text-gray-600">การประเมินนี้จะใช้ในการคำนวณช่วงเวลาทบทวนครั้งถัดไป</p>
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {[0, 1, 2, 3, 4, 5].map((quality) => {
                  const { text, desc, color, bg, border } = getQualityLabel(quality)
                  return (
                    <Button
                      key={quality}
                      onClick={() => handleAnswer(quality)}
                      variant="outline"
                      className={`${bg} ${color} ${border} hover:opacity-80 p-4 h-auto`}
                    >
                      <div className="text-center w-full">
                        <div className="font-bold text-lg mb-1">{quality}</div>
                        <div className="font-semibold text-sm mb-1">{text}</div>
                        <div className="text-xs opacity-75 leading-tight">{desc}</div>
                      </div>
                    </Button>
                  )
                })}
              </div>

              <div className="mt-6 p-4 bg-gray-50 rounded-lg border">
                <h4 className="font-semibold text-gray-900 mb-2">คำแนะนำในการประเมิน:</h4>
                <ul className="text-sm text-gray-700 space-y-1">
                  <li><strong>0-2:</strong> ตอบผิดหรือไม่จำได้ → ระบบจะให้ทบทวนเร็วขึ้น</li>
                  <li><strong>3:</strong> ตอบถูกแต่ยาก → ระบบจะให้ทบทวนบ่อยขึ้นเล็กน้อย</li>
                  <li><strong>4:</strong> ตอบถูกแต่ลังเล → ระบบจะเพิ่มช่วงเวลาทบทวนตามปกติ</li>
                  <li><strong>5:</strong> ตอบถูกทันทีและมั่นใจ → ระบบจะเพิ่มช่วงเวลาทบทวนมากขึ้น</li>
                </ul>
                
              </div>
            </div>
          )}

          {!showAnswer && (
            <div className="text-center">
              <p className="text-gray-600 mb-4">อ่านคำถามและคิดคำตอบในใจ แล้วคลิกเพื่อดูคำตอบ</p>
              <Button
                onClick={() => setShowAnswer(true)}
                className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 text-lg"
              >
                <Eye className="h-5 w-5 mr-2" />
                แสดงคำตอบและประเมิน
              </Button>
            </div>
          )}
        </div>
      </div>
      </div>
    </AuthWrapper>
  )
}