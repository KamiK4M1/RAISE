"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { motion, AnimatePresence } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { Slider } from "@/components/ui/slider"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import {
  Brain,
  ArrowLeft,
  FileText,
  Loader2,
  AlertCircle,
  BookOpen,
  Target,
  Settings,
  Upload,
  Sparkles,
  CheckCircle2,
  Clock,
  Stars,
  Play,
  Wand2,
  Hash,
} from "lucide-react"
import Link from "next/link"
import { apiService } from "@/lib/api"
import type { Document } from "@/types/api"
import { AuthWrapper } from "@/components/providers/auth-wrpper"

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
  const [generatedFlashcards, setGeneratedFlashcards] = useState<Record<string, unknown> | null>(null)

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
        const completedDocs = response.data.filter((doc) => doc.status === "completed")
        setDocuments(completedDocs)
      }
    } catch (error) {
      console.error("Error loading documents:", error)
      setError("ไม่สามารถโหลดรายการเอกสารได้")
    } finally {
      setLoading(false)
    }
  }

  const handleGenerate = async () => {
    if (generationType === "document" && !selectedDocument) {
      setError("กรุณาเลือกเอกสาร")
      return
    }

    if (generationType === "topic" && !customTopic.trim()) {
      setError("กรุณาใส่หัวข้อที่ต้องการสร้างแฟลชการ์ด")
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
        response = await apiService.generateFlashcardsFromTopic(customTopic.trim(), flashcardCount, difficulty)
      }

      if (response.success && response.data) {
        setGeneratedFlashcards(response.data as Record<string, unknown>)
        setShowSuccessDialog(true)
      } else {
        throw new Error(response.message || "ไม่สามารถสร้างแฟลชการ์ดได้")
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "เกิดข้อผิดพลาดในการสร้างแฟลชการ์ด")
    } finally {
      setIsGenerating(false)
    }
  }

  const handleStartReview = () => {
    setShowSuccessDialog(false)
    if (generationType === "document") {
      router.push(`/flashcards/${selectedDocument}`)
    } else {
      // For topic-based flashcards, use the document_id from the API response
      if (generatedFlashcards && generatedFlashcards.document_id) {
        router.push(`/flashcards/${generatedFlashcards.document_id}`)
      } else if (generatedFlashcards && generatedFlashcards.flashcards && generatedFlashcards.flashcards.length > 0) {
        // Fallback to document_id from individual flashcard
        const documentId = generatedFlashcards.flashcards[0]?.document_id
        if (documentId) {
          router.push(`/flashcards/${documentId}`)
        } else {
          router.push("/flashcards")
        }
      } else {
        // Fallback to general flashcards page
        router.push("/flashcards")
      }
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
    <AuthWrapper>
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-purple-50">
        {/* Navigation */}
        <nav className="bg-white/80 backdrop-blur-sm border-b sticky top-0 z-50">
          <div className="container mx-auto px-4 py-4 flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link href="/dashboard">
                <Button variant="ghost" size="sm" className="text-gray-600 hover:text-gray-900">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  กลับ
                </Button>
              </Link>
              <div className="flex items-center space-x-2">
                <div className="p-2 bg-gradient-to-r from-purple-600 to-blue-600 rounded-lg">
                  <Sparkles className="h-6 w-6 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-gray-900">สร้างแฟลชการ์ด</h1>
                  <p className="text-sm text-gray-600">AI จะช่วยสร้างแฟลชการ์ดให้คุณ</p>
                </div>
              </div>
            </div>
            <Link href="/flashcards/library">
              <Button variant="outline" className="hidden sm:flex bg-transparent">
                <BookOpen className="h-4 w-4 mr-2" />
                ดูคลังแฟลชการ์ด
              </Button>
            </Link>
          </div>
        </nav>

        <div className="container mx-auto px-4 py-8">
          <div className="max-w-6xl mx-auto">
            {/* Header */}
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-12">
              <div className="inline-flex items-center justify-center p-3 bg-gradient-to-r from-purple-100 to-blue-100 rounded-full mb-6">
                <Stars className="h-8 w-8 text-purple-600" />
              </div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent mb-4">
                สร้างแฟลชการ์ดด้วย AI
              </h1>
              <p className="text-lg text-gray-600 max-w-2xl mx-auto">
                ให้ AI ช่วยสร้างแฟลชการ์ดที่ปรับแต่งเฉพาะสำหรับการเรียนรู้ของคุณ จากเอกสารหรือหัวข้อที่คุณสนใจ
              </p>
            </motion.div>

            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center"
                >
                  <AlertCircle className="h-5 w-5 text-red-600 mr-3" />
                  <span className="text-red-700">{error}</span>
                </motion.div>
              )}
            </AnimatePresence>

            <div className="grid lg:grid-cols-3 gap-8">
              {/* Generation Options */}
              <div className="lg:col-span-2 space-y-6">
                {/* Generation Type Selection */}
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
                  <Card className="border-0 shadow-lg bg-white/50 backdrop-blur-sm">
                    <CardHeader>
                      <CardTitle className="flex items-center text-xl">
                        <Target className="h-6 w-6 mr-3 text-purple-600" />
                        เลือกแหล่งเนื้อหา
                      </CardTitle>
                      <CardDescription className="text-base">
                        เลือกว่าต้องการสร้างแฟลชการ์ดจากเอกสารที่มีอยู่ หรือจากหัวข้อที่กำหนดเอง
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
                          <Card
                            className={`cursor-pointer transition-all duration-300 ${
                              generationType === "document"
                                ? "border-blue-500 bg-gradient-to-br from-blue-50 to-indigo-50 shadow-md"
                                : "border-gray-200 hover:border-blue-300 hover:shadow-md"
                            }`}
                            onClick={() => setGenerationType("document")}
                          >
                            <CardContent className="p-6 text-center">
                              <div
                                className={`mx-auto mb-4 p-3 rounded-full w-fit ${
                                  generationType === "document" ? "bg-blue-100" : "bg-gray-100"
                                }`}
                              >
                                <FileText
                                  className={`h-8 w-8 ${
                                    generationType === "document" ? "text-blue-600" : "text-gray-500"
                                  }`}
                                />
                              </div>
                              <h3 className="font-semibold mb-2 text-lg">จากเอกสาร</h3>
                              <p className="text-sm text-gray-600">สร้างจากเอกสารที่อัปโหลดแล้ว</p>
                              {generationType === "document" && (
                                <Badge className="mt-2 bg-blue-100 text-blue-700">เลือกแล้ว</Badge>
                              )}
                            </CardContent>
                          </Card>
                        </motion.div>

                        <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
                          <Card
                            className={`cursor-pointer transition-all duration-300 ${
                              generationType === "topic"
                                ? "border-purple-500 bg-gradient-to-br from-purple-50 to-pink-50 shadow-md"
                                : "border-gray-200 hover:border-purple-300 hover:shadow-md"
                            }`}
                            onClick={() => setGenerationType("topic")}
                          >
                            <CardContent className="p-6 text-center">
                              <div
                                className={`mx-auto mb-4 p-3 rounded-full w-fit ${
                                  generationType === "topic" ? "bg-purple-100" : "bg-gray-100"
                                }`}
                              >
                                <BookOpen
                                  className={`h-8 w-8 ${
                                    generationType === "topic" ? "text-purple-600" : "text-gray-500"
                                  }`}
                                />
                              </div>
                              <h3 className="font-semibold mb-2 text-lg">จากหัวข้อ</h3>
                              <p className="text-sm text-gray-600">ใส่หัวข้อที่ต้องการเรียนรู้</p>
                              {generationType === "topic" && (
                                <Badge className="mt-2 bg-purple-100 text-purple-700">เลือกแล้ว</Badge>
                              )}
                            </CardContent>
                          </Card>
                        </motion.div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>

                {/* Document Selection */}
                <AnimatePresence mode="wait">
                  {generationType === "document" && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={{ duration: 0.3 }}
                    >
                      <Card className="border-0 shadow-lg bg-white/50 backdrop-blur-sm">
                        <CardHeader>
                          <CardTitle className="flex items-center text-xl">
                            <FileText className="h-6 w-6 mr-3 text-blue-600" />
                            เลือกเอกสาร
                          </CardTitle>
                          <CardDescription className="text-base">
                            เลือกเอกสารที่ต้องการสร้างแฟลชการ์ด (เฉพาะเอกสารที่ประมวลผลเสร็จแล้ว)
                          </CardDescription>
                        </CardHeader>
                        <CardContent>
                          {documents.length === 0 ? (
                            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center py-12">
                              <div className="p-4 bg-gray-100 rounded-full w-fit mx-auto mb-6">
                                <Upload className="h-12 w-12 text-gray-400" />
                              </div>
                              <h3 className="text-lg font-semibold text-gray-900 mb-2">ไม่มีเอกสารที่พร้อมใช้งาน</h3>
                              <p className="text-gray-600 mb-6">เริ่มต้นด้วยการอัปโหลดเอกสารแรกของคุณ</p>
                              <Link href="/upload">
                                <Button className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white">
                                  <Upload className="h-4 w-4 mr-2" />
                                  อัปโหลดเอกสาร
                                </Button>
                              </Link>
                            </motion.div>
                          ) : (
                            <div className="space-y-3">
                              {documents.map((doc, index) => {
                                const isCompleted = doc.processing_status === "completed" || doc.status === "completed"
                                const isSelected = selectedDocument === doc.document_id

                                return (
                                  <motion.div
                                    key={doc.document_id}
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: index * 0.1 }}
                                    whileHover={{ scale: 1.01 }}
                                    whileTap={{ scale: 0.99 }}
                                  >
                                    <Card
                                      className={`cursor-pointer transition-all duration-300 ${
                                        isSelected
                                          ? "border-blue-500 bg-gradient-to-r from-blue-50 to-indigo-50 shadow-md"
                                          : "border-gray-200 hover:border-blue-300 hover:shadow-md"
                                      }`}
                                      onClick={() => setSelectedDocument(doc.document_id)}
                                    >
                                      <CardContent className="p-4">
                                        <div className="flex items-center justify-between">
                                          <div className="flex items-center space-x-3">
                                            <div
                                              className={`p-2 rounded-lg ${isSelected ? "bg-blue-100" : "bg-gray-100"}`}
                                            >
                                              <FileText
                                                className={`h-5 w-5 ${isSelected ? "text-blue-600" : "text-gray-500"}`}
                                              />
                                            </div>
                                            <div>
                                              <p className="font-medium line-clamp-1">{doc.filename}</p>
                                              <p className="text-sm text-gray-500">
                                                {new Date(doc.created_at).toLocaleDateString("th-TH")}
                                              </p>
                                            </div>
                                          </div>
                                          <div className="flex items-center space-x-2">
                                            {isCompleted ? (
                                              <Badge className="bg-green-100 text-green-700">
                                                <CheckCircle2 className="h-3 w-3 mr-1" />
                                                พร้อมใช้งาน
                                              </Badge>
                                            ) : (
                                              <Badge className="bg-yellow-100 text-yellow-700">
                                                <Clock className="h-3 w-3 mr-1" />
                                                กำลังประมวลผล
                                              </Badge>
                                            )}
                                            {isSelected && <Badge className="bg-blue-100 text-blue-700">เลือกแล้ว</Badge>}
                                          </div>
                                        </div>
                                      </CardContent>
                                    </Card>
                                  </motion.div>
                                )
                              })}
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Topic Input */}
                <AnimatePresence mode="wait">
                  {generationType === "topic" && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={{ duration: 0.3 }}
                    >
                      <Card className="border-0 shadow-lg bg-white/50 backdrop-blur-sm">
                        <CardHeader>
                          <CardTitle className="flex items-center text-xl">
                            <BookOpen className="h-6 w-6 mr-3 text-purple-600" />
                            ใส่หัวข้อที่ต้องการเรียนรู้
                          </CardTitle>
                          <CardDescription className="text-base">
                            ระบุหัวข้อหรือเนื้อหาที่ต้องการสร้างแฟลชการ์ด เช่น &quot;ประวัติศาสตร์ไทย&quot;, &quot;คณิตศาสตร์ชั้นม.6&quot;
                          </CardDescription>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-6">
                            <div>
                              <Label htmlFor="topic" className="text-base font-medium">
                                หัวข้อ
                              </Label>
                              <motion.div whileFocus={{ scale: 1.02 }} className="mt-2">
                                <Input
                                  id="topic"
                                  value={customTopic}
                                  onChange={(e) => setCustomTopic(e.target.value)}
                                  placeholder="เช่น ประวัติศาสตร์ไทย สมัยอยุธยา, ฟิสิกส์ การเคลื่อนที่, ชีววิทยา เซลล์"
                                  className="text-lg p-4 border-2 focus:border-purple-500 focus:ring-purple-200"
                                />
                              </motion.div>
                            </div>

                            <motion.div
                              initial={{ opacity: 0, y: 10 }}
                              animate={{ opacity: 1, y: 0 }}
                              className="p-4 bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-xl"
                            >
                              <div className="flex items-start space-x-3">
                                <div className="p-1 bg-green-100 rounded-full">
                                  <Sparkles className="h-4 w-4 text-green-600" />
                                </div>
                                <div>
                                  <p className="font-medium text-green-800 mb-1">เคล็ดลับสำหรับหัวข้อที่ดี</p>
                                  <ul className="text-sm text-green-700 space-y-1">
                                    <li>• ระบุหัวข้อให้ละเอียดและชัดเจน</li>
                                    <li>• เพิ่มบริบทหรือระดับการศึกษา</li>
                                    <li>• ใช้ภาษาไทยหรือภาษาอังกฤษได้</li>
                                  </ul>
                                </div>
                              </div>
                            </motion.div>

                            {/* Topic Suggestions */}
                            <div>
                              <p className="text-sm font-medium text-gray-700 mb-3">ตัวอย่างหัวข้อยอดนิยม</p>
                              <div className="flex flex-wrap gap-2">
                                {[
                                  "ประวัติศาสตร์ไทย สมัยอยุธยา",
                                  "คณิตศาสตร์ แคลคูลัส",
                                  "ฟิสิกส์ กลศาสตร์",
                                  "ชีววิทยา เซลล์และระบบ",
                                  "เคมี ตารางธาตุ",
                                  "ภาษาอังกฤษ Grammar",
                                ].map((suggestion) => (
                                  <motion.button
                                    key={suggestion}
                                    whileHover={{ scale: 1.05 }}
                                    whileTap={{ scale: 0.95 }}
                                    onClick={() => setCustomTopic(suggestion)}
                                    className="px-3 py-1 text-xs bg-white border border-gray-200 rounded-full hover:border-purple-300 hover:bg-purple-50 transition-colors"
                                  >
                                    {suggestion}
                                  </motion.button>
                                ))}
                              </div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* Settings */}
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 }}
                className="space-y-6"
              >
                {/* Settings Card */}
                <Card className="border-0 shadow-xl bg-white/70 backdrop-blur-md sticky top-24 overflow-hidden">
                  <div className="absolute inset-0 bg-gradient-to-br from-purple-50/50 to-blue-50/50"></div>
                  <CardHeader className="relative">
                    <CardTitle className="flex items-center text-xl">
                      <div className="p-2 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg mr-3">
                        <Settings className="h-5 w-5 text-white" />
                      </div>
                      <div>
                        <div className="bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
                          ตั้งค่าแฟลชการ์ด
                        </div>
                        <div className="text-sm text-gray-500 font-normal mt-1">
                          ปรับแต่งแฟลชการ์ดให้เหมาะกับการเรียนรู้ของคุณ
                        </div>
                      </div>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-8 relative">
                    {/* Card Count with Enhanced Slider */}
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <Label
                          htmlFor="count"
                          className="text-base font-semibold flex items-center gap-2 text-gray-700"
                        >
                          <div className="p-1.5 bg-purple-100 rounded-lg">
                            <Hash className="h-4 w-4 text-purple-600" />
                          </div>
                          จำนวนการ์ด
                        </Label>
                        <div className="flex items-center space-x-3">
                          <div className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent min-w-[4rem] text-center">
                            {flashcardCount}
                          </div>
                          <div className="text-sm text-gray-500 bg-gray-100 px-2 py-1 rounded-full">การ์ด</div>
                        </div>
                      </div>
                      <div className="px-3 py-2 bg-gradient-to-r from-purple-50 to-blue-50 rounded-xl border border-purple-100">
                        <Slider
                          value={[flashcardCount]}
                          onValueChange={(value) => setFlashcardCount(value[0])}
                          max={50}
                          min={1}
                          step={1}
                          className="w-full [&_[role=slider]]:bg-gradient-to-r [&_[role=slider]]:from-purple-500 [&_[role=slider]]:to-blue-500 [&_[role=slider]]:border-0 [&_[role=slider]]:shadow-lg [&_[role=slider]]:scale-110"
                        />
                        <div className="flex justify-between text-xs text-gray-500 mt-3 px-1">
                          <span className="bg-white px-2 py-1 rounded-full shadow-sm">1</span>
                          <span className="bg-white px-2 py-1 rounded-full shadow-sm">25</span>
                          <span className="bg-white px-2 py-1 rounded-full shadow-sm">50</span>
                        </div>
                      </div>
                    </div>

                    {/* Enhanced Difficulty with Toggle Group */}
                    <div className="space-y-4">
                      <Label className="text-base font-semibold flex items-center gap-2 text-gray-700">
                        <div className="p-1.5 bg-purple-100 rounded-lg">
                          <Target className="h-4 w-4 text-purple-600" />
                        </div>
                        ระดับความยาก
                      </Label>
                      <div className="p-3 bg-gradient-to-r from-purple-50 to-blue-50 rounded-xl border border-purple-100">
                        <ToggleGroup
                          type="single"
                          value={difficulty}
                          onValueChange={(value) => value && setDifficulty(value)}
                          className="grid grid-cols-3 gap-3 w-full"
                        >
                          <ToggleGroupItem
                            value="easy"
                            className="flex-1 py-4 px-3 data-[state=on]:bg-gradient-to-r data-[state=on]:from-green-500 data-[state=on]:to-emerald-500 data-[state=on]:text-white data-[state=on]:border-green-500 data-[state=on]:shadow-lg data-[state=on]:scale-105 border-2 border-gray-200 hover:border-green-300 bg-white hover:bg-green-50 transition-all duration-200 rounded-xl"
                          >
                            <div className="text-center">
                              <div className="font-semibold text-sm">ง่าย</div>
                              <div className="text-xs opacity-75 mt-1">Easy</div>
                            </div>
                          </ToggleGroupItem>
                          <ToggleGroupItem
                            value="medium"
                            className="flex-1 py-4 px-3 data-[state=on]:bg-gradient-to-r data-[state=on]:from-yellow-500 data-[state=on]:to-orange-500 data-[state=on]:text-white data-[state=on]:border-yellow-500 data-[state=on]:shadow-lg data-[state=on]:scale-105 border-2 border-gray-200 hover:border-yellow-300 bg-white hover:bg-yellow-50 transition-all duration-200 rounded-xl"
                          >
                            <div className="text-center">
                              <div className="font-semibold text-sm">ปานกลาง</div>
                              <div className="text-xs opacity-75 mt-1">Medium</div>
                            </div>
                          </ToggleGroupItem>
                          <ToggleGroupItem
                            value="hard"
                            className="flex-1 py-4 px-3 data-[state=on]:bg-gradient-to-r data-[state=on]:from-red-500 data-[state=on]:to-pink-500 data-[state=on]:text-white data-[state=on]:border-red-500 data-[state=on]:shadow-lg data-[state=on]:scale-105 border-2 border-gray-200 hover:border-red-300 bg-white hover:bg-red-50 transition-all duration-200 rounded-xl"
                          >
                            <div className="text-center">
                              <div className="font-semibold text-sm">ยาก</div>
                              <div className="text-xs opacity-75 mt-1">Hard</div>
                            </div>
                          </ToggleGroupItem>
                        </ToggleGroup>
                      </div>
                    </div>

                    {/* Enhanced Bloom's Taxonomy with Select */}
                    <div className="space-y-4">
                      <Label className="text-base font-semibold flex items-center gap-2 text-gray-700">
                        <div className="p-1.5 bg-purple-100 rounded-lg">
                          <Brain className="h-4 w-4 text-purple-600" />
                        </div>
                        ระดับความคิด (Bloom&apos;s Taxonomy)
                      </Label>
                      <div className="relative">
                        <Select value={bloomLevel} onValueChange={setBloomLevel}>
                          <SelectTrigger className="w-full h-14 text-base bg-white border-2 border-gray-200 hover:border-purple-300 focus:border-purple-500 rounded-xl shadow-sm">
                            <SelectValue placeholder="เลือกระดับความคิด" />
                          </SelectTrigger>
                          <SelectContent className="rounded-xl border-2 shadow-xl">
                            <SelectItem value="all" className="py-3 px-4 text-base rounded-lg">
                              <div className="flex items-center gap-3">
                                <span className="text-lg">🌟</span>
                                <div>
                                  <div className="font-medium">ทุกระดับ</div>
                                  <div className="text-xs text-gray-500">All Levels</div>
                                </div>
                              </div>
                            </SelectItem>
                            <SelectItem value="remember" className="py-3 px-4 text-base rounded-lg">
                              <div className="flex items-center gap-3">
                                <span className="text-lg">🧠</span>
                                <div>
                                  <div className="font-medium">จำ</div>
                                  <div className="text-xs text-gray-500">Remember</div>
                                </div>
                              </div>
                            </SelectItem>
                            <SelectItem value="understand" className="py-3 px-4 text-base rounded-lg">
                              <div className="flex items-center gap-3">
                                <span className="text-lg">💡</span>
                                <div>
                                  <div className="font-medium">เข้าใจ</div>
                                  <div className="text-xs text-gray-500">Understand</div>
                                </div>
                              </div>
                            </SelectItem>
                            <SelectItem value="apply" className="py-3 px-4 text-base rounded-lg">
                              <div className="flex items-center gap-3">
                                <span className="text-lg">🔧</span>
                                <div>
                                  <div className="font-medium">ประยุกต์</div>
                                  <div className="text-xs text-gray-500">Apply</div>
                                </div>
                              </div>
                            </SelectItem>
                            <SelectItem value="analyze" className="py-3 px-4 text-base rounded-lg">
                              <div className="flex items-center gap-3">
                                <span className="text-lg">🔍</span>
                                <div>
                                  <div className="font-medium">วิเคราะห์</div>
                                  <div className="text-xs text-gray-500">Analyze</div>
                                </div>
                              </div>
                            </SelectItem>
                            <SelectItem value="evaluate" className="py-3 px-4 text-base rounded-lg">
                              <div className="flex items-center gap-3">
                                <span className="text-lg">⚖️</span>
                                <div>
                                  <div className="font-medium">ประเมิน</div>
                                  <div className="text-xs text-gray-500">Evaluate</div>
                                </div>
                              </div>
                            </SelectItem>
                            <SelectItem value="create" className="py-3 px-4 text-base rounded-lg">
                              <div className="flex items-center gap-3">
                                <span className="text-lg">✨</span>
                                <div>
                                  <div className="font-medium">สร้าง</div>
                                  <div className="text-xs text-gray-500">Create</div>
                                </div>
                              </div>
                            </SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    {/* Enhanced Generation Summary */}
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="relative overflow-hidden"
                    >
                      <div className="absolute inset-0 bg-gradient-to-br from-purple-500/10 via-blue-500/10 to-indigo-500/10 rounded-2xl"></div>
                      <div className="absolute inset-0 bg-white/40 rounded-2xl backdrop-blur-sm"></div>
                      <div className="relative p-6 border-2 border-purple-200/50 rounded-2xl">
                        <div className="flex items-center space-x-3 mb-6">
                          <div className="p-2.5 bg-gradient-to-r from-purple-500 to-blue-500 rounded-xl shadow-lg">
                            <Sparkles className="h-5 w-5 text-white" />
                          </div>
                          <div>
                            <span className="text-xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
                              สรุปการสร้าง
                            </span>
                            <div className="text-sm text-gray-500">Generation Summary</div>
                          </div>
                        </div>
                        <div className="grid grid-cols-1 gap-4 text-sm">
                          <div className="flex justify-between items-center p-3 bg-white/60 rounded-xl border border-purple-100">
                            <span className="text-gray-600 flex items-center gap-2 font-medium">
                              <div className="p-1 bg-purple-100 rounded-lg">
                                <Hash className="h-3 w-3 text-purple-600" />
                              </div>
                              จำนวนการ์ด
                            </span>
                            <div className="flex items-center gap-2">
                              <span className="text-2xl font-bold text-purple-600">{flashcardCount}</span>
                              <span className="text-xs text-gray-500 bg-purple-50 px-2 py-1 rounded-full">การ์ด</span>
                            </div>
                          </div>

                          <div className="flex justify-between items-center p-3 bg-white/60 rounded-xl border border-purple-100">
                            <span className="text-gray-600 flex items-center gap-2 font-medium">
                              <div className="p-1 bg-purple-100 rounded-lg">
                                <Target className="h-3 w-3 text-purple-600" />
                              </div>
                              ระดับความยาก
                            </span>
                            <Badge
                              className={`px-3 py-1 text-sm font-medium ${
                                difficulty === "easy"
                                  ? "bg-gradient-to-r from-green-100 to-emerald-100 text-green-700 border-green-200"
                                  : difficulty === "medium"
                                    ? "bg-gradient-to-r from-yellow-100 to-orange-100 text-yellow-700 border-yellow-200"
                                    : "bg-gradient-to-r from-red-100 to-pink-100 text-red-700 border-red-200"
                              } border`}
                            >
                              {difficulty === "easy" ? "ง่าย" : difficulty === "medium" ? "ปานกลาง" : "ยาก"}
                            </Badge>
                          </div>

                          <div className="flex justify-between items-center p-3 bg-white/60 rounded-xl border border-purple-100">
                            <span className="text-gray-600 flex items-center gap-2 font-medium">
                              <div className="p-1 bg-purple-100 rounded-lg">
                                <FileText className="h-3 w-3 text-purple-600" />
                              </div>
                              แหล่งที่มา
                            </span>
                            <Badge className="bg-gradient-to-r from-blue-100 to-indigo-100 text-blue-700 border border-blue-200 px-3 py-1 text-sm font-medium">
                              {generationType === "document" ? "เอกสาร" : "หัวข้อ"}
                            </Badge>
                          </div>

                          <div className="flex justify-between items-center p-3 bg-white/60 rounded-xl border border-purple-100">
                            <span className="text-gray-600 flex items-center gap-2 font-medium">
                              <div className="p-1 bg-purple-100 rounded-lg">
                                <Brain className="h-3 w-3 text-purple-600" />
                              </div>
                              ระดับความคิด
                            </span>
                            <span className="font-semibold text-sm bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
                              {bloomLevel === "all"
                                ? "ทุกระดับ"
                                : bloomLevel === "remember"
                                  ? "จำ"
                                  : bloomLevel === "understand"
                                    ? "เข้าใจ"
                                    : bloomLevel === "apply"
                                      ? "ประยุกต์"
                                      : bloomLevel === "analyze"
                                        ? "วิเคราะห์"
                                        : bloomLevel === "evaluate"
                                          ? "ประเมิน"
                                          : "สร้าง"}
                            </span>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  </CardContent>
                </Card>

                {/* Generate Button */}
                <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} className="relative">
                  <div className="absolute inset-0 bg-gradient-to-r from-purple-600 to-blue-600 rounded-xl blur-xl opacity-25 animate-pulse"></div>
                  <Button
                    onClick={handleGenerate}
                    disabled={
                      isGenerating ||
                      (generationType === "document" && !selectedDocument) ||
                      (generationType === "topic" && !customTopic.trim())
                    }
                    className="relative w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white py-6 text-lg font-semibold shadow-2xl border-0 overflow-hidden"
                    size="lg"
                  >
                    <div className="absolute inset-0 bg-gradient-to-r from-white/10 to-transparent"></div>
                    {isGenerating ? (
                      <div className="relative flex items-center justify-center">
                        <Loader2 className="h-6 w-6 mr-3 animate-spin" />
                        <div className="text-center">
                          <div className="font-bold">กำลังสร้างแฟลชการ์ด</div>
                          <div className="text-sm opacity-90">AI กำลังประมวลผล...</div>
                        </div>
                      </div>
                    ) : (
                      <div className="relative flex items-center justify-center">
                        <Wand2 className="h-6 w-6 mr-3" />
                        <div className="text-center">
                          <div className="font-bold">สร้างแฟลชการ์ด</div>
                          <div className="text-sm opacity-90">Generate Flashcards</div>
                        </div>
                      </div>
                    )}
                  </Button>
                </motion.div>
              </motion.div>
            </div>
          </div>
        </div>

        {/* Success Dialog */}
        <Dialog open={showSuccessDialog} onOpenChange={setShowSuccessDialog}>
          <DialogContent className="sm:max-w-md">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="text-center py-6"
            >
              <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-gradient-to-r from-green-100 to-emerald-100 mb-6">
                <CheckCircle2 className="h-8 w-8 text-green-600" />
              </div>
              <DialogHeader>
                <DialogTitle className="text-2xl font-bold text-gray-900 mb-2">สร้างแฟลชการ์ดสำเร็จ! 🎉</DialogTitle>
                <DialogDescription className="text-base text-gray-600">
                  สร้างแฟลชการ์ดจำนวน{" "}
                  <span className="font-semibold text-purple-600">
                    {generatedFlashcards?.flashcards?.length || generatedFlashcards?.flashcards_generated || 0} ใบ
                  </span>{" "}
                  เรียบร้อยแล้ว พร้อมเริ่มทบทวนได้เลย
                </DialogDescription>
              </DialogHeader>

              <div className="flex flex-col sm:flex-row gap-3 mt-8">
                <Button variant="outline" onClick={() => setShowSuccessDialog(false)} className="flex-1">
                  ดูในคลัง
                </Button>
                <Button
                  onClick={handleStartReview}
                  className="flex-1 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white"
                >
                  <Play className="h-4 w-4 mr-2" />
                  เริ่มทบทวนเลย
                </Button>
              </div>
            </motion.div>
          </DialogContent>
        </Dialog>
      </div>
    </AuthWrapper>
  )
}
