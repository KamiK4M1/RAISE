"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
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
  Upload,
  Zap,
  BookOpen,
  MessageSquare,
  BarChart3,
  FileText,
  Clock,
  Target,
  TrendingUp,
  Trash2,
  Eye,
  LogOut,
  Menu,
  X,
} from "lucide-react"
import Link from "next/link"
import { apiService } from "@/lib/api"
import type { Document } from "@/types/api"
import { AuthWrapper } from "@/components/providers/auth-wrpper"
import { ForgettingCurvePreview } from "@/components/analytics/ForgettingCurvePreview"
import { signOut, useSession } from "next-auth/react"

export default function DashboardPage() {
  const { data: session, status } = useSession()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [stats, setStats] = useState({
    documentsUploaded: 0,
    flashcardsStudied: 0,
    quizzesTaken: 0,
    questionsAsked: 0,
    studyStreak: 0,
    totalStudyTime: 0,
    averageScore: 0,
    flashcardRetention: 0,
    averageTimePerQuestion: 0,
    weeklyGoalDays: 0,
    weeklyGoalTarget: 7,
  })
  const [recentDocuments, setRecentDocuments] = useState<Document[]>([])
  const [recentActivities, setRecentActivities] = useState<Record<string, unknown>[]>([])
  const [user, setUser] = useState<Record<string, unknown> | null>(null)
  const [, setLoading] = useState(true)
  const [deletingDocuments, setDeletingDocuments] = useState<Set<string>>(new Set())
  const [showLogoutDialog, setShowLogoutDialog] = useState(false)
  const [isLoggingOut, setIsLoggingOut] = useState(false)

  const handleLogoutClick = () => {
    setShowLogoutDialog(true)
    setMobileMenuOpen(false)
  }

  const handleLogoutConfirm = async () => {
    setIsLoggingOut(true)

    try {
      apiService.setAuthToken(null)
      await signOut({
        callbackUrl: "/login",
        redirect: true,
      })
    } catch (error) {
      console.error("Logout error:", error)
      if (typeof window !== "undefined") {
        localStorage.removeItem("auth_token")
        await signOut({ callbackUrl: "/login", redirect: true })
      }
    } finally {
      setIsLoggingOut(false)
      setShowLogoutDialog(false)
    }
  }

  const handleLogoutCancel = () => {
    setShowLogoutDialog(false)
  }

  useEffect(() => {
    if (status === "loading" || !session?.accessToken) {
      return
    }

    const loadDashboardData = async () => {
      try {
        try {
          const userResponse = await apiService.getCurrentUser()
          if (userResponse.success && userResponse.data) {
            setUser(userResponse.data)
          }
        } catch (userError) {
          console.error("Failed to load user data:", userError)
        }

        const documentsResponse = await apiService.listDocuments()
        let documentCount = 0
        if (documentsResponse.success && documentsResponse.data) {
          setRecentDocuments(documentsResponse.data.slice(0, 5))
          documentCount = documentsResponse.data.length
        }

        try {
          const analyticsResponse = await apiService.getUserAnalytics()
          if (analyticsResponse.success && analyticsResponse.data) {
            const data = analyticsResponse.data
            setStats({
              documentsUploaded: documentCount,
              flashcardsStudied: data.flashcard_stats?.total_cards || 0,
              quizzesTaken: data.quiz_stats?.total_attempts || 0,
              questionsAsked: data.chat_stats?.total_questions || 0,
              studyStreak: data.flashcard_stats?.streak_days || 0,
              totalStudyTime: Math.round((data.study_patterns?.total_study_time || 0) / 60),
              averageScore: Math.round((data.quiz_stats?.average_score || 0) * 100),
              flashcardRetention: Math.round((data.flashcard_stats?.retention_rate || 0) * 100),
              averageTimePerQuestion: Math.round(data.study_patterns?.average_session_length || 0),
              weeklyGoalDays: data.study_patterns?.weekly_activity?.length || 0,
              weeklyGoalTarget: 7,
            })
          } else {
            setStats({
              documentsUploaded: documentCount,
              flashcardsStudied: 0,
              quizzesTaken: 0,
              questionsAsked: 0,
              studyStreak: 0,
              totalStudyTime: 0,
              averageScore: 0,
              flashcardRetention: 0,
              averageTimePerQuestion: 0,
              weeklyGoalDays: 0,
              weeklyGoalTarget: 7,
            })
          }
        } catch (analyticsError) {
          console.error("Analytics failed, using document count only:", analyticsError)
          setStats({
            documentsUploaded: documentCount,
            flashcardsStudied: 0,
            quizzesTaken: 0,
            questionsAsked: 0,
            studyStreak: 0,
            totalStudyTime: 0,
            averageScore: 0,
            flashcardRetention: 0,
            averageTimePerQuestion: 0,
            weeklyGoalDays: 0,
            weeklyGoalTarget: 7,
          })
        }

        try {
          console.log("Fetching recent activities...")
          const activitiesResponse = await apiService.getRecentActivity(5)
          console.log("Activities response:", activitiesResponse)
          if (activitiesResponse.success && activitiesResponse.data?.activities) {
            console.log("Setting activities:", activitiesResponse.data.activities)
            setRecentActivities(
              Array.isArray((activitiesResponse.data as { activities: Record<string, unknown>[] }).activities)
                ? (activitiesResponse.data as { activities: Record<string, unknown>[] }).activities
                : [],
            )
          } else {
            console.log("No activities data found in response")
          }
        } catch (activitiesError) {
          console.error("Failed to load recent activities:", activitiesError)
        }
      } catch (error) {
        console.error("Error loading dashboard data:", error)
        setStats({
          documentsUploaded: 0,
          flashcardsStudied: 0,
          quizzesTaken: 0,
          questionsAsked: 0,
          studyStreak: 0,
          totalStudyTime: 0,
          averageScore: 0,
          flashcardRetention: 0,
          averageTimePerQuestion: 0,
          weeklyGoalDays: 0,
          weeklyGoalTarget: 7,
        })
      } finally {
        setLoading(false)
      }
    }

    loadDashboardData()
  }, [session, status])

  const handleDeleteDocument = async (documentId: string) => {
    if (!confirm("คุณแน่ใจหรือไม่ว่าต้องการลบเอกสารนี้? การกระทำนี้ไม่สามารถยกเลิกได้")) {
      return
    }

    setDeletingDocuments((prev) => new Set(prev).add(documentId))

    try {
      const response = await apiService.deleteDocument(documentId)
      if (response.success) {
        setRecentDocuments((prev) => prev.filter((doc) => doc.document_id !== documentId))
        setStats((prev) => ({
          ...prev,
          documentsUploaded: prev.documentsUploaded - 1,
        }))
      } else {
        throw new Error(response.message || "Failed to delete document")
      }
    } catch (error) {
      console.error("Error deleting document:", error)
      alert("เกิดข้อผิดพลาดในการลบเอกสาร กรุณาลองใหม่อีกครั้ง")
    } finally {
      setDeletingDocuments((prev) => {
        const newSet = new Set(prev)
        newSet.delete(documentId)
        return newSet
      })
    }
  }

  return (
    <AuthWrapper>
      <div className="min-h-screen bg-gray-50">
        {/* Navigation */}
        <nav className="bg-white border-b sticky top-0 z-50">
          <div className="container mx-auto px-3 sm:px-4 lg:px-6">
            <div className="flex items-center justify-between h-14 sm:h-16">
              {/* Logo */}
              <div className="flex items-center space-x-2 sm:space-x-3">
                <div className="relative">
                  <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg sm:rounded-xl blur opacity-75"></div>
                  <Brain className="relative h-6 w-6 sm:h-8 sm:w-8 text-white bg-gradient-to-r from-blue-600 to-purple-600 p-1 sm:p-1.5 rounded-lg sm:rounded-xl" />
                </div>
                <span className="text-lg sm:text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  RAISE
                </span>
              </div>

              {/* Desktop Navigation */}
              <div className="hidden md:flex items-center space-x-4">
                <span className="text-sm lg:text-base text-gray-600">สวัสดี, {String(user?.name) || "นักเรียน"}</span>
                <Button
                  onClick={handleLogoutClick}
                  variant="outline"
                  size="sm"
                  className="bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
                >
                  <LogOut className="h-4 w-4 mr-2" />
                  ออกจากระบบ
                </Button>
              </div>

              {/* Mobile Menu Button */}
              <div className="md:hidden">
                <Button variant="ghost" size="sm" onClick={() => setMobileMenuOpen(!mobileMenuOpen)} className="p-2">
                  {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
                </Button>
              </div>
            </div>

            {/* Mobile Menu */}
            {mobileMenuOpen && (
              <div className="md:hidden border-t bg-white py-3">
                <div className="flex flex-col space-y-3">
                  <div className="px-3 py-2 text-sm text-gray-600">สวัสดี, {String(user?.name) || "นักเรียน"}</div>
                  <Button
                    onClick={handleLogoutClick}
                    variant="outline"
                    size="sm"
                    className="mx-3 justify-start bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
                  >
                    <LogOut className="h-4 w-4 mr-2" />
                    ออกจากระบบ
                  </Button>
                </div>
              </div>
            )}
          </div>
        </nav>

        <div className="container mx-auto px-3 sm:px-4 lg:px-6 py-4 sm:py-6 lg:py-8">
          {/* Welcome Section */}
          <div className="mb-6 sm:mb-8">
            <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold text-gray-900 mb-2">แดชบอร์ดการเรียนรู้</h1>
            <p className="text-sm sm:text-base text-gray-600">ติดตามความก้าวหน้าและเข้าถึงเครื่องมือการเรียนรู้ของคุณ</p>
          </div>

          {/* Quick Stats */}
          <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 lg:gap-6 mb-6 sm:mb-8">
            <Card className="border-0 shadow-sm hover:shadow-md transition-shadow">
              <CardContent className="p-3 sm:p-4 lg:p-6">
                <div className="flex items-center justify-between">
                  <div className="min-w-0 flex-1">
                    <p className="text-xs sm:text-sm text-gray-600 mb-1">เอกสาร</p>
                    <p className="text-lg sm:text-xl lg:text-2xl font-bold text-gray-900 truncate">
                      {stats.documentsUploaded}
                    </p>
                  </div>
                  <FileText className="h-5 w-5 sm:h-6 sm:w-6 lg:h-8 lg:w-8 text-blue-600 flex-shrink-0 ml-2" />
                </div>
              </CardContent>
            </Card>

            <Card className="border-0 shadow-sm hover:shadow-md transition-shadow">
              <CardContent className="p-3 sm:p-4 lg:p-6">
                <div className="flex items-center justify-between">
                  <div className="min-w-0 flex-1">
                    <p className="text-xs sm:text-sm text-gray-600 mb-1">แฟลชการ์ด</p>
                    <p className="text-lg sm:text-xl lg:text-2xl font-bold text-gray-900 truncate">
                      {stats.flashcardsStudied}
                    </p>
                  </div>
                  <Zap className="h-5 w-5 sm:h-6 sm:w-6 lg:h-8 lg:w-8 text-purple-600 flex-shrink-0 ml-2" />
                </div>
              </CardContent>
            </Card>

            <Card className="border-0 shadow-sm hover:shadow-md transition-shadow">
              <CardContent className="p-3 sm:p-4 lg:p-6">
                <div className="flex items-center justify-between">
                  <div className="min-w-0 flex-1">
                    <p className="text-xs sm:text-sm text-gray-600 mb-1">แบบทดสอบ</p>
                    <p className="text-lg sm:text-xl lg:text-2xl font-bold text-gray-900 truncate">
                      {stats.quizzesTaken}
                    </p>
                  </div>
                  <BookOpen className="h-5 w-5 sm:h-6 sm:w-6 lg:h-8 lg:w-8 text-green-600 flex-shrink-0 ml-2" />
                </div>
              </CardContent>
            </Card>

            <Card className="border-0 shadow-sm hover:shadow-md transition-shadow">
              <CardContent className="p-3 sm:p-4 lg:p-6">
                <div className="flex items-center justify-between">
                  <div className="min-w-0 flex-1">
                    <p className="text-xs sm:text-sm text-gray-600 mb-1">เวลาเรียน (ชม.)</p>
                    <p className="text-lg sm:text-xl lg:text-2xl font-bold text-gray-900 truncate">
                      {stats.totalStudyTime}
                    </p>
                  </div>
                  <Clock className="h-5 w-5 sm:h-6 sm:w-6 lg:h-8 lg:w-8 text-orange-600 flex-shrink-0 ml-2" />
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="grid lg:grid-cols-3 gap-4 sm:gap-6 lg:gap-8">
            {/* Main Content */}
            <div className="lg:col-span-2 space-y-4 sm:space-y-6">
              {/* Quick Actions */}
              <Card className="border-0 shadow-sm">
                <CardHeader className="pb-3 sm:pb-4 lg:pb-6">
                  <CardTitle className="text-base sm:text-lg lg:text-xl">เครื่องมือการเรียนรู้</CardTitle>
                  <CardDescription className="text-xs sm:text-sm">เลือกเครื่องมือที่ต้องการใช้งาน</CardDescription>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
                    {/* Upload Document */}
                    <Link href="/upload" className="block">
                      <Card className="border border-gray-200 hover:border-blue-300 hover:shadow-md transition-all cursor-pointer h-full">
                        <CardContent className="p-4 sm:p-6 text-center h-full flex flex-col justify-center">
                          <Upload className="h-8 w-8 sm:h-10 sm:w-10 lg:h-12 lg:w-12 text-blue-600 mx-auto mb-3 sm:mb-4" />
                          <h3 className="font-semibold mb-2 text-sm sm:text-base">อัปโหลดเอกสาร</h3>
                          <p className="text-xs sm:text-sm text-gray-600 leading-relaxed">
                            เพิ่มเอกสารใหม่เพื่อสร้างเครื่องมือการเรียนรู้
                          </p>
                        </CardContent>
                      </Card>
                    </Link>

                    {/* Flashcards - Featured */}
                    <Card className="border border-gray-200 hover:border-purple-300 hover:shadow-md transition-all cursor-pointer bg-gradient-to-br from-purple-50 to-indigo-50 sm:col-span-2 lg:col-span-2">
                      <CardContent className="p-4 sm:p-6">
                        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4 space-y-3 sm:space-y-0">
                          <div className="flex items-center space-x-3">
                            <div className="p-2 bg-purple-600 rounded-lg flex-shrink-0">
                              <Brain className="h-5 w-5 sm:h-6 sm:w-6 text-white" />
                            </div>
                            <div className="min-w-0">
                              <h3 className="font-semibold text-base sm:text-lg text-gray-900">แฟลชการ์ด</h3>
                              <p className="text-xs sm:text-sm text-gray-600">ทบทวนและสร้างแฟลชการ์ดอัจฉริยะ</p>
                            </div>
                          </div>
                          <div className="text-center sm:text-right flex-shrink-0">
                            <p className="text-xl sm:text-2xl font-bold text-purple-600">{stats.flashcardsStudied}</p>
                            <p className="text-xs text-gray-500">บัตรทั้งหมด</p>
                          </div>
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                          <Link href="/flashcards/library">
                            <Button
                              className="w-full bg-white border border-purple-200 text-purple-700 hover:bg-purple-50 hover:border-purple-300 transition-colors text-sm"
                              variant="outline"
                              size="sm"
                            >
                              <BookOpen className="h-4 w-4 mr-2" />
                              ดูแฟลชการ์ด
                            </Button>
                          </Link>
                          <Link href="/flashcards/generate">
                            <Button
                              className="w-full bg-purple-600 text-white hover:bg-purple-700 transition-colors text-sm"
                              size="sm"
                            >
                              <Zap className="h-4 w-4 mr-2" />
                              สร้างชุดใหม่
                            </Button>
                          </Link>
                        </div>
                      </CardContent>
                    </Card>

                    {/* Quiz */}
                    <Link href="/quiz" className="block">
                      <Card className="border border-gray-200 hover:border-green-300 hover:shadow-md transition-all cursor-pointer h-full">
                        <CardContent className="p-4 sm:p-6 text-center h-full flex flex-col justify-center">
                          <BookOpen className="h-8 w-8 sm:h-10 sm:w-10 lg:h-12 lg:w-12 text-green-600 mx-auto mb-3 sm:mb-4" />
                          <h3 className="font-semibold mb-2 text-sm sm:text-base">แบบทดสอบ</h3>
                          <p className="text-xs sm:text-sm text-gray-600 leading-relaxed">
                            ทดสอบความรู้ด้วยแบบทดสอบอัตโนมัติ
                          </p>
                        </CardContent>
                      </Card>
                    </Link>

                    {/* Chat AI */}
                    <Link href="/chat" className="block">
                      <Card className="border border-gray-200 hover:border-orange-300 hover:shadow-md transition-all cursor-pointer h-full">
                        <CardContent className="p-4 sm:p-6 text-center h-full flex flex-col justify-center">
                          <MessageSquare className="h-8 w-8 sm:h-10 sm:w-10 lg:h-12 lg:w-12 text-orange-600 mx-auto mb-3 sm:mb-4" />
                          <h3 className="font-semibold mb-2 text-sm sm:text-base">ถาม AI</h3>
                          <p className="text-xs sm:text-sm text-gray-600 leading-relaxed">สอบถามคำถามเกี่ยวกับเนื้อหา</p>
                        </CardContent>
                      </Card>
                    </Link>

                    {/* Reports */}
                    <Link href="/reports" className="block">
                      <Card className="border border-gray-200 hover:border-pink-300 hover:shadow-md transition-all cursor-pointer h-full">
                        <CardContent className="p-4 sm:p-6 text-center h-full flex flex-col justify-center">
                          <BarChart3 className="h-8 w-8 sm:h-10 sm:w-10 lg:h-12 lg:w-12 text-pink-600 mx-auto mb-3 sm:mb-4" />
                          <h3 className="font-semibold mb-2 text-sm sm:text-base">รายงาน</h3>
                          <p className="text-xs sm:text-sm text-gray-600 leading-relaxed">ดูสถิติและความคืบหน้า</p>
                        </CardContent>
                      </Card>
                    </Link>
                  </div>
                </CardContent>
              </Card>

              {/* Recent Activity */}
              <Card className="border-0 shadow-sm">
                <CardHeader className="pb-3 sm:pb-4">
                  <CardTitle className="text-base sm:text-lg">กิจกรรมล่าสุด</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3 sm:space-y-4">
                    {recentActivities.length > 0 ? (
                      recentActivities.map((activity, index) => {
                        const getIconColorClass = (color: string) => {
                          switch (color) {
                            case "blue":
                              return "bg-blue-600"
                            case "purple":
                              return "bg-purple-600"
                            case "green":
                              return "bg-green-600"
                            case "orange":
                              return "bg-orange-600"
                            default:
                              return "bg-blue-600"
                          }
                        }

                        return (
                          <div key={index} className="flex items-center space-x-3 py-2">
                            <div
                              className={`w-2 h-2 ${getIconColorClass(String(activity.icon_color) || "blue")} rounded-full flex-shrink-0`}
                            ></div>
                            <span className="text-sm flex-1 min-w-0 truncate">{String(activity.title)}</span>
                            <span className="text-xs text-gray-500 flex-shrink-0">
                              {String(activity.relative_time)}
                            </span>
                          </div>
                        )
                      })
                    ) : (
                      <div className="text-center text-gray-500 text-sm py-8">ยังไม่มีกิจกรรมล่าสุด</div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Recent Documents */}
              <Card className="border-0 shadow-sm">
                <CardHeader className="pb-3 sm:pb-4">
                  <CardTitle className="text-base sm:text-lg">เอกสารล่าสุด</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {recentDocuments.length > 0 ? (
                      recentDocuments.map((document) => (
                        <div
                          key={document.document_id}
                          className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                        >
                          <div className="flex items-center space-x-3 min-w-0 flex-1">
                            <FileText className="h-4 w-4 sm:h-5 sm:w-5 text-blue-600 flex-shrink-0" />
                            <div className="min-w-0 flex-1">
                              <p className="text-sm font-medium text-gray-900 truncate">{document.filename}</p>
                              <p className="text-xs text-gray-500">
                                {new Date(document.created_at).toLocaleDateString("th-TH")}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center space-x-1 sm:space-x-2 flex-shrink-0">
                            <Link href={`/documents/${document.document_id}`}>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="text-blue-600 hover:text-blue-800 p-1 sm:p-2"
                              >
                                <Eye className="h-4 w-4" />
                              </Button>
                            </Link>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDeleteDocument(document.document_id)}
                              disabled={deletingDocuments.has(document.document_id)}
                              className="text-red-600 hover:text-red-800 p-1 sm:p-2"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="text-center text-gray-500 text-sm py-8">ยังไม่มีเอกสารที่อัปโหลด</div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Sidebar */}
            <div className="space-y-4 sm:space-y-6">
              {/* Forgetting Curve Preview */}
              <div className="block">
                <ForgettingCurvePreview />
              </div>

              {/* Study Streak */}
              <Card className="border-0 shadow-sm">
                <CardHeader className="pb-3 sm:pb-4">
                  <CardTitle className="flex items-center space-x-2 text-base sm:text-lg">
                    <Target className="h-4 w-4 sm:h-5 sm:w-5 text-orange-600 flex-shrink-0" />
                    <span>สถิติการเรียน</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
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
                        <span className="text-sm font-semibold">
                          {stats.weeklyGoalDays}/{stats.weeklyGoalTarget} วัน
                        </span>
                      </div>
                      <Progress value={(stats.weeklyGoalDays / stats.weeklyGoalTarget) * 100} className="h-2" />
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Performance */}
              <Card className="border-0 shadow-sm">
                <CardHeader className="pb-3 sm:pb-4">
                  <CardTitle className="flex items-center space-x-2 text-base sm:text-lg">
                    <TrendingUp className="h-4 w-4 sm:h-5 sm:w-5 text-green-600 flex-shrink-0" />
                    <span>ผลการเรียน</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">คะแนนเฉลี่ย</span>
                      <span className="text-sm font-semibold text-green-600">{stats.averageScore}%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">แฟลชการ์ดที่จำได้</span>
                      <span className="text-sm font-semibold text-blue-600">{stats.flashcardRetention}%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">เวลาเฉลี่ยต่อคำถาม</span>
                      <span className="text-sm font-semibold text-purple-600">{stats.averageTimePerQuestion} วิ</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>

        {/* Logout Confirmation Dialog */}
        <Dialog open={showLogoutDialog} onOpenChange={setShowLogoutDialog}>
          <DialogContent className="sm:max-w-md mx-4">
            <DialogHeader>
              <DialogTitle className="text-base sm:text-lg">ออกจากระบบ</DialogTitle>
              <DialogDescription className="text-sm">
                คุณแน่ใจหรือไม่ว่าต้องการออกจากระบบ? คุณจะต้องเข้าสู่ระบบใหม่เพื่อเข้าใช้งาน
              </DialogDescription>
            </DialogHeader>
            <DialogFooter className="flex-col sm:flex-row gap-2 sm:gap-0">
              <Button
                variant="outline"
                onClick={handleLogoutCancel}
                disabled={isLoggingOut}
                className="w-full sm:w-auto order-2 sm:order-1 bg-transparent"
              >
                ยกเลิก
              </Button>
              <Button
                variant="destructive"
                onClick={handleLogoutConfirm}
                disabled={isLoggingOut}
                className="w-full sm:w-auto order-1 sm:order-2"
              >
                {isLoggingOut ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                    กำลังออกจากระบบ...
                  </>
                ) : (
                  <>
                    <LogOut className="h-4 w-4 mr-2" />
                    ออกจากระบบ
                  </>
                )}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </AuthWrapper>
  )
}
