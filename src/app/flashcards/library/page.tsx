"use client"

import { useState, useEffect } from "react"
import { Button } from "../../../components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Brain, ArrowLeft, Clock, CheckCircle, XCircle, BookOpen, Folder, Calendar, Eye, Trash2, RotateCcw, Play } from "lucide-react"
import Link from "next/link"
import { apiService } from "@/lib/api"
import { useRouter } from "next/navigation"

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
  overdue_hours?: number
}

interface TopicData {
  document_id: string
  topic_name: string
  flashcard_count: number
  last_reviewed: string | null
  due_count: number
}

export default function FlashcardLibraryPage() {
  const [allFlashcards, setAllFlashcards] = useState<FlashcardData[]>([])
  const [dueFlashcards, setDueFlashcards] = useState<FlashcardData[]>([])
  const [topics, setTopics] = useState<TopicData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState("all")
  const router = useRouter()

  useEffect(() => {
    loadFlashcardData()
  }, [])

  const loadFlashcardData = async () => {
    try {
      setLoading(true)
      
      // Load all data in parallel
      const [allResponse, dueResponse, topicsResponse] = await Promise.all([
        apiService.getAllUserFlashcards(0, 100),
        apiService.getDueFlashcards(50),
        apiService.getFlashcardTopics()
      ])

      if (allResponse.success && allResponse.data) {
        setAllFlashcards(allResponse.data.flashcards || [])
      }

      if (dueResponse.success && dueResponse.data) {
        setDueFlashcards(dueResponse.data.flashcards || [])
      }

      if (topicsResponse.success && topicsResponse.data) {
        setTopics(topicsResponse.data.topics || [])
      }

    } catch (error) {
      console.error('Error loading flashcard data:', error)
      setError(error instanceof Error ? error.message : 'ไม่สามารถโหลดข้อมูลแฟลชการ์ดได้')
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteFlashcard = async (cardId: string) => {
    if (!confirm('คุณแน่ใจหรือไม่ที่จะลบแฟลชการ์ดนี้?')) return

    try {
      const response = await apiService.deleteFlashcard(cardId)
      if (response.success) {
        // Remove from local state
        setAllFlashcards(prev => prev.filter(card => card.card_id !== cardId))
        setDueFlashcards(prev => prev.filter(card => card.card_id !== cardId))
      }
    } catch (error) {
      console.error('Error deleting flashcard:', error)
      alert('ไม่สามารถลบแฟลชการ์ดได้')
    }
  }

  const handleResetFlashcard = async (cardId: string) => {
    if (!confirm('คุณแน่ใจหรือไม่ที่จะรีเซ็ตความคืบหน้าของแฟลชการ์ดนี้?')) return

    try {
      const response = await apiService.resetFlashcard(cardId)
      if (response.success) {
        // Reload data to get updated info
        loadFlashcardData()
      }
    } catch (error) {
      console.error('Error resetting flashcard:', error)
      alert('ไม่สามารถรีเซ็ตแฟลชการ์ดได้')
    }
  }

  const startReviewSession = (docId?: string) => {
    if (docId) {
      router.push(`/flashcards/${docId}`)
    } else {
      router.push('/flashcards')
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

  const getUrgencyColor = (urgency: string, isDue: boolean) => {
    if (!isDue) return "bg-gray-100 text-gray-600"
    
    switch (urgency) {
      case "high": return "bg-red-100 text-red-600"
      case "medium": return "bg-yellow-100 text-yellow-600"
      case "low": return "bg-green-100 text-green-600"
      default: return "bg-blue-100 text-blue-600"
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">กำลังโหลดคลังแฟลชการ์ด...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-6">
          <XCircle className="h-16 w-16 text-red-600 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">ไม่สามารถโหลดข้อมูลได้</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <Button onClick={loadFlashcardData} className="bg-blue-600 hover:bg-blue-700">
            <RotateCcw className="h-4 w-4 mr-2" />
            ลองใหม่
          </Button>
        </div>
      </div>
    )
  }

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
              <span className="text-2xl font-bold text-gray-900">คลังแฟลชการ์ด</span>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Button
              onClick={() => startReviewSession()}
              className="bg-blue-600 hover:bg-blue-700"
            >
              <Play className="h-4 w-4 mr-2" />
              เริ่มทบทวน
            </Button>
            <Link href="/flashcards/generate">
              <Button variant="outline">
                สร้างแฟลชการ์ด
              </Button>
            </Link>
          </div>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-8">
        <div className="max-w-6xl mx-auto">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <Card>
              <CardContent className="p-6 text-center">
                <BookOpen className="h-8 w-8 text-blue-600 mx-auto mb-2" />
                <p className="text-2xl font-bold text-blue-600">{allFlashcards.length}</p>
                <p className="text-sm text-gray-600">แฟลชการ์ดทั้งหมด</p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6 text-center">
                <Clock className="h-8 w-8 text-orange-600 mx-auto mb-2" />
                <p className="text-2xl font-bold text-orange-600">{dueFlashcards.length}</p>
                <p className="text-sm text-gray-600">ถึงเวลาทบทวน</p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6 text-center">
                <Folder className="h-8 w-8 text-green-600 mx-auto mb-2" />
                <p className="text-2xl font-bold text-green-600">{topics.length}</p>
                <p className="text-sm text-gray-600">หัวข้อ</p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6 text-center">
                <CheckCircle className="h-8 w-8 text-purple-600 mx-auto mb-2" />
                <p className="text-2xl font-bold text-purple-600">
                  {allFlashcards.filter(card => card.review_count > 0).length}
                </p>
                <p className="text-sm text-gray-600">ทบทวนแล้ว</p>
              </CardContent>
            </Card>
          </div>

          {/* Main Content */}
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="all">แฟลชการ์ดทั้งหมด</TabsTrigger>
              <TabsTrigger value="due">ถึงเวลาทบทวน ({dueFlashcards.length})</TabsTrigger>
              <TabsTrigger value="topics">หัวข้อ ({topics.length})</TabsTrigger>
            </TabsList>

            <TabsContent value="all" className="space-y-4">
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-semibold">แฟลชการ์ดทั้งหมด</h2>
                <p className="text-sm text-gray-600">{allFlashcards.length} แฟลชการ์ด</p>
              </div>
              
              <div className="grid gap-4">
                {allFlashcards.map((card) => (
                  <Card key={card.card_id} className="hover:shadow-md transition-shadow">
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
                          <Badge className={getUrgencyColor(card.urgency, card.is_due)}>
                            {card.is_due ? 'ถึงเวลา' : 'รอทบทวน'}
                          </Badge>
                        </div>
                      </div>
                      
                      <div className="flex justify-between items-center">
                        <div className="text-xs text-gray-500">
                          <Calendar className="h-3 w-3 inline mr-1" />
                          ทบทวนครั้งถัดไป: {new Date(card.next_review).toLocaleDateString('th-TH')}
                        </div>
                        <div className="flex items-center space-x-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleResetFlashcard(card.card_id)}
                          >
                            <RotateCcw className="h-3 w-3" />
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleDeleteFlashcard(card.card_id)}
                            className="text-red-600 hover:text-red-700 hover:bg-red-50"
                          >
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </TabsContent>

            <TabsContent value="due" className="space-y-4">
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-semibold">แฟลชการ์ดที่ถึงเวลาทบทวน</h2>
                {dueFlashcards.length > 0 && (
                  <Button
                    onClick={() => startReviewSession()}
                    className="bg-orange-600 hover:bg-orange-700"
                  >
                    <Play className="h-4 w-4 mr-2" />
                    เริ่มทบทวนทันที
                  </Button>
                )}
              </div>
              
              {dueFlashcards.length === 0 ? (
                <Card>
                  <CardContent className="p-8 text-center">
                    <CheckCircle className="h-12 w-12 text-green-600 mx-auto mb-4" />
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">เยี่ยม! ไม่มีแฟลชการ์ดที่ถึงเวลาทบทวน</h3>
                    <p className="text-gray-600">คุณทบทวนครบทุกใบแล้ว กลับมาใหม่พรุ่งนี้</p>
                  </CardContent>
                </Card>
              ) : (
                <div className="grid gap-4">
                  {dueFlashcards.map((card) => (
                    <Card key={card.card_id} className="border-orange-200 hover:shadow-md transition-shadow">
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
                              {card.overdue_hours && card.overdue_hours > 0 && (
                                <>
                                  <span>•</span>
                                  <span className="text-orange-600">
                                    เลยเวลา {Math.round(card.overdue_hours)} ชั่วโมง
                                  </span>
                                </>
                              )}
                            </div>
                          </div>
                          <Badge className="bg-orange-100 text-orange-600">
                            {card.urgency === 'high' ? 'เร่งด่วน' : 'ถึงเวลา'}
                          </Badge>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </TabsContent>

            <TabsContent value="topics" className="space-y-4">
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-semibold">หัวข้อแฟลชการ์ด</h2>
                <p className="text-sm text-gray-600">{topics.length} หัวข้อ</p>
              </div>
              
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {topics.map((topic) => (
                  <Card key={topic.document_id} className="hover:shadow-md transition-shadow cursor-pointer"
                        onClick={() => router.push(`/flashcards/${topic.document_id}`)}>
                    <CardHeader>
                      <div className="flex justify-between items-start">
                        <CardTitle className="text-lg line-clamp-2">{topic.topic_name}</CardTitle>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={(e) => {
                            e.stopPropagation()
                            startReviewSession(topic.document_id)
                          }}
                        >
                          <Play className="h-3 w-3" />
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">แฟลชการ์ด:</span>
                          <span className="font-medium">{topic.flashcard_count} ใบ</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">ถึงเวลาทบทวน:</span>
                          <span className={topic.due_count > 0 ? "font-medium text-orange-600" : "text-gray-500"}>
                            {topic.due_count} ใบ
                          </span>
                        </div>
                        {topic.last_reviewed && (
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-600">ทบทวนล่าสุด:</span>
                            <span className="text-gray-500">
                              {formatTimeAgo(topic.last_reviewed)}
                            </span>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  )
}