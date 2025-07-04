"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Flashcard } from "@/types/api"
import { apiService } from "@/lib/api"
import { Loader2, AlertCircle, ArrowLeft, RefreshCw, Lightbulb, Check, Brain, Play, Eye, Calendar, BookOpen, Clock } from "lucide-react"
import Link from "next/link"

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
  const router = useRouter()
  const id = params.id as string

  const [flashcards, setFlashcards] = useState<FlashcardData[]>([])
  const [documentInfo, setDocumentInfo] = useState<any>(null)
  const [currentCardIndex, setCurrentCardIndex] = useState(0)
  const [isFlipped, setIsFlipped] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState("study")

  useEffect(() => {
    if (id) {
      loadFlashcardData()
    }
  }, [id])

  const loadFlashcardData = async () => {
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
        const flashcards = flashcardsResponse.data.flashcards || []
        setFlashcards(flashcards)
        
        if (docResponse.success && docResponse.data) {
          setDocumentInfo(docResponse.data)
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
    } catch (err: any) {
      setError(err.message || "เกิดข้อผิดพลาดในการโหลดข้อมูล")
    } finally {
      setLoading(false)
    }
  }

  const startStudySession = () => {
    if (flashcards.length === 0) {
      alert("ไม่มีแฟลชการ์ดในเอกสารนี้")
      return
    }
    
    // Always allow studying all flashcards repeatedly
    setCurrentCardIndex(0)
    setIsFlipped(false)
    setActiveTab("study")
  }

  const handleAnswer = async (difficulty: "easy" | "medium" | "hard") => {
    if (flashcards.length === 0) return
    
    const qualityMap = { easy: 5, medium: 3, hard: 1 }
    
    try {
      const answer = {
        card_id: flashcards[currentCardIndex].card_id,
        quality: qualityMap[difficulty],
        time_taken: 3000, // Default time
        user_answer: ""
      }

      await apiService.submitFlashcardAnswer(answer)
      
      // Move to next card or finish
      if (currentCardIndex < flashcards.length - 1) {
        setCurrentCardIndex(currentCardIndex + 1)
        setIsFlipped(false)
      } else {
        alert("เสร็จสิ้นการทบทวน!")
        loadFlashcardData() // Reload to get updated status
        setActiveTab("list")
      }
    } catch (error) {
      console.error('Error submitting answer:', error)
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
                  {documentInfo?.source_name || documentInfo?.filename || 'แฟลชการ์ด'}
                </h1>
                {documentInfo?.is_topic_based && (
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
                  {/* Progress */}
                  <div className="mb-6">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm text-gray-600">ความคืบหน้า</span>
                      <span className="text-sm font-medium">
                        {currentCardIndex + 1} / {flashcards.length}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${((currentCardIndex + 1) / flashcards.length) * 100}%` }}
                      ></div>
                    </div>
                  </div>

                  {/* Flashcard */}
                  <Card className="min-h-[400px] shadow-lg">
                    <CardHeader>
                      <div className="flex justify-between items-center">
                        <div>
                          <CardTitle className="text-lg">แฟลชการ์ด</CardTitle>
                          <CardDescription>
                            ระดับความยาก: {currentCard.difficulty} | ทบทวนครั้งที่: {currentCard.review_count + 1}
                          </CardDescription>
                        </div>
                        <Badge className={currentCard.is_due ? "bg-orange-100 text-orange-600" : "bg-gray-100 text-gray-600"}>
                          {currentCard.is_due ? "ถึงเวลา" : "รอทบทวน"}
                        </Badge>
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

                      {!isFlipped ? (
                        <div className="text-center">
                          <p className="text-gray-600 mb-4">คิดคำตอบแล้วคลิกเพื่อดูคำตอบ</p>
                          <Button
                            onClick={() => setIsFlipped(true)}
                            className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3"
                          >
                            <Eye className="h-4 w-4 mr-2" />
                            แสดงคำตอบ
                          </Button>
                        </div>
                      ) : (
                        <div className="grid grid-cols-3 gap-4">
                          <Button
                            onClick={() => handleAnswer("hard")}
                            variant="outline"
                            className="bg-red-50 text-red-700 border-red-200 hover:bg-red-100 py-6"
                          >
                            <div className="text-center">
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
                              <div className="font-semibold">ง่าย</div>
                              <div className="text-sm opacity-75">ทบทวนใน 7 วัน</div>
                            </div>
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
  )
}
