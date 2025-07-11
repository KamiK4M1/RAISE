"use client"

import { useState, useEffect, useCallback } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Progress } from "@/components/ui/progress"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog"
import {
  Brain,
  ArrowLeft,
  Search,
  Plus,
  Play,
  MoreVertical,
  BookOpen,
  Clock,
  Target,
  Eye,
  Trash2,
  AlertCircle,
} from "lucide-react"
import Link from "next/link"
import { apiService } from "@/lib/api"
import { AuthWrapper } from "@/components/providers/auth-wrpper"

interface FlashcardSet {
  document_id: string
  source_name: string
  filename: string
  total_cards: number
  due_count: number
  mastered_count: number
  created_at: string
  last_reviewed: string
  average_difficulty: string
  completion_rate: number
  is_topic_based?: boolean
}

export default function FlashcardLibraryPage() {
  const [flashcardSets, setFlashcardSets] = useState<FlashcardSet[]>([])
  const [filteredSets, setFilteredSets] = useState<FlashcardSet[]>([])
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedFilter, setSelectedFilter] = useState("all")
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [selectedSet, setSelectedSet] = useState<FlashcardSet | null>(null)
  const [stats, setStats] = useState({
    totalSets: 0,
    totalCards: 0,
    dueCards: 0,
    masteredCards: 0,
  })

  useEffect(() => {
    loadFlashcardSets()
  }, [])

  useEffect(() => {
    filterSets()
  }, [flashcardSets, searchQuery, selectedFilter, filterSets])

  const loadFlashcardSets = async () => {
    try {
      setLoading(true)
      setError(null)

      // Get all flashcard topics and documents
      const [topicsResponse, documentsResponse] = await Promise.all([
        apiService.getFlashcardTopics(),
        apiService.listDocuments(),
      ])

      console.log('Topics response:', topicsResponse)
      console.log('Documents response:', documentsResponse)

      const sets: FlashcardSet[] = []
      let totalCards = 0
      let totalDue = 0
      let totalMastered = 0

      // Process topics
      if (topicsResponse.success && topicsResponse.data?.topics) {
        for (const topic of topicsResponse.data.topics) {
          const topicName = topic.topic_name || topic.name || 'untitled'
          const flashcardsResponse = await apiService.getFlashcardsByDocument(
            `topic_${topicName.replace(/\s+/g, '_')}`,
            0,
            1000
          )
          
          if (flashcardsResponse.success && flashcardsResponse.data?.flashcards) {
            const cards = flashcardsResponse.data.flashcards
            
            // Only include topics that have flashcards
            if (cards.length > 0) {
              const dueCount = cards.filter((card: { is_due: boolean }) => card.is_due).length
              const masteredCount = cards.filter((card: { review_count: number }) => card.review_count >= 5).length
              
              sets.push({
                document_id: `topic_${topicName.replace(/\s+/g, '_')}`,
                source_name: topicName,
                filename: `${topicName}.topic`,
                total_cards: cards.length,
                due_count: dueCount,
                mastered_count: masteredCount,
                created_at: topic.created_at || new Date().toISOString(),
                last_reviewed: topic.last_reviewed || new Date().toISOString(),
                average_difficulty: topic.average_difficulty || 'medium',
                completion_rate: (masteredCount / cards.length) * 100,
                is_topic_based: true,
              })
              
              totalCards += cards.length
              totalDue += dueCount
              totalMastered += masteredCount
            }
          }
        }
      }

      // Process documents
      if (documentsResponse.success && documentsResponse.data) {
        for (const document of documentsResponse.data) {
          if (!document?.document_id) continue
          
          const flashcardsResponse = await apiService.getFlashcardsByDocument(
            document.document_id,
            0,
            1000
          )
          
          if (flashcardsResponse.success && flashcardsResponse.data?.flashcards) {
            const cards = flashcardsResponse.data.flashcards
            
            // Only include documents that have flashcards
            if (cards.length > 0) {
              const dueCount = cards.filter((card: { is_due: boolean }) => card.is_due).length
              const masteredCount = cards.filter((card: { review_count: number }) => card.review_count >= 5).length
              
              sets.push({
                document_id: document.document_id,
                source_name: document.filename || 'Untitled Document',
                filename: document.filename || 'Untitled Document',
                total_cards: cards.length,
                due_count: dueCount,
                mastered_count: masteredCount,
                created_at: document.created_at || new Date().toISOString(),
                last_reviewed: cards[0].created_at || document.created_at || new Date().toISOString(),
                average_difficulty: 'medium',
                completion_rate: (masteredCount / cards.length) * 100,
                is_topic_based: false,
              })
              
              totalCards += cards.length
              totalDue += dueCount
              totalMastered += masteredCount
            }
          }
        }
      }

      setFlashcardSets(sets)
      setStats({
        totalSets: sets.length,
        totalCards,
        dueCards: totalDue,
        masteredCards: totalMastered,
      })
    } catch (err: unknown) {
      console.error('Error loading flashcard sets:', err)
      setError(err instanceof Error ? err.message : 'ไม่สามารถโหลดข้อมูลแฟลชการ์ดได้')
    } finally {
      setLoading(false)
    }
  }

  const filterSets = useCallback(() => {
    let filtered = flashcardSets

    // Filter by search query
    if (searchQuery) {
      filtered = filtered.filter(set => 
        set.source_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        set.filename.toLowerCase().includes(searchQuery.toLowerCase())
      )
    }

    // Filter by type
    switch (selectedFilter) {
      case 'due':
        filtered = filtered.filter(set => set.due_count > 0)
        break
      case 'mastered':
        filtered = filtered.filter(set => set.completion_rate >= 80)
        break
      case 'topics':
        filtered = filtered.filter(set => set.is_topic_based)
        break
      case 'documents':
        filtered = filtered.filter(set => !set.is_topic_based)
        break
      default:
        break
    }

    setFilteredSets(filtered)
  }, [flashcardSets, searchQuery, selectedFilter])

  const handleDeleteSet = (set: FlashcardSet) => {
    setSelectedSet(set)
    setShowDeleteDialog(true)
  }

  const confirmDelete = async () => {
    if (!selectedSet) return
    
    try {
      if (selectedSet.is_topic_based) {
        // Handle topic deletion logic here
        console.log('Delete topic:', selectedSet.source_name)
      } else {
        await apiService.deleteDocument(selectedSet.document_id)
      }
      
      await loadFlashcardSets()
      setShowDeleteDialog(false)
      setSelectedSet(null)
    } catch (error) {
      console.error('Error deleting set:', error)
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
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
          <p className="text-gray-600">กำลังโหลดคลังแฟลชการ์ด...</p>
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
          <Button onClick={loadFlashcardSets} className="bg-purple-600 hover:bg-purple-700">
            ลองใหม่
          </Button>
        </div>
      </div>
    )
  }

  return (
    <AuthWrapper>
      <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white border-b sticky top-0 z-40">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Link href="/dashboard">
              <Button variant="ghost" size="sm" className="text-gray-600 hover:text-gray-900">
                <ArrowLeft className="h-4 w-4 mr-2" />
                กลับ
              </Button>
            </Link>
            <div className="flex items-center space-x-2">
              <Brain className="h-8 w-8 text-purple-600" />
              <div>
                <h1 className="text-xl font-bold text-gray-900">คลังแฟลชการ์ด</h1>
                <p className="text-sm text-gray-600">จัดการและทบทวนแฟลชการ์ดทั้งหมด</p>
              </div>
            </div>
          </div>
          <Link href="/flashcards/generate">
            <Button className="bg-purple-600 hover:bg-purple-700 relative z-50">
              <Plus className="h-4 w-4 mr-2" />
              สร้างชุดใหม่
            </Button>
          </Link>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-8">
        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <Card className="border-0 shadow-sm bg-gradient-to-r from-purple-50 to-purple-100">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-purple-600 font-medium">ชุดทั้งหมด</p>
                    <p className="text-2xl font-bold text-purple-800">{stats.totalSets}</p>
                  </div>
                  <BookOpen className="h-8 w-8 text-purple-600" />
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <Card className="border-0 shadow-sm bg-gradient-to-r from-blue-50 to-blue-100">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-blue-600 font-medium">การ์ดทั้งหมด</p>
                    <p className="text-2xl font-bold text-blue-800">{stats.totalCards}</p>
                  </div>
                  <Brain className="h-8 w-8 text-blue-600" />
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <Card className="border-0 shadow-sm bg-gradient-to-r from-orange-50 to-orange-100">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-orange-600 font-medium">ถึงเวลาทบทวน</p>
                    <p className="text-2xl font-bold text-orange-800">{stats.dueCards}</p>
                  </div>
                  <Clock className="h-8 w-8 text-orange-600" />
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <Card className="border-0 shadow-sm bg-gradient-to-r from-green-50 to-green-100">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-green-600 font-medium">เรียนรู้แล้ว</p>
                    <p className="text-2xl font-bold text-green-800">{stats.masteredCards}</p>
                  </div>
                  <Target className="h-8 w-8 text-green-600" />
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Search and Filter */}
        <Card className="border-0 shadow-sm mb-6">
          <CardContent className="p-6">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="ค้นหาชุดแฟลชการ์ด..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
              <div className="flex space-x-2">
                <Button
                  variant={selectedFilter === 'all' ? 'default' : 'outline'}
                  onClick={() => setSelectedFilter('all')}
                  className={selectedFilter === 'all' ? 'bg-purple-600 hover:bg-purple-700' : ''}
                >
                  ทั้งหมด
                </Button>
                <Button
                  variant={selectedFilter === 'due' ? 'default' : 'outline'}
                  onClick={() => setSelectedFilter('due')}
                  className={selectedFilter === 'due' ? 'bg-orange-600 hover:bg-orange-700' : ''}
                >
                  ถึงเวลาทบทวน
                </Button>
                <Button
                  variant={selectedFilter === 'mastered' ? 'default' : 'outline'}
                  onClick={() => setSelectedFilter('mastered')}
                  className={selectedFilter === 'mastered' ? 'bg-green-600 hover:bg-green-700' : ''}
                >
                  เรียนรู้แล้ว
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Flashcard Sets Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <AnimatePresence>
            {filteredSets.map((set, index) => (
              <motion.div
                key={set.document_id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ delay: index * 0.1 }}
                whileHover={{ y: -5 }}
                className="group"
              >
                <Card className="border-0 shadow-sm hover:shadow-lg transition-all duration-300 overflow-hidden">
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          {set.is_topic_based ? (
                            <Badge className="bg-indigo-100 text-indigo-600">หัวข้อ</Badge>
                          ) : (
                            <Badge className="bg-blue-100 text-blue-600">เอกสาร</Badge>
                          )}
                          {set.due_count > 0 && (
                            <Badge className="bg-orange-100 text-orange-600">
                              {set.due_count} ถึงเวลา
                            </Badge>
                          )}
                        </div>
                        <CardTitle className="text-lg line-clamp-2">{set.source_name}</CardTitle>
                        <CardDescription className="text-sm">
                          {set.total_cards} การ์ด • สร้างเมื่อ {formatTimeAgo(set.created_at)}
                        </CardDescription>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="opacity-0 group-hover:opacity-100 transition-opacity"
                        onClick={() => handleDeleteSet(set)}
                      >
                        <MoreVertical className="h-4 w-4" />
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent className="pt-0">
                    <div className="space-y-4">
                      {/* Progress Bar */}
                      <div>
                        <div className="flex justify-between text-sm text-gray-600 mb-1">
                          <span>ความคืบหน้า</span>
                          <span>{Math.round(set.completion_rate)}%</span>
                        </div>
                        <Progress value={set.completion_rate} className="h-2" />
                      </div>

                      {/* Stats */}
                      <div className="grid grid-cols-3 gap-4 text-center">
                        <div>
                          <p className="text-2xl font-bold text-blue-600">{set.total_cards}</p>
                          <p className="text-xs text-gray-500">ทั้งหมด</p>
                        </div>
                        <div>
                          <p className="text-2xl font-bold text-orange-600">{set.due_count}</p>
                          <p className="text-xs text-gray-500">ถึงเวลา</p>
                        </div>
                        <div>
                          <p className="text-2xl font-bold text-green-600">{set.mastered_count}</p>
                          <p className="text-xs text-gray-500">เรียนรู้แล้ว</p>
                        </div>
                      </div>

                      {/* Action Buttons */}
                      <div className="flex space-x-2">
                        <Link href={`/flashcards/${set.document_id}`} className="flex-1">
                          <Button 
                            variant="outline" 
                            className="w-full"
                          >
                            <Eye className="h-4 w-4 mr-2" />
                            ดูการ์ด
                          </Button>
                        </Link>
                        {set.due_count > 0 && (
                          <Link href={`/flashcards/${set.document_id}?mode=study`} className="flex-1">
                            <Button 
                              className="w-full bg-purple-600 hover:bg-purple-700"
                            >
                              <Play className="h-4 w-4 mr-2" />
                              ทบทวน
                            </Button>
                          </Link>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>

        {/* Empty State */}
        {filteredSets.length === 0 && !loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-12"
          >
            <Brain className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              {searchQuery || selectedFilter !== 'all' ? 'ไม่พบชุดแฟลชการ์ด' : 'ยังไม่มีชุดแฟลชการ์ด'}
            </h3>
            <p className="text-gray-600 mb-6">
              {searchQuery || selectedFilter !== 'all' 
                ? 'ลองปรับการค้นหาหรือตัวกรองของคุณ' 
                : 'เริ่มต้นสร้างชุดแฟลชการ์ดแรกของคุณ'}
            </p>
            <Link href="/flashcards/generate">
              <Button className="bg-purple-600 hover:bg-purple-700">
                <Plus className="h-4 w-4 mr-2" />
                สร้างชุดแฟลชการ์ดใหม่
              </Button>
            </Link>
          </motion.div>
        )}
      </div>

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>ลบชุดแฟลชการ์ด</DialogTitle>
            <DialogDescription>
              คุณแน่ใจหรือไม่ว่าต้องการลบชุดแฟลชการ์ด &quot;{selectedSet?.source_name}&quot; 
              การกระทำนี้จะลบแฟลชการ์ดทั้งหมด {selectedSet?.total_cards} ใบ และไม่สามารถยกเลิกได้
            </DialogDescription>
          </DialogHeader>
          <div className="flex justify-end space-x-2">
            <Button variant="outline" onClick={() => setShowDeleteDialog(false)}>
              ยกเลิก
            </Button>
            <Button variant="destructive" onClick={confirmDelete}>
              <Trash2 className="h-4 w-4 mr-2" />
              ลบ
            </Button>
          </div>
        </DialogContent>
      </Dialog>
      </div>
    </AuthWrapper>
  )
}