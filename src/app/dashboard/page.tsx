"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import {
  Brain,
  Upload,
  Zap,
  BookOpen,
  MessageSquare,
  BarChart3,
  FileText,
  Clock,
  Target,
  TrendingUp,
} from "lucide-react"
import Link from "next/link"
import { apiService } from "@/lib/api"
import { UserAnalytics, Document } from "@/types/api"

export default function DashboardPage() {
  const [stats, setStats] = useState({
    documentsUploaded: 0,
    flashcardsStudied: 0,
    quizzesTaken: 0,
    questionsAsked: 0,
    studyStreak: 0,
    totalStudyTime: 0,
  })
  const [recentDocuments, setRecentDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        // Load user analytics
        const analyticsResponse = await apiService.getUserAnalytics(30)
        if (analyticsResponse.success && analyticsResponse.data) {
          const data = analyticsResponse.data
          setStats({
            documentsUploaded: data.learning_progress.total_documents_studied,
            flashcardsStudied: data.flashcard_stats.total_reviews,
            quizzesTaken: data.quiz_stats.total_attempts,
            questionsAsked: data.chat_stats.total_questions,
            studyStreak: data.flashcard_stats.streak_days,
            totalStudyTime: Math.round(data.study_patterns.total_study_time / 60), // Convert to hours
          })
        }

        // Load recent documents
        const documentsResponse = await apiService.getDocuments()
        if (documentsResponse.success && documentsResponse.data) {
          setRecentDocuments(documentsResponse.data.slice(0, 5))
        }
      } catch (error) {
        console.error('Error loading dashboard data:', error)
        // Keep mock data as fallback
        setStats({
          documentsUploaded: 12,
          flashcardsStudied: 156,
          quizzesTaken: 8,
          questionsAsked: 23,
          studyStreak: 7,
          totalStudyTime: 45,
        })
      } finally {
        setLoading(false)
      }
    }

    loadDashboardData()
  }, [])

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white border-b sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Brain className="h-8 w-8 text-blue-600" />
            <span className="text-2xl font-bold text-gray-900">RAISE</span>
          </div>
          <div className="flex items-center space-x-4">
            <span className="text-gray-600">สวัสดี, นักเรียน</span>
            <Button variant="outline" className="bg-white text-gray-700 border-gray-300 hover:bg-gray-50">
              ออกจากระบบ
            </Button>
          </div>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">แดชบอร์ดการเรียนรู้</h1>
          <p className="text-gray-600">ติดตามความก้าวหน้าและเข้าถึงเครื่องมือการเรียนรู้ของคุณ</p>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <Card className="border-0 shadow-sm">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">เอกสาร</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.documentsUploaded}</p>
                </div>
                <FileText className="h-8 w-8 text-blue-600" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-sm">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">แฟลชการ์ด</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.flashcardsStudied}</p>
                </div>
                <Zap className="h-8 w-8 text-purple-600" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-sm">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">แบบทดสอบ</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.quizzesTaken}</p>
                </div>
                <BookOpen className="h-8 w-8 text-green-600" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-sm">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">เวลาเรียน (ชม.)</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.totalStudyTime}</p>
                </div>
                <Clock className="h-8 w-8 text-orange-600" />
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Main Actions */}
          <div className="lg:col-span-2 space-y-6">
            {/* Quick Actions */}
            <Card className="border-0 shadow-sm">
              <CardHeader>
                <CardTitle>เครื่องมือการเรียนรู้</CardTitle>
                <CardDescription>เลือกเครื่องมือที่ต้องการใช้งาน</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-2 gap-4">
                  <Link href="/upload">
                    <Card className="border border-gray-200 hover:border-blue-300 hover:shadow-md transition-all cursor-pointer">
                      <CardContent className="p-6 text-center">
                        <Upload className="h-12 w-12 text-blue-600 mx-auto mb-4" />
                        <h3 className="font-semibold mb-2">อัปโหลดเอกสาร</h3>
                        <p className="text-sm text-gray-600">เพิ่มเอกสารใหม่เพื่อสร้างเครื่องมือการเรียนรู้</p>
                      </CardContent>
                    </Card>
                  </Link>

                  <Link href="/flashcards">
                    <Card className="border border-gray-200 hover:border-purple-300 hover:shadow-md transition-all cursor-pointer">
                      <CardContent className="p-6 text-center">
                        <Zap className="h-12 w-12 text-purple-600 mx-auto mb-4" />
                        <h3 className="font-semibold mb-2">แฟลชการ์ด</h3>
                        <p className="text-sm text-gray-600">ทบทวนความรู้ด้วยแฟลชการ์ดอัจฉริยะ</p>
                      </CardContent>
                    </Card>
                  </Link>

                  <Link href="/quiz">
                    <Card className="border border-gray-200 hover:border-green-300 hover:shadow-md transition-all cursor-pointer">
                      <CardContent className="p-6 text-center">
                        <BookOpen className="h-12 w-12 text-green-600 mx-auto mb-4" />
                        <h3 className="font-semibold mb-2">แบบทดสอบ</h3>
                        <p className="text-sm text-gray-600">ทดสอบความรู้ด้วยแบบทดสอบอัตโนมัติ</p>
                      </CardContent>
                    </Card>
                  </Link>

                  <Link href="/chat">
                    <Card className="border border-gray-200 hover:border-orange-300 hover:shadow-md transition-all cursor-pointer">
                      <CardContent className="p-6 text-center">
                        <MessageSquare className="h-12 w-12 text-orange-600 mx-auto mb-4" />
                        <h3 className="font-semibold mb-2">ถาม AI</h3>
                        <p className="text-sm text-gray-600">สอบถามคำถามเกี่ยวกับเนื้อหา</p>
                      </CardContent>
                    </Card>
                  </Link>
                </div>
              </CardContent>
            </Card>

            {/* Recent Activity */}
            <Card className="border-0 shadow-sm">
              <CardHeader>
                <CardTitle>กิจกรรมล่าสุด</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center space-x-3">
                    <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                    <span className="text-sm">อัปโหลดเอกสาร "คณิตศาสตร์ บทที่ 5"</span>
                    <span className="text-xs text-gray-500 ml-auto">2 ชั่วโมงที่แล้ว</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="w-2 h-2 bg-purple-600 rounded-full"></div>
                    <span className="text-sm">ทำแฟลชการ์ด "สมการเชิงเส้น" 15 ใบ</span>
                    <span className="text-xs text-gray-500 ml-auto">5 ชั่วโมงที่แล้ว</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="w-2 h-2 bg-green-600 rounded-full"></div>
                    <span className="text-sm">ทำแบบทดสอบ "ฟิสิกส์ บทที่ 3" คะแนน 85%</span>
                    <span className="text-xs text-gray-500 ml-auto">1 วันที่แล้ว</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Study Streak */}
            <Card className="border-0 shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Target className="h-5 w-5 text-orange-600" />
                  <span>สถิติการเรียน</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm text-gray-600">เรียนต่อเนื่อง</span>
                      <span className="text-sm font-semibold">{stats.studyStreak} วัน</span>
                    </div>
                    <Progress value={(stats.studyStreak / 30) * 100} className="h-2" />
                  </div>

                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm text-gray-600">เป้าหมายรายสัปดาห์</span>
                      <span className="text-sm font-semibold">5/7 วัน</span>
                    </div>
                    <Progress value={(5 / 7) * 100} className="h-2" />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Performance */}
            <Card className="border-0 shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <TrendingUp className="h-5 w-5 text-green-600" />
                  <span>ผลการเรียน</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">คะแนนเฉลี่ย</span>
                    <span className="text-sm font-semibold text-green-600">82%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">แฟลชการ์ดที่จำได้</span>
                    <span className="text-sm font-semibold text-blue-600">78%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">เวลาเฉลี่ยต่อคำถาม</span>
                    <span className="text-sm font-semibold text-purple-600">12 วิ</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Quick Access */}
            <Card className="border-0 shadow-sm">
              <CardHeader>
                <CardTitle>เข้าถึงด่วน</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <Link href="/reports">
                    <Button
                      variant="outline"
                      className="w-full justify-start bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
                    >
                      <BarChart3 className="h-4 w-4 mr-2" />
                      รายงานความก้าวหน้า
                    </Button>
                  </Link>
                  <Link href="/settings">
                    <Button
                      variant="outline"
                      className="w-full justify-start bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
                    >
                      <Target className="h-4 w-4 mr-2" />
                      ตั้งค่าการเรียนรู้
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
