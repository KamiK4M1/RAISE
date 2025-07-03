"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { 
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog"
import {
  Brain,
  ArrowLeft,
  FileText,
  Plus,
  Loader2,
  AlertCircle,
  BookOpen,
  Target,
  Settings,
} from "lucide-react"
import Link from "next/link"
import { apiService } from "@/lib/api"
import { Document } from "@/types/api"

export default function GenerateFlashcardsPage() {
  const router = useRouter()
  const [documents, setDocuments] = useState<Document[]>([])
  const [selectedDocument, setSelectedDocument] = useState<string>("")
  const [customTopic, setCustomTopic] = useState("")
  const [generationType, setGenerationType] = useState<"document" | "topic">("document")
  const [isGenerating, setIsGenerating] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showSuccessDialog, setShowSuccessDialog] = useState(false)
  const [generatedFlashcards, setGeneratedFlashcards] = useState<any[]>([])

  // Flashcard options
  const [flashcardCount, setFlashcardCount] = useState(10)
  const [difficulty, setDifficulty] = useState("medium")
  const [bloomLevel, setBloomLevel] = useState("all")

  useEffect(() => {
    loadDocuments()
  }, [])

  const loadDocuments = async () => {
    try {
      setLoading(true)
      const response = await apiService.listDocuments()
      if (response.success && response.data) {
        // Filter only completed documents
        console.log(response.data)
        const completedDocs = response.data.filter(doc => doc.status === 'completed')
        setDocuments(completedDocs)
      }
    } catch (error) {
      console.error('Error loading documents:', error)
      setError('ไม่สามารถโหลดรายการเอกสารได้')
    } finally {
      setLoading(false)
    }
  }

  const handleGenerate = async () => {
    if (generationType === "document" && !selectedDocument) {
      setError('กรุณาเลือกเอกสาร')
      return
    }

    if (generationType === "topic" && !customTopic.trim()) {
      setError('กรุณาใส่หัวข้อที่ต้องการสร้างแฟลชการ์ด')
      return
    }

    setIsGenerating(true)
    setError(null)

    try {
      let response
      if (generationType === "document") {
        // Generate from document
        response = await apiService.generateFlashcards(selectedDocument, {
          count: flashcardCount,
          difficulty: difficulty,
          bloom_level: bloomLevel !== "all" ? bloomLevel : undefined,
        })
      } else {
        // Generate from topic
        response = await apiService.generateFlashcardsFromTopic(
          customTopic.trim(),
          flashcardCount,
          difficulty
        )
      }

      if (response.success && response.data) {
        setGeneratedFlashcards(response.data)
        setShowSuccessDialog(true)
      } else {
        throw new Error(response.message || 'ไม่สามารถสร้างแฟลชการ์ดได้')
      }
    } catch (err: any) {
      setError(err.message || 'เกิดข้อผิดพลาดในการสร้างแฟลชการ์ด')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleStartReview = () => {
    setShowSuccessDialog(false)
    if (generationType === "document") {
      router.push(`/flashcards/${selectedDocument}`)
    } else {
      // For topic-based flashcards, go to general flashcards page
      router.push('/flashcards')
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">กำลังโหลดข้อมูล...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white border-b">
        <div className="container mx-auto px-4 py-4 flex items-center">
          <Link href="/dashboard">
            <Button variant="ghost" size="sm" className="text-gray-600 hover:text-gray-900">
              <ArrowLeft className="h-4 w-4 mr-2" />
              กลับหน้าหลัก
            </Button>
          </Link>
          <div className="flex items-center space-x-2 ml-4">
            <Brain className="h-8 w-8 text-blue-600" />
            <span className="text-2xl font-bold text-gray-900">RAISE</span>
          </div>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">สร้างแฟลชการ์ดใหม่</h1>
            <p className="text-gray-600">เลือกวิธีการสร้างแฟลชการ์ดที่เหมาะกับการเรียนรู้ของคุณ</p>
          </div>

          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center">
              <AlertCircle className="h-5 w-5 text-red-600 mr-3" />
              <span className="text-red-700">{error}</span>
            </div>
          )}

          <div className="grid lg:grid-cols-3 gap-8">
            {/* Generation Options */}
            <div className="lg:col-span-2 space-y-6">
              {/* Generation Type Selection */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Target className="h-5 w-5 mr-2 text-blue-600" />
                    เลือกแหล่งเนื้อหา
                  </CardTitle>
                  <CardDescription>
                    เลือกว่าต้องการสร้างแฟลชการ์ดจากเอกสารที่มีอยู่ หรือจากหัวข้อที่กำหนดเอง
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Card 
                      className={`cursor-pointer transition-all ${
                        generationType === "document" 
                          ? "border-blue-500 bg-blue-50" 
                          : "border-gray-200 hover:border-gray-300"
                      }`}
                      onClick={() => setGenerationType("document")}
                    >
                      <CardContent className="p-6 text-center">
                        <FileText className="h-12 w-12 text-blue-600 mx-auto mb-4" />
                        <h3 className="font-semibold mb-2">จากเอกสาร</h3>
                        <p className="text-sm text-gray-600">สร้างจากเอกสารที่อัปโหลดแล้ว</p>
                      </CardContent>
                    </Card>

                    <Card 
                      className={`cursor-pointer transition-all ${
                        generationType === "topic" 
                          ? "border-blue-500 bg-blue-50" 
                          : "border-gray-200 hover:border-gray-300"
                      }`}
                      onClick={() => setGenerationType("topic")}
                    >
                      <CardContent className="p-6 text-center">
                        <BookOpen className="h-12 w-12 text-purple-600 mx-auto mb-4" />
                        <h3 className="font-semibold mb-2">จากหัวข้อ</h3>
                        <p className="text-sm text-gray-600">ใส่หัวข้อที่ต้องการเรียนรู้</p>
                      </CardContent>
                    </Card>
                  </div>
                </CardContent>
              </Card>

              {/* Document Selection */}
              {generationType === "document" && (
                <Card>
                  <CardHeader>
                    <CardTitle>เลือกเอกสาร</CardTitle>
                    <CardDescription>
                      เลือกเอกสารที่ต้องการสร้างแฟลชการ์ด (เฉพาะเอกสารที่ประมวลผลเสร็จแล้ว)
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {documents.length === 0 ? (
                      <div className="text-center py-8">
                        <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                        <p className="text-gray-600 mb-2">ไม่มีเอกสารที่พร้อมใช้งาน</p>
                        <p className="text-sm text-gray-500 mb-4">กรุณาตรวจสอบ Browser Console (F12) เพื่อดูข้อมูลการโหลด</p>
                        <Link href="/upload">
                          <Button className="bg-blue-600 hover:bg-blue-700">
                            อัปโหลดเอกสาร
                          </Button>
                        </Link>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {documents.map((doc) => {
                          const statusColor = doc.processing_status === 'completed' || doc.status === 'completed' ? 'text-green-600' : 'text-amber-600'
                          const statusText = doc.processing_status === 'completed' || doc.status === 'completed' ? 'พร้อมใช้งาน' : `สถานะ: ${doc.processing_status || doc.status || 'ไม่ทราบ'}`
                          
                          return (
                            <Card 
                              key={doc.document_id}
                              className={`cursor-pointer transition-all ${
                                selectedDocument === doc.document_id
                                  ? "border-blue-500 bg-blue-50"
                                  : "border-gray-200 hover:border-gray-300"
                              }`}
                              onClick={() => setSelectedDocument(doc.document_id)}
                            >
                              <CardContent className="p-4">
                                <div className="flex items-center justify-between">
                                  <div className="flex items-center space-x-3">
                                    <FileText className="h-5 w-5 text-blue-600" />
                                    <div>
                                      <p className="font-medium">{doc.filename}</p>
                                      <p className="text-sm text-gray-500">
                                        {new Date(doc.created_at).toLocaleDateString('th-TH')}
                                      </p>
                                    </div>
                                  </div>
                                  <div className={`text-sm font-medium ${statusColor}`}>
                                    {statusText}
                                  </div>
                                </div>
                              </CardContent>
                            </Card>
                          )
                        })}
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}

              {/* Topic Input */}
              {generationType === "topic" && (
                <Card>
                  <CardHeader>
                    <CardTitle>ใส่หัวข้อที่ต้องการเรียนรู้</CardTitle>
                    <CardDescription>
                      ระบุหัวข้อหรือเนื้อหาที่ต้องการสร้างแฟลชการ์ด เช่น "ประวัติศาสตร์ไทย", "คณิตศาสตร์ชั้นม.6"
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div>
                        <Label htmlFor="topic">หัวข้อ</Label>
                        <Input
                          id="topic"
                          value={customTopic}
                          onChange={(e) => setCustomTopic(e.target.value)}
                          placeholder="เช่น ประวัติศาสตร์ไทย สมัยอยุธยา"
                          className="mt-1"
                        />
                      </div>
                      <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                        <p className="text-sm text-green-800">
                          <strong>เคล็ดลับ:</strong> ระบุหัวข้อให้ละเอียดเพื่อให้ AI สร้างแฟลชการ์ดที่มีคุณภาพมากขึ้น
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>

            {/* Settings */}
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Settings className="h-5 w-5 mr-2 text-gray-600" />
                    ตั้งค่าแฟลชการ์ด
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label htmlFor="count">จำนวนการ์ด</Label>
                    <Input
                      id="count"
                      type="number"
                      value={flashcardCount}
                      onChange={(e) => setFlashcardCount(parseInt(e.target.value) || 10)}
                      min="1"
                      max="50"
                      className="mt-1"
                    />
                  </div>

                  <div>
                    <Label htmlFor="difficulty">ระดับความยาก</Label>
                    <select
                      id="difficulty"
                      value={difficulty}
                      onChange={(e) => setDifficulty(e.target.value)}
                      className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="easy">ง่าย</option>
                      <option value="medium">ปานกลาง</option>
                      <option value="hard">ยาก</option>
                    </select>
                  </div>

                  <div>
                    <Label htmlFor="bloom">ระดับ Bloom's Taxonomy</Label>
                    <select
                      id="bloom"
                      value={bloomLevel}
                      onChange={(e) => setBloomLevel(e.target.value)}
                      className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="all">ทุกระดับ</option>
                      <option value="remember">จำ (Remember)</option>
                      <option value="understand">เข้าใจ (Understand)</option>
                      <option value="apply">ประยุกต์ (Apply)</option>
                      <option value="analyze">วิเคราะห์ (Analyze)</option>
                      <option value="evaluate">ประเมิน (Evaluate)</option>
                      <option value="create">สร้าง (Create)</option>
                    </select>
                  </div>
                </CardContent>
              </Card>

              {/* Generate Button */}
              <Button
                onClick={handleGenerate}
                disabled={isGenerating || (generationType === "document" && !selectedDocument) || (generationType === "topic" && !customTopic.trim())}
                className="w-full bg-blue-600 hover:bg-blue-700 py-3"
                size="lg"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                    กำลังสร้างแฟลชการ์ด...
                  </>
                ) : (
                  <>
                    <Plus className="h-5 w-5 mr-2" />
                    สร้างแฟลชการ์ด
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Success Dialog */}
      <Dialog open={showSuccessDialog} onOpenChange={setShowSuccessDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>สร้างแฟลชการ์ดสำเร็จ!</DialogTitle>
            <DialogDescription>
              สร้างแฟลชการ์ดจำนวน {generatedFlashcards.length} ใบเรียบร้อยแล้ว พร้อมเริ่มทบทวนได้เลย
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSuccessDialog(false)}>
              ปิด
            </Button>
            <Button onClick={handleStartReview} className="bg-blue-600 hover:bg-blue-700">
              เริ่มทบทวน
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}