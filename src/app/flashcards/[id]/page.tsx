"use client"

import { useEffect, useState, useCallback } from "react"
import { useParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Progress } from "@/components/ui/progress"
import { apiService } from "@/lib/api"
import {  AlertCircle, ArrowLeft, RefreshCw, Check, Brain, Play, Eye, Calendar, BookOpen, Clock, Star, CheckCircle, XCircle, EyeOff } from "lucide-react"
import Link from "next/link"
import { AuthWrapper } from "@/components/providers/auth-wrpper"

interface FlashcardData {
  card_id: string
  document_id: string
  question: string
  answer: string
  difficulty: string
  next_review: string
  review_count: number
  created_at: string
  ease_factor: number
  interval: number
  urgency: string
  is_due: boolean
}

export default function FlashcardPage() {
  const params = useParams()
  const id = params.id as string

  const [flashcards, setFlashcards] = useState<FlashcardData[]>([])
  const [documentInfo, setDocumentInfo] = useState<Record<string, unknown> | null>(null)
  const [currentCardIndex, setCurrentCardIndex] = useState(0)
  const [isFlipped, setIsFlipped] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState("study")
  const [studySession, setStudySession] = useState({
    correct: 0,
    incorrect: 0,
    total: 0,
  })
  const [sessionStartTime, setSessionStartTime] = useState(Date.now())
  const [cardStartTime, setCardStartTime] = useState(Date.now())

  const loadFlashcardData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Decode URL-encoded Thai characters
      const decodedId = decodeURIComponent(id)
      
      // Load flashcards for this document/topic and document info
      const [flashcardsResponse, docResponse] = await Promise.all([
        apiService.getFlashcardsByDocument(decodedId, 0, 100),
        apiService.getDocument(decodedId).catch(() => ({ success: false })) // Don't fail if document doesn't exist (for topics)
      ])

      if (flashcardsResponse.success && flashcardsResponse.data) {
        const flashcards = (flashcardsResponse.data as { flashcards?: FlashcardData[] }).flashcards || []
        setFlashcards(flashcards)
        
        if (docResponse.success && 'data' in docResponse && docResponse.data) {
          setDocumentInfo(docResponse.data as unknown as Record<string, unknown>)
        } else {
          // Handle topic-based flashcards
          const isTopicBased = id.startsWith('topic_')
          setDocumentInfo({
            is_topic_based: isTopicBased,
            source_name: isTopicBased ? id.replace('topic_', '').replace(/_/g, ' ') : id,
            filename: isTopicBased ? `${id.replace('topic_', '').replace(/_/g, ' ')}.topic` : 'Unknown'
          })
        }
        
        // Don't show error if flashcards array is empty - that's normal
      } else {
        setError("ไม่พบแฟลชการ์ดสำหรับเอกสาร/หัวข้อนี้")
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "เกิดข้อผิดพลาดในการโหลดข้อมูล")
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => {
    if (id) {
      loadFlashcardData()
    }
  }, [id, loadFlashcardData])

  const startStudySession = () => {
    if (flashcards.length === 0) {
      alert("ไม่มีแฟลชการ์ดในเอกสารนี้")
      return
    }
    
    // Reset session state
    setCurrentCardIndex(0)
    setIsFlipped(false)
    setActiveTab("study")
    setStudySession({ correct: 0, incorrect: 0, total: 0 })
    setSessionStartTime(Date.now())
    setCardStartTime(Date.now())
  }

  const handleAnswer = async (quality: number) => {
    if (flashcards.length === 0) return
    
    const timeSpent = Math.round((Date.now() - cardStartTime) / 1000)
    const isCorrect = quality >= 3
    
    try {
      const answer = {
        card_id: flashcards[currentCardIndex].card_id,
        quality: quality,
        time_taken: timeSpent,
        is_correct: isCorrect,
        user_answer: ""
      }

      await apiService.submitFlashcardAnswer(answer)
      
      // Update session stats
      if (isCorrect) {
        setStudySession((prev) => ({ ...prev, correct: prev.correct + 1, total: prev.total + 1 }))
      } else {
        setStudySession((prev) => ({ ...prev, incorrect: prev.incorrect + 1, total: prev.total + 1 }))
      }
    } catch (error) {
      console.error('Error submitting answer:', error)
      // Continue even if API call fails - don't block user progression
    }
    
    // Always move to next card or finish, regardless of API success/failure
    if (currentCardIndex < flashcards.length - 1) {
      setCurrentCardIndex(currentCardIndex + 1)
      setIsFlipped(false)
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
      loadFlashcardData() // Reload to get updated status
      setActiveTab("list")
    }
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

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
    
    if (diffDays === 0) return 'วันนี้'
    if (diffDays === 1) return 'เมื่อวาน'
    if (diffDays < 7) return `${diffDays} วันที่แล้ว`
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} สัปดาห์ที่แล้ว`
    return `${Math.floor(diffDays / 30)} เดือนที่แล้ว`
  }

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
          <AlertCircle className="h-16 w-16 text-red-600 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">เกิดข้อผิดพลาด</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <div className="space-y-2">
            <Button onClick={loadFlashcardData} className="bg-blue-600 hover:bg-blue-700 w-full">
              <RefreshCw className="h-4 w-4 mr-2" />
              ลองใหม่
            </Button>
            <Link href="/flashcards/library">
              <Button variant="outline" className="w-full">
                <ArrowLeft className="h-4 w-4 mr-2" />
                กลับไปคลังแฟลชการ์ด
              </Button>
            </Link>
          </div>
        </div>
      </div>
    )
  }

  const currentCard = flashcards[currentCardIndex]
  const dueCount = flashcards.filter(card => card.is_due).length

  return (
    <AuthWrapper>
      <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Link href="/flashcards/library">
              <Button variant="ghost" size="sm" className="text-gray-600 hover:text-gray-900">
                <ArrowLeft className="h-4 w-4 mr-2" />
                กลับ
              </Button>
            </Link>
            <div className="flex items-center space-x-2">
              <Brain className="h-8 w-8 text-blue-600" />
              <div>
                <h1 className="text-xl font-bold text-gray-900">
                  {String(documentInfo?.source_name) || String(documentInfo?.filename) || 'แฟลชการ์ด'}
                </h1>
                {Boolean(documentInfo?.is_topic_based) && (
                  <p className="text-sm text-gray-600">หัวข้อการเรียนรู้</p>
                )}
              </div>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <div className="text-sm text-gray-600">
              {flashcards.length} แฟลชการ์ด • {dueCount} ถึงเวลาทบทวน
            </div>
          </div>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-8">
        <div className="max-w-6xl mx-auto">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="list">รายการแฟลชการ์ด</TabsTrigger>
              <TabsTrigger value="study">ทบทวน</TabsTrigger>
            </TabsList>

            <TabsContent value="list" className="space-y-6">
              <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold">แฟลชการ์ดทั้งหมด</h2>
                <Button onClick={startStudySession} className="bg-blue-600 hover:bg-blue-700">
                  <Play className="h-4 w-4 mr-2" />
                  เริ่มทบทวน {dueCount > 0 ? `(${dueCount})` : ''}
                </Button>
              </div>

              <div className="grid gap-4">
                {flashcards.map((card, index) => (
                  <Card key={card.card_id} className={`hover:shadow-md transition-shadow ${card.is_due ? 'border-orange-200 bg-orange-50' : ''}`}>
                    <CardContent className="p-6">
                      <div className="flex justify-between items-start mb-4">
                        <div className="flex-1">
                          <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2">
                            {card.question}
                          </h3>
                          <p className="text-gray-600 text-sm line-clamp-2 mb-3">
                            {card.answer}
                          </p>
                          <div className="flex items-center space-x-2 text-xs text-gray-500">
                            <Badge variant="outline">{card.difficulty}</Badge>
                            <span>•</span>
                            <span>ทบทวน {card.review_count} ครั้ง</span>
                            <span>•</span>
                            <span>สร้างเมื่อ {formatTimeAgo(card.created_at)}</span>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2 ml-4">
                          {card.is_due ? (
                            <Badge className="bg-orange-100 text-orange-600">ถึงเวลา</Badge>
                          ) : (
                            <Badge className="bg-gray-100 text-gray-600">รอทบทวน</Badge>
                          )}
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              setCurrentCardIndex(index)
                              setIsFlipped(false)
                              setActiveTab("study")
                            }}
                          >
                            <Eye className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>
                      
                      <div className="flex justify-between items-center text-xs text-gray-500">
                        <div className="flex items-center">
                          <Calendar className="h-3 w-3 mr-1" />
                          ทบทวนครั้งถัดไป: {new Date(card.next_review).toLocaleDateString('th-TH')}
                        </div>
                        <div className="flex items-center">
                          <Clock className="h-3 w-3 mr-1" />
                          ช่วงเวลา: {card.interval} วัน
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              {flashcards.length === 0 && (
                <Card>
                  <CardContent className="p-8 text-center">
                    <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">ไม่มีแฟลชการ์ด</h3>
                    <p className="text-gray-600 mb-4">ยังไม่มีแฟลชการ์ดสำหรับเอกสาร/หัวข้อนี้</p>
                    <Link href="/flashcards/generate">
                      <Button className="bg-blue-600 hover:bg-blue-700">
                        สร้างแฟลชการ์ด
                      </Button>
                    </Link>
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            <TabsContent value="study" className="space-y-6">
              {currentCard ? (
                <div className="max-w-4xl mx-auto">
                  {/* Header with SM-2 Info */}
                  <div className="mb-6">
                    <h2 className="text-2xl font-bold text-gray-900 mb-2">ทบทวนแฟลชการ์ดด้วย SM-2 Algorithm</h2>
                    <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                      <p className="text-sm text-blue-800">
                        <Star className="h-4 w-4 inline mr-1" />
                        <strong>SM-2 Algorithm:</strong> ระบบจะปรับช่วงเวลาทบทวนตามการประเมินความยากง่าย (Quality 0-5) 
                        โดยใช้สูตร I(n) = I(n-1) × EF เพื่อหาช่วงเวลาที่เหมาะสมที่สุด
                      </p>
                    </div>
                  </div>

                  {/* Progress */}
                  <div className="mb-6">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm text-gray-600">ความคืบหน้า</span>
                      <span className="text-sm font-medium">
                        {currentCardIndex + 1} / {flashcards.length}
                      </span>
                    </div>
                    <Progress value={((currentCardIndex + 1) / flashcards.length) * 100} className="h-3" />
                  </div>

                  {/* Stats */}
                  <div className="grid grid-cols-3 gap-4 mb-6">
                    <Card className="border-0 shadow-sm">
                      <CardContent className="p-4 text-center">
                        <CheckCircle className="h-6 w-6 text-green-600 mx-auto mb-2" />
                        <p className="text-xl font-bold text-green-600">{studySession.correct}</p>
                        <p className="text-xs text-gray-600">ถูก</p>
                      </CardContent>
                    </Card>

                    <Card className="border-0 shadow-sm">
                      <CardContent className="p-4 text-center">
                        <XCircle className="h-6 w-6 text-red-600 mx-auto mb-2" />
                        <p className="text-xl font-bold text-red-600">{studySession.incorrect}</p>
                        <p className="text-xs text-gray-600">ผิด</p>
                      </CardContent>
                    </Card>

                    <Card className="border-0 shadow-sm">
                      <CardContent className="p-4 text-center">
                        <Clock className="h-6 w-6 text-blue-600 mx-auto mb-2" />
                        <p className="text-xl font-bold text-blue-600">{studySession.total}</p>
                        <p className="text-xs text-gray-600">รวม</p>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Flashcard */}
                  <Card className="min-h-[400px] shadow-lg">
                    <CardHeader>
                      <div className="flex justify-between items-center">
                        <div>
                          <CardTitle className="text-lg">แฟลชการ์ด</CardTitle>
                          <CardDescription>
                            ระดับความยาก: {currentCard.difficulty} | 
                            EF: {currentCard.ease_factor?.toFixed(2) || '2.50'} | 
                            ช่วงเวลา: {currentCard.interval || 1} วัน | 
                            ทบทวนครั้งถัดไป: {new Date(currentCard.next_review).toLocaleDateString('th-TH')}
                          </CardDescription>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Badge className={currentCard.is_due ? "bg-orange-100 text-orange-600" : "bg-gray-100 text-gray-600"}>
                            {currentCard.is_due ? "ถึงเวลา" : "รอทบทวน"}
                          </Badge>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setIsFlipped(!isFlipped)}
                            className="bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
                          >
                            {isFlipped ? <EyeOff className="h-4 w-4 mr-2" /> : <Eye className="h-4 w-4 mr-2" />}
                            {isFlipped ? "ซ่อนคำตอบ" : "แสดงคำตอบ"}
                          </Button>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="flex-1 flex flex-col justify-center">
                      <div className="text-center mb-8">
                        <h2 className="text-2xl font-bold text-gray-900 mb-4">
                          {isFlipped ? "คำตอบ" : "คำถาม"}
                        </h2>
                        <p className="text-lg text-gray-700 leading-relaxed whitespace-pre-wrap">
                          {isFlipped ? currentCard.answer : currentCard.question}
                        </p>
                      </div>

                      {isFlipped && (
                        <div className="border-t pt-6">
                          {/* SM-2 Quality Rating Buttons */}
                          <div className="space-y-4">
                            <div className="text-center mb-4">
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

                            <div className="mt-4 p-4 bg-gray-50 rounded-lg border">
                              <h4 className="font-semibold text-gray-900 mb-2">คำแนะนำในการประเมิน:</h4>
                              <ul className="text-sm text-gray-700 space-y-1">
                                <li><strong>0-2:</strong> ตอบผิดหรือไม่จำได้ → ระบบจะให้ทบทวนเร็วขึ้น</li>
                                <li><strong>3:</strong> ตอบถูกแต่ยาก → ระบบจะให้ทบทวนบ่อยขึ้นเล็กน้อย</li>
                                <li><strong>4:</strong> ตอบถูกแต่ลังเล → ระบบจะเพิ่มช่วงเวลาทบทวนตามปกติ</li>
                                <li><strong>5:</strong> ตอบถูกทันทีและมั่นใจ → ระบบจะเพิ่มช่วงเวลาทบทวนมากขึ้น</li>
                              </ul>
                            </div>
                          </div>
                        </div>
                      )}

                      {!isFlipped && (
                        <div className="text-center">
                          <p className="text-gray-600 mb-4">อ่านคำถามและคิดคำตอบในใจ แล้วคลิกเพื่อดูคำตอบ</p>
                          <Button
                            onClick={() => setIsFlipped(true)}
                            className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 text-lg"
                          >
                            <Eye className="h-5 w-5 mr-2" />
                            แสดงคำตอบและประเมิน
                          </Button>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </div>
              ) : (
                <Card>
                  <CardContent className="p-8 text-center">
                    <Check className="h-12 w-12 text-green-600 mx-auto mb-4" />
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">เสร็จสิ้นการทบทวน!</h3>
                    <p className="text-gray-600 mb-4">คุณทบทวนแฟลชการ์ดครบทุกใบแล้ว</p>
                    <div className="space-y-2">
                      <Button onClick={() => setActiveTab("list")} className="bg-blue-600 hover:bg-blue-700">
                        ดูรายการแฟลชการ์ด
                      </Button>
                      <Button onClick={startStudySession} variant="outline">
                        ทบทวนใหม่
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )}
            </TabsContent>
          </Tabs>
        </div>
      </div>
      </div>
    </AuthWrapper>
  )
}