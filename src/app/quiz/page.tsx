"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { BloomsQuizInterface } from "@/components/quiz/BloomsQuizInterface"
import { Brain, BookOpen, Target, Clock, ArrowRight, Upload } from "lucide-react"
import Link from "next/link"
import { apiService } from "@/lib/api"
import { Document } from "@/types/api"
import { AuthWrapper } from "@/components/providers/auth-wrpper"

export default function QuizPage() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [selectedDocument, setSelectedDocument] = useState("")
  const [showQuiz, setShowQuiz] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadDocuments = async () => {
      try {
        setLoading(true)
        const response = await apiService.listDocuments()
        if (response.success && response.data) {
          // Filter only completed documents
          const completedDocs = response.data.filter(doc => 
            doc.processing_status === 'completed' || doc.status === 'completed'
          )
          setDocuments(completedDocs)
          if (completedDocs.length > 0) {
            setSelectedDocument(completedDocs[0].document_id)
          }
        } else {
          throw new Error(response.message || 'Failed to load documents')
        }
      } catch (error) {
        console.error('Error loading documents:', error)
        setError(error instanceof Error ? error.message : 'Failed to load documents')
      } finally {
        setLoading(false)
      }
    }

    loadDocuments()
  }, [])

  const handleStartQuiz = () => {
    if (selectedDocument) {
      setShowQuiz(true)
    }
  }

  const handleBackToSetup = () => {
    setShowQuiz(false)
  }

  if (showQuiz && selectedDocument) {
    return (
      <BloomsQuizInterface 
        documentId={selectedDocument}
        onBack={handleBackToSetup}
      />
    )
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Brain className="h-12 w-12 text-blue-600 mx-auto mb-4 animate-spin" />
          <p className="text-gray-600">กำลังโหลดเอกสาร...</p>
        </div>
      </div>
    )
  }

  if (error && documents.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <CardTitle className="text-red-600">เกิดข้อผิดพลาด</CardTitle>
            <CardDescription>{error}</CardDescription>
          </CardHeader>
          <CardContent>
            <Button 
              onClick={() => window.location.reload()} 
              className="w-full"
            >
              ลองใหม่
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (documents.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <CardTitle>ไม่มีเอกสารที่พร้อมใช้งาน</CardTitle>
            <CardDescription>
              คุณจำเป็นต้องอัปโหลดและประมวลผลเอกสารอย่างน้อย 1 ฉบับก่อนที่จะสามารถทำแบบทดสอบได้
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link href="/upload">
              <Button className="w-full">
                <Upload className="h-4 w-4 mr-2" />
                อัปโหลดเอกสาร
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <AuthWrapper>
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50">
        {/* Navigation */}
        <nav className="bg-white/80 backdrop-blur-sm border-b sticky top-0 z-50">
          <div className="container mx-auto px-4 py-4 flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link href="/dashboard">
                <Button variant="ghost" size="sm" className="text-gray-600 hover:text-gray-900">
                  <ArrowRight className="h-4 w-4 mr-2 rotate-180" />
                  กลับ
                </Button>
              </Link>
              <div className="flex items-center space-x-2">
                <div className="p-2 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg">
                  <Brain className="h-6 w-6 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-gray-900">แบบทดสอบ AI</h1>
                  <p className="text-sm text-gray-600">ครอบคลุมทุกระดับ Bloom's Taxonomy</p>
                </div>
              </div>
            </div>
          </div>
        </nav>

      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-12">
            <div className="inline-flex items-center justify-center p-3 bg-gradient-to-r from-blue-100 to-purple-100 rounded-full mb-6">
              <Target className="h-8 w-8 text-blue-600" />
            </div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-4">
              แบบทดสอบ Bloom's Taxonomy
            </h1>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              ทดสอบความรู้ความเข้าใจของคุณในทุกระดับ ตั้งแต่การจำไปจนถึงการสร้างสรรค์
            </p>
          </div>

          {/* Bloom's Taxonomy Overview */}
          <Card className="border-0 shadow-lg mb-8 bg-white/50 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center text-xl">
                <Brain className="h-6 w-6 mr-3 text-blue-600" />
                ระดับการเรียนรู้ตาม Bloom's Taxonomy
              </CardTitle>
              <CardDescription className="text-base">
                แบบทดสอบนี้จะประเมินความสามารถของคุณในทุกระดับของการคิด
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                {[
                  { level: "จำ (Remember)", description: "การระลึกข้อเท็จจริงและแนวคิด", color: "bg-blue-50 text-blue-700", icon: "🧠" },
                  { level: "เข้าใจ (Understand)", description: "การตีความและอธิบายความหมาย", color: "bg-green-50 text-green-700", icon: "💡" },
                  { level: "ประยุกต์ (Apply)", description: "การนำความรู้ไปใช้ในสถานการณ์ใหม่", color: "bg-yellow-50 text-yellow-700", icon: "🔧" },
                  { level: "วิเคราะห์ (Analyze)", description: "การแยกแยะและหาความสัมพันธ์", color: "bg-orange-50 text-orange-700", icon: "🔍" },
                  { level: "ประเมิน (Evaluate)", description: "การตัดสินใจและการวิจารณ์", color: "bg-purple-50 text-purple-700", icon: "⚖️" },
                  { level: "สร้างสรรค์ (Create)", description: "การสร้างใหม่และการออกแบบ", color: "bg-pink-50 text-pink-700", icon: "✨" }
                ].map((item, index) => (
                  <div key={index} className={`p-4 rounded-lg border ${item.color}`}>
                    <div className="flex items-center space-x-2 mb-2">
                      <span className="text-xl">{item.icon}</span>
                      <h3 className="font-semibold">{item.level}</h3>
                    </div>
                    <p className="text-sm opacity-80">{item.description}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Document Selection */}
          <Card className="border-0 shadow-lg mb-8 bg-white/50 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center text-xl">
                <BookOpen className="h-6 w-6 mr-3 text-blue-600" />
                เลือกเอกสารสำหรับสร้างแบบทดสอบ
              </CardTitle>
              <CardDescription className="text-base">
                เลือกเอกสารที่คุณต้องการให้ AI สร้างแบบทดสอบตาม Bloom's Taxonomy
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <Select value={selectedDocument} onValueChange={setSelectedDocument}>
                  <SelectTrigger className="h-12 text-base">
                    <SelectValue placeholder="เลือกเอกสาร" />
                  </SelectTrigger>
                  <SelectContent>
                    {documents.map((doc) => (
                      <SelectItem key={doc.document_id} value={doc.document_id}>
                        <div className="flex items-center justify-between w-full">
                          <span className="truncate mr-4">{doc.filename}</span>
                          <span className="text-xs text-gray-500">
                            ({(doc.file_size / 1024).toFixed(1)} KB)
                          </span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                {selectedDocument && (
                  <div className="p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-200">
                    <h4 className="font-medium text-blue-900 mb-2">แบบทดสอบจะประกอบด้วย:</h4>
                    <ul className="text-sm text-blue-800 space-y-1">
                      <li>• คำถาม 15 ข้อ ครอบคลุมทุกระดับ Bloom's Taxonomy</li>
                      <li>• เวลาทำข้อสอบ 20 นาที</li>
                      <li>• คำอธิบายละเอียดสำหรับทุกข้อ</li>
                      <li>• การวิเคราะห์ผลงานแยกตามระดับการคิด</li>
                      <li>• คำแนะนำสำหรับการศึกษาต่อ</li>
                    </ul>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Start Quiz Button */}
          <div className="text-center">
            {error && (
              <p className="text-red-600 mb-4 text-sm">{error}</p>
            )}
            <Button
              onClick={handleStartQuiz}
              disabled={!selectedDocument}
              size="lg"
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-8 py-6 text-lg font-semibold shadow-2xl border-0"
            >
              <Brain className="h-6 w-6 mr-3" />
              เริ่มทำแบบทดสอบ
              <ArrowRight className="h-6 w-6 ml-3" />
            </Button>
            <p className="text-sm text-gray-600 mt-4">
              แบบทดสอบจะใช้เวลา 20 นาที และครอบคลุมทุกระดับการคิด
            </p>
          </div>
        </div>
      </div>
      </div>
    </AuthWrapper>
  )
}