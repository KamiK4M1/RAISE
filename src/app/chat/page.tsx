"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Brain, ArrowLeft, Send, User, Bot, FileText, Loader2 } from "lucide-react"
import Link from "next/link"

interface Message {
  id: string
  type: "user" | "ai"
  content: string
  timestamp: Date
  sources?: string[]
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
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: "user",
      content: inputMessage,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInputMessage("")
    setIsLoading(true)

    // TODO: Send to Python backend RAG system
    try {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 2000))

      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        type: "ai",
        content: `ขอบคุณสำหรับคำถาม "${inputMessage}" ครับ\n\nจากการค้นหาในเอกสารที่คุณอัปโหลดไว้ ผมพบข้อมูลที่เกี่ยวข้องดังนี้:\n\n• สมการเชิงเส้นคือสมการที่มีตัวแปรยกกำลังหนึ่ง\n• สามารถเขียนในรูปแบบทั่วไปได้เป็น ax + b = 0\n• วิธีการแก้คือการหาค่า x ที่ทำให้สมการเป็นจริง\n\nหากต้องการข้อมูลเพิ่มเติมหรือมีคำถามอื่น สามารถถามได้เลยครับ`,
        timestamp: new Date(),
        sources: ["คณิตศาสตร์_บทที่5.pdf", "สมการเชิงเส้น_สรุป.docx"],
      }

      setMessages((prev) => [...prev, aiResponse])
    } catch (error) {
      console.error("Error sending message:", error)
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: "ai",
        content: "ขออภัยครับ เกิดข้อผิดพลาดในการประมวลผล กรุณาลองใหม่อีกครั้ง",
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
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
              <span className="text-2xl font-bold text-gray-900">AI Learning</span>
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
                        {message.sources && (
                          <div className="mt-3 pt-3 border-t border-gray-300">
                            <p className="text-sm font-medium mb-2">แหล่งข้อมูล:</p>
                            <div className="space-y-1">
                              {message.sources.map((source, index) => (
                                <div key={index} className="flex items-center space-x-2 text-sm">
                                  <FileText className="h-3 w-3" />
                                  <span>{source}</span>
                                </div>
                              ))}
                            </div>
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
                <p className="text-xs text-gray-500 mt-2">กด Enter เพื่อส่งข้อความ หรือ Shift + Enter เพื่อขึ้นบรรทัดใหม่</p>
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
  )
}
