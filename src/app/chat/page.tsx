"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Brain, ArrowLeft, Send, User, Bot, FileText, Loader2, ChevronDown } from "lucide-react"
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
  const [documents, setDocuments] = useState<Array<{document_id: string, filename: string}>>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)
  
  
  
  

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    // Load documents when component mounts
    const loadDocuments = async () => {
      try {
        const response = await apiService.getDocuments()
        if (response.success && response.data) {
          setDocuments(response.data)
        }
      } catch (error) {
        console.error('Error loading documents:', error)
      }
    }
    loadDocuments()
  }, [])

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: "user",
      content: inputMessage,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const currentQuestion = inputMessage;
    setInputMessage("");
    setIsLoading(true);

    try {
      const response = await apiService.askQuestion(
        currentQuestion,
        sessionId
      );

      if (response.success && response.data) {
        const aiMessage: Message = {
          id: (Date.now() + 1).toString(),
          type: "ai",
          content: response.data.answer,
          timestamp: new Date(),
          sources: response.data.sources,
          confidence: response.data.confidence
        };

        setMessages((prev) => [...prev, aiMessage]);
        
        // Update session ID if provided
        if (response.data.session_id) {
          setSessionId(response.data.session_id);
        }
      } else {
        throw new Error(response.message || 'Failed to get response');
      }
    } catch (error) {
      console.error("Error sending message:", error);
      
      // Fallback response for demo
      const fallbackResponse: Message = {
        id: (Date.now() + 1).toString(),
        type: "ai",
        content: `ขอบคุณสำหรับคำถาม "${currentQuestion}" ครับ\n\nขออภัย ขณะนี้ระบบยังไม่สามารถเชื่อมต่อกับ backend ได้ นี่เป็นการตอบสนองแบบตัวอย่าง:\n\n• ระบบ RAG จะค้นหาข้อมูลที่เกี่ยวข้องในเอกสาร\n• วิเคราะห์บริบทและสร้างคำตอบที่แม่นยำ\n• แสดงแหล่งข้อมูลอ้างอิงพร้อมระดับความเชื่อมั่น\n\nกรุณาตรวจสอบการเชื่อมต่อ backend และลองใหม่อีกครั้ง`,
        timestamp: new Date(),
        sources: [
          {
            chunk_id: "demo-chunk-1",
            text: "ข้อมูลตัวอย่างจากเอกสาร...",
            similarity: 0.85
          }
        ],
        confidence: 0.7
      };
      setMessages((prev) => [...prev, fallbackResponse]);
    } finally {
      setIsLoading(false);
    }
  };

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
      <div className="min-h-screen bg-gray-50 flex flex-col">
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
              <span className="text-2xl font-bold text-gray-900">RAISE</span>
            </div>
          </div>
        </div>
      </nav>

      <div className="flex-1 container mx-auto px-4 py-8 flex flex-col">
        <div className="max-w-4xl mx-auto w-full flex flex-col h-full">
          {/* Header */}
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">ระบบถาม-ตอบ AI</h1>
            <p className="text-gray-600">สอบถามคำถามเกี่ยวกับเนื้อหาในเอกสารของคุณ AI จะตอบโดยอ้างอิงจากเอกสารที่อัปโหลดไว้</p>
          </div>

          {/* Document Info */}
          <Card className="mb-4 border-0 shadow-sm">
            <CardContent className="p-4">
              <div className="flex items-center space-x-3">
                <FileText className="h-5 w-5 text-blue-500" />
                <div className="flex-1">
                  <h3 className="text-sm font-medium text-gray-900">ระบบค้นหาอัตโนมัติ</h3>
                  <p className="text-sm text-gray-600 mt-1">
                    AI จะค้นหาข้อมูลจากเอกสารทั้งหมดของคุณ ({documents.length} เอกสาร) เพื่อตอบคำถาม
                  </p>
                </div>
              </div>
              {documents.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {documents.slice(0, 3).map((doc) => (
                    <span key={doc.document_id} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                      {doc.filename}
                    </span>
                  ))}
                  {documents.length > 3 && (
                    <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                      +{documents.length - 3} เอกสารอื่น ๆ
                    </span>
                  )}
                </div>
              )}
              {documents.length === 0 && (
                <div className="mt-2 text-sm text-amber-600 flex items-center space-x-1">
                  <span>⚠️</span>
                  <span>ไม่พบเอกสารใด ๆ กรุณาอัปโหลดเอกสารก่อนใช้งาน</span>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Chat Messages */}
          <Card className="flex-1 border-0 shadow-sm mb-4 flex flex-col">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Bot className="h-5 w-5 text-blue-600" />
                <span>การสนทนา</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col">
              <div className="flex-1 overflow-y-auto space-y-4 mb-4 max-h-96">
                {messages.map((message) => (
                  <div key={message.id} className={`flex ${message.type === "user" ? "justify-end" : "justify-start"}`}>
                    <div
                      className={`flex space-x-3 max-w-3xl ${message.type === "user" ? "flex-row-reverse space-x-reverse" : ""}`}
                    >
                      <div
                        className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                          message.type === "user" ? "bg-blue-600 text-white" : "bg-gray-200 text-gray-600"
                        }`}
                      >
                        {message.type === "user" ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                      </div>
                      <div
                        className={`rounded-lg p-4 ${
                          message.type === "user" ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-900"
                        }`}
                      >
                        <p className="whitespace-pre-wrap">{message.content}</p>
                        {message.sources && message.sources.length > 0 && (
                          <div className="mt-3 pt-3 border-t border-gray-300">
                            <p className="text-sm font-medium mb-2">แหล่งข้อมูล:</p>
                            <div className="space-y-2">
                              {message.sources.map((source, index) => (
                                <div key={index} className="text-sm bg-white/20 rounded p-2">
                                  <div className="flex items-center space-x-2 mb-1">
                                    <FileText className="h-3 w-3" />
                                    <span className="font-medium">
                                      {typeof source === 'object' && source.document_title 
                                        ? source.document_title 
                                        : `ส่วนที่ ${index + 1}`}
                                    </span>
                                    {typeof source === 'object' && source.similarity && (
                                      <span className="text-xs opacity-75">
                                        ({Math.round(source.similarity * 100)}% ความเกี่ยวข้อง)
                                      </span>
                                    )}
                                  </div>
                                  {typeof source === 'object' && source.text && (
                                    <p className="text-xs opacity-90 line-clamp-2">
                                      {source.text.length > 100 
                                        ? source.text.substring(0, 100) + "..." 
                                        : source.text}
                                    </p>
                                  )}
                                  {typeof source === 'string' && (
                                    <span className="text-xs">{source}</span>
                                  )}
                                </div>
                              ))}
                            </div>
                            {message.confidence && (
                              <div className="mt-2 text-xs opacity-75">
                                ความมั่นใจ: {Math.round(message.confidence * 100)}%
                              </div>
                            )}
                          </div>
                        )}
                        <p className="text-xs mt-2 opacity-75">{formatTime(message.timestamp)}</p>
                      </div>
                    </div>
                  </div>
                ))}

                {isLoading && (
                  <div className="flex justify-start">
                    <div className="flex space-x-3 max-w-3xl">
                      <div className="w-8 h-8 rounded-full bg-gray-200 text-gray-600 flex items-center justify-center flex-shrink-0">
                        <Bot className="h-4 w-4" />
                      </div>
                      <div className="bg-gray-100 text-gray-900 rounded-lg p-4">
                        <div className="flex items-center space-x-2">
                          <Loader2 className="h-4 w-4 animate-spin" />
                          <span>กำลังค้นหาข้อมูล...</span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* Input Area */}
              <div className="border-t pt-4">
                <div className="flex space-x-2">
                  <Input
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="พิมพ์คำถามของคุณที่นี่..."
                    disabled={isLoading}
                    className="flex-1"
                  />
                  <Button
                    onClick={handleSendMessage}
                    disabled={!inputMessage.trim() || isLoading}
                    className="bg-blue-600 hover:bg-blue-700"
                  >
                    {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                  </Button>
                </div>
                <div className="flex items-center justify-between text-xs text-gray-500 mt-2">
                  <span>กด Enter เพื่อส่งข้อความ หรือ Shift + Enter เพื่อขึ้นบรรทัดใหม่</span>
                  <div className="flex items-center space-x-1">
                    <FileText className="h-3 w-3" />
                    <span className="truncate max-w-32">
                      ค้นหาจาก {documents.length} เอกสาร
                    </span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Quick Questions */}
          <Card className="border-0 shadow-sm">
            <CardHeader>
              <CardTitle className="text-lg">คำถามที่ถามบ่อย</CardTitle>
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
                    className="text-left justify-start h-auto p-3 bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
                    onClick={() => setInputMessage(question)}
                  >
                    {question}
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
