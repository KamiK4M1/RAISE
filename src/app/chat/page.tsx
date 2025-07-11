"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Brain, ArrowLeft, Send, User, Bot, FileText, Loader2, Sparkles, MessageCircle, Zap } from "lucide-react"
import Link from "next/link"
import { apiService } from "@/lib/api"
import { AuthWrapper } from "@/components/providers/auth-wrpper"

interface Message {
  id: string
  type: "user" | "ai"
  content: string
  timestamp: Date
  sources?: Array<{
    chunk_id: string
    text: string
    similarity: number
  }>
  confidence?: number
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      type: "ai",
      content: "สวัสดีครับ! ผมเป็น AI ที่จะช่วยตอบคำถามเกี่ยวกับเนื้อหาในเอกสารที่คุณอัปโหลดไว้ มีอะไรให้ช่วยไหมครับ?",
      timestamp: new Date(),
    },
  ])
  const [inputMessage, setInputMessage] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [sessionId, setSessionId] = useState<string | undefined>(undefined)
  const [selectedDocument, setSelectedDocument] = useState<string | undefined>(undefined)
  const [documents, setDocuments] = useState<Array<{ document_id: string; filename: string }>>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    const loadDocuments = async () => {
      try {
        const response = await apiService.getDocuments()
        if (response.success && response.data) {
          setDocuments(response.data)
        }
      } catch (error) {
        console.error("Error loading documents:", error)
      }
    }
    loadDocuments()
  }, [])

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: "user",
      content: inputMessage,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    const currentQuestion = inputMessage
    setInputMessage("")
    setIsLoading(true)

    try {
      const response = await apiService.askQuestion(currentQuestion, sessionId)

      if (response.success && response.data) {
        const aiMessage: Message = {
          id: (Date.now() + 1).toString(),
          type: "ai",
          content: response.data.answer,
          timestamp: new Date(),
          sources: response.data.sources,
          confidence: response.data.confidence,
        }

        setMessages((prev) => [...prev, aiMessage])

        if (response.data.session_id) {
          setSessionId(response.data.session_id)
        }
      } else {
        throw new Error(response.message || "Failed to get response")
      }
    } catch (error) {
      console.error("Error sending message:", error)

      const fallbackResponse: Message = {
        id: (Date.now() + 1).toString(),
        type: "ai",
        content: `ขอบคุณสำหรับคำถาม "${currentQuestion}" ครับ\n\nขออภัย ขณะนี้ระบบยังไม่สามารถเชื่อมต่อกับ backend ได้ นี่เป็นการตอบสนองแบบตัวอย่าง:\n\n• ระบบ RAG จะค้นหาข้อมูลที่เกี่ยวข้องในเอกสาร\n• วิเคราะห์บริบทและสร้างคำตอบที่แม่นยำ\n• แสดงแหล่งข้อมูลอ้างอิงพร้อมระดับความเชื่อมั่น\n\nกรุณาตรวจสอบการเชื่อมต่อ backend และลองใหม่อีกครั้ง`,
        timestamp: new Date(),
        sources: [
          {
            chunk_id: "demo-chunk-1",
            text: "ข้อมูลตัวอย่างจากเอกสาร...",
            similarity: 0.85,
          },
        ],
        confidence: 0.7,
      }
      setMessages((prev) => [...prev, fallbackResponse])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString("th-TH", {
      hour: "2-digit",
      minute: "2-digit",
    })
  }

  return (
    <AuthWrapper>
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
        {/* Modern Navigation */}
        <nav className="bg-white/80 backdrop-blur-lg border-b border-white/20 sticky top-0 z-50 shadow-lg">
          <div className="container mx-auto px-4 py-4 flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link href="/dashboard">
                <Button variant="ghost" size="sm" className="text-gray-600 hover:text-gray-900 hover:bg-white/50">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  กลับ
                </Button>
              </Link>
              <div className="flex items-center space-x-3">
                <div className="relative">
                  <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl blur opacity-75"></div>
                  <Brain className="relative h-8 w-8 text-white bg-gradient-to-r from-blue-600 to-purple-600 p-1.5 rounded-xl" />
                </div>
                <span className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  RAISE
                </span>
              </div>
            </div>
          </div>
        </nav>

        <div className="flex-1 container mx-auto px-4 py-8 flex flex-col">
          <div className="max-w-4xl mx-auto w-full flex flex-col h-full">
            {/* Modern Header */}
            <div className="mb-8 text-center">
              <div className="inline-flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-blue-100 to-purple-100 rounded-full mb-4">
                <MessageCircle className="h-4 w-4 text-blue-600" />
                <span className="text-sm font-medium text-blue-800">AI Assistant</span>
              </div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-gray-900 via-blue-800 to-purple-800 bg-clip-text text-transparent mb-3">
                ระบบถาม-ตอบ AI
              </h1>
              <p className="text-lg text-gray-600 max-w-2xl mx-auto">
                สอบถามคำถามเกี่ยวกับเนื้อหาในเอกสารของคุณ AI จะตอบโดยอ้างอิงจากเอกสารที่อัปโหลดไว้
              </p>
            </div>

            {/* Document Info */}
            <Card className="mb-6 border-0 shadow-lg bg-white/70 backdrop-blur-sm">
              <CardContent className="p-6">
                <div className="flex items-center space-x-4">
                  <div className="p-3 bg-gradient-to-r from-blue-500 to-purple-500 rounded-xl">
                    <FileText className="h-6 w-6 text-white" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 mb-1">ระบบค้นหาอัตโนมัติ</h3>
                    <p className="text-gray-600">
                      AI จะค้นหาข้อมูลจากเอกสารทั้งหมดของคุณ ({documents.length} เอกสาร) เพื่อตอบคำถาม
                    </p>
                  </div>
                </div>
                {documents.length > 0 && (
                  <div className="mt-4 flex flex-wrap gap-2">
                    {documents.slice(0, 3).map((doc) => (
                      <span
                        key={doc.document_id}
                        className="px-3 py-1 bg-gradient-to-r from-blue-100 to-purple-100 text-blue-800 text-sm rounded-full font-medium"
                      >
                        {doc.filename}
                      </span>
                    ))}
                    {documents.length > 3 && (
                      <span className="px-3 py-1 bg-gray-100 text-gray-600 text-sm rounded-full">
                        +{documents.length - 3} เอกสารอื่น ๆ
                      </span>
                    )}
                  </div>
                )}
                {documents.length === 0 && (
                  <div className="mt-4 p-4 bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 rounded-lg">
                    <div className="flex items-center space-x-2 text-amber-700">
                      <Sparkles className="h-4 w-4" />
                      <span className="font-medium">ไม่พบเอกสารใด ๆ กรุณาอัปโหลดเอกสารก่อนใช้งาน</span>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Chat Messages */}
            <Card className="flex-1 border-0 shadow-xl mb-6 flex flex-col bg-white/70 backdrop-blur-sm">
              <CardHeader className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-t-lg">
                <CardTitle className="flex items-center space-x-2">
                  <Bot className="h-5 w-5 text-blue-600" />
                  <span>การสนทนา</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="flex-1 flex flex-col p-6">
                <div className="flex-1 overflow-y-auto space-y-6 mb-6 max-h-96">
                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex ${message.type === "user" ? "justify-end" : "justify-start"}`}
                    >
                      <div
                        className={`flex space-x-3 max-w-3xl ${message.type === "user" ? "flex-row-reverse space-x-reverse" : ""}`}
                      >
                        <div
                          className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 shadow-lg ${
                            message.type === "user"
                              ? "bg-gradient-to-r from-blue-600 to-purple-600 text-white"
                              : "bg-gradient-to-r from-gray-100 to-gray-200 text-gray-600"
                          }`}
                        >
                          {message.type === "user" ? <User className="h-5 w-5" /> : <Bot className="h-5 w-5" />}
                        </div>
                        <div
                          className={`rounded-2xl p-4 shadow-lg ${
                            message.type === "user"
                              ? "bg-gradient-to-r from-blue-600 to-purple-600 text-white"
                              : "bg-white border border-gray-100"
                          }`}
                        >
                          <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
                          {message.sources && message.sources.length > 0 && (
                            <div className="mt-4 pt-4 border-t border-gray-200">
                              <p className="text-sm font-medium mb-3 flex items-center">
                                <FileText className="h-4 w-4 mr-1" />
                                แหล่งข้อมูล:
                              </p>
                              <div className="space-y-2">
                                {message.sources.map((source, index) => (
                                  <div key={index} className="text-sm bg-gray-50 rounded-lg p-3 border">
                                    <div className="flex items-center space-x-2 mb-2">
                                      <FileText className="h-3 w-3" />
                                      <span className="font-medium">
                                        {typeof source === "object" && (source as any).document_title
                                          ? (source as any).document_title
                                          : `ส่วนที่ ${index + 1}`}
                                      </span>
                                      {typeof source === "object" && source.similarity && (
                                        <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full">
                                          {Math.round(source.similarity * 100)}% ความเกี่ยวข้อง
                                        </span>
                                      )}
                                    </div>
                                    {typeof source === "object" && source.text && (
                                      <p className="text-xs text-gray-600 line-clamp-2">
                                        {source.text.length > 100 ? source.text.substring(0, 100) + "..." : source.text}
                                      </p>
                                    )}
                                  </div>
                                ))}
                              </div>
                              {message.confidence && (
                                <div className="mt-3 flex items-center space-x-2">
                                  <Zap className="h-3 w-3 text-green-500" />
                                  <span className="text-xs text-gray-600">
                                    ความมั่นใจ: {Math.round(message.confidence * 100)}%
                                  </span>
                                </div>
                              )}
                            </div>
                          )}
                          <p className="text-xs mt-3 opacity-75">{formatTime(message.timestamp)}</p>
                        </div>
                      </div>
                    </div>
                  ))}

                  {isLoading && (
                    <div className="flex justify-start">
                      <div className="flex space-x-3 max-w-3xl">
                        <div className="w-10 h-10 rounded-full bg-gradient-to-r from-gray-100 to-gray-200 text-gray-600 flex items-center justify-center flex-shrink-0">
                          <Bot className="h-5 w-5" />
                        </div>
                        <div className="bg-white border border-gray-100 rounded-2xl p-4 shadow-lg">
                          <div className="flex items-center space-x-3">
                            <Loader2 className="h-5 w-5 animate-spin text-blue-600" />
                            <span className="text-gray-600">กำลังค้นหาข้อมูล...</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  <div ref={messagesEndRef} />
                </div>

                {/* Input Area */}
                <div className="border-t pt-6">
                  <div className="flex space-x-3">
                    <Input
                      value={inputMessage}
                      onChange={(e) => setInputMessage(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder="พิมพ์คำถามของคุณที่นี่..."
                      disabled={isLoading}
                      className="flex-1 bg-white/50 border-gray-200 focus:border-blue-400 focus:ring-blue-400/20"
                    />
                    <Button
                      onClick={handleSendMessage}
                      disabled={!inputMessage.trim() || isLoading}
                      className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 shadow-lg"
                    >
                      {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                    </Button>
                  </div>
                  <div className="flex items-center justify-between text-xs text-gray-500 mt-3">
                    <span>กด Enter เพื่อส่งข้อความ หรือ Shift + Enter เพื่อขึ้นบรรทัดใหม่</span>
                    <div className="flex items-center space-x-2">
                      <FileText className="h-3 w-3" />
                      <span className="truncate max-w-32">ค้นหาจาก {documents.length} เอกสาร</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Quick Questions */}
            <Card className="border-0 shadow-xl bg-white/70 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-lg flex items-center">
                  <Sparkles className="h-5 w-5 mr-2 text-yellow-600" />
                  คำถามที่ถามบ่อย
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-2 gap-3">
                  {[
                    "สรุปเนื้อหาหลักของเอกสารนี้",
                    "มีแบบฝึกหัดอะไรบ้างในเอกสาร?",
                    "จุดสำคัญที่ควรจำคืออะไร?",
                    "มีตัวอย่างการใช้งานไหม?",
                  ].map((question, index) => (
                    <Button
                      key={index}
                      variant="outline"
                      className="text-left justify-start h-auto p-4 bg-white/50 text-gray-700 border-gray-200 hover:bg-white/80 hover:border-blue-300 transition-all duration-300 hover:scale-105"
                      onClick={() => setInputMessage(question)}
                    >
                      <div className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-gradient-to-r from-blue-400 to-purple-400 rounded-full"></div>
                        <span>{question}</span>
                      </div>
                    </Button>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </AuthWrapper>
  )
}
