"use client"

import { useState, useEffect } from "react"
import { useSession } from "next-auth/react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
// import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Brain, ArrowLeft, TrendingUp, Target, Clock, Award, BookOpen, Zap, MessageSquare, BarChart3, PieChart, Activity, AlertCircle, Star } from "lucide-react"
import Link from "next/link"
import { apiService } from "@/lib/api"
// import { UserAnalytics } from "@/types/api"
import { AuthWrapper } from "@/components/providers/auth-wrpper"
import { ForgettingCurveChart } from "@/components/analytics/ForgettingCurveChart"
import { LearningRecommendations } from "@/components/analytics/LearningRecommendations"

export default function ReportsPage() {
  const [timeRange, setTimeRange] = useState("week")
  const [stats, setStats] = useState({
    totalStudyTime: 0,
    documentsStudied: 0,
    flashcardsReviewed: 0,
    quizzesTaken: 0,
    questionsAsked: 0,
    averageScore: 0,
    studyStreak: 0,
    improvementRate: 0,
  })
  const [weeklyProgress, setWeeklyProgress] = useState<Array<{day: string, studyTime: number, score: number}>>([])
  // const [subjectPerformance, setSubjectPerformance] = useState<Array<{subject: string, score: number, improvement: string, color: string}>>([])
  const [bloomTaxonomy, setBloomTaxonomy] = useState<Array<{level: string, score: number, questions: number}>>([])
  const [, setRecommendations] = useState<Array<{type: string, title: string, description: string, priority: string}>>([])
  const [performanceAnalysis, setPerformanceAnalysis] = useState<{strengths: string[], weaknesses: string[], trends: Array<{metric: string, trend: string, change: number}>}>({strengths: [], weaknesses: [], trends: []})
  const [learningVelocity, setLearningVelocity] = useState<Array<{week: string, velocity: number, retention: number}>>([])
  const [studyPatterns, setStudyPatterns] = useState<{pattern: string, consistency: number, optimalTimes: string[], sessionLength: number}>({ pattern: '', consistency: 0, optimalTimes: [], sessionLength: 0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { status } = useSession()
  
  useEffect(() => {
    // Don't try to load data if session is still loading or user is not authenticated
    if (status === "loading") return
    if (status === "unauthenticated") {
      setError("กรุณาเข้าสู่ระบบเพื่อดูรายงาน")
      setLoading(false)
      return
    }
    
    const loadReportsData = async () => {
      try {
        setError(null)
        // const days = timeRange === "week" ? 7 : 30
        const response = await apiService.getUserAnalytics()
        
        if (response.success && response.data) {
          const data = response.data
          
          setStats({
            totalStudyTime: Math.round(data.study_patterns.total_study_time / 60),
            documentsStudied: data.learning_progress.total_documents_studied,
            flashcardsReviewed: data.flashcard_stats.total_reviews,
            quizzesTaken: data.quiz_stats.total_attempts,
            questionsAsked: data.chat_stats.total_questions,
            averageScore: Math.round(data.quiz_stats.average_score),
            studyStreak: data.flashcard_stats.streak_days,
            improvementRate: Math.round(data.quiz_stats.improvement_rate),
          })
          
          // Set recommendations
          if (data.recommendations) {
            setRecommendations(data.recommendations)
          }
          
          // Set performance analysis
          setPerformanceAnalysis({
            strengths: (data.flashcard_stats as Record<string, unknown>).strong_subjects as string[] || ['คณิตศาสตร์', 'ฟิสิกส์'],
            weaknesses: (data.flashcard_stats as Record<string, unknown>).weak_subjects as string[] || ['เคมี', 'ชีววิทยา'],
            trends: [
              { metric: 'คะแนนเฉลี่ย', trend: 'เพิ่มขึ้น', change: data.quiz_stats.improvement_rate || 12 },
              { metric: 'ความเร็วในการเรียน', trend: 'เพิ่มขึ้น', change: 8 },
              { metric: 'อัตราการจำ', trend: 'คงที่', change: 2 }
            ]
          })
          
          // Set learning velocity
          setLearningVelocity([
            { week: 'สัปดาห์ที่ 1', velocity: 15, retention: 78 },
            { week: 'สัปดาห์ที่ 2', velocity: 18, retention: 82 },
            { week: 'สัปดาห์ที่ 3', velocity: 22, retention: 85 },
            { week: 'สัปดาห์ที่ 4', velocity: 25, retention: 88 }
          ])
          
          // Set study patterns
          setStudyPatterns({
            pattern: (data.study_patterns as Record<string, unknown>).pattern as string || 'consistent',
            consistency: data.study_patterns.consistency_score || 85,
            optimalTimes: (data.study_patterns as Record<string, unknown>).optimal_times as string[] || ['เช้า', 'เย็น'],
            sessionLength: data.study_patterns.average_session_length || 45
          })
          
          if (data.study_patterns.weekly_activity) {
            setWeeklyProgress(data.study_patterns.weekly_activity.map(item => ({
              day: item.day,
              studyTime: item.hours_studied,
              score: item.score
            })))
          }
          
          if (data.quiz_stats.bloom_averages) {
            const bloomLevels = [
              { key: "remember", label: "จำ (Remember)" },
              { key: "understand", label: "เข้าใจ (Understand)" },
              { key: "apply", label: "ประยุกต์ (Apply)" },
              { key: "analyze", label: "วิเคราะห์ (Analyze)" },
              { key: "evaluate", label: "ประเมิน (Evaluate)" },
              { key: "create", label: "สร้างสรรค์ (Create)" }
            ]
            
            setBloomTaxonomy(bloomLevels.map(level => ({
              level: level.label,
              score: Math.round((data.quiz_stats.bloom_averages[level.key] || 0) * 100),
              questions: Math.round(Math.random() * 30 + 10) // Mock question count
            })))
          }
        }
      } catch (error) {
        console.error('Error loading reports data:', error)
        setError(`ไม่สามารถโหลดข้อมูลรายงานได้: ${error instanceof Error ? error.message : 'เกิดข้อผิดพลาดไม่ทราบสาเหตุ'}`)
        // Fallback to mock data
        setStats({
          totalStudyTime: 45,
          documentsStudied: 12,
          flashcardsReviewed: 156,
          quizzesTaken: 8,
          questionsAsked: 23,
          averageScore: 82,
          studyStreak: 7,
          improvementRate: 15,
        })
        
        setRecommendations([
          {
            type: 'study_optimization',
            title: 'เพิ่มการทบทวนแฟลชการ์ด',
            description: 'ควรเพิ่มเวลาในการทบทวนแฟลชการ์ดวิชาเคมี เนื่องจากมีอัตราการจำต่ำกว่าค่าเฉลี่ย',
            priority: 'high'
          },
          {
            type: 'bloom_taxonomy',
            title: 'พัฒนาทักษะการคิดขั้นสูง',
            description: 'ควรเพิ่มเวลาในการทำแบบทดสอบระดับ "สร้างสรรค์" เพื่อพัฒนาทักษะการคิดขั้นสูง',
            priority: 'medium'
          },
          {
            type: 'study_pattern',
            title: 'รักษาความสม่ำเสมอ',
            description: 'การเรียนต่อเนื่อง 7 วันแสดงให้เห็นถึงความมุ่งมั่น ควรรักษาจังหวะนี้ต่อไป',
            priority: 'low'
          }
        ])
        
        setPerformanceAnalysis({
          strengths: ['คณิตศาสตร์', 'ฟิสิกส์', 'ภาษาอังกฤษ'],
          weaknesses: ['เคมี', 'ชีววิทยา'],
          trends: [
            { metric: 'คะแนนเฉลี่ย', trend: 'เพิ่มขึ้น', change: 12 },
            { metric: 'ความเร็วในการเรียน', trend: 'เพิ่มขึ้น', change: 8 },
            { metric: 'อัตราการจำ', trend: 'คงที่', change: 2 }
          ]
        })
        
        setLearningVelocity([
          { week: 'สัปดาห์ที่ 1', velocity: 15, retention: 78 },
          { week: 'สัปดาห์ที่ 2', velocity: 18, retention: 82 },
          { week: 'สัปดาห์ที่ 3', velocity: 22, retention: 85 },
          { week: 'สัปดาห์ที่ 4', velocity: 25, retention: 88 }
        ])
        
        setStudyPatterns({
          pattern: 'consistent',
          consistency: 85,
          optimalTimes: ['เช้า', 'เย็น'],
          sessionLength: 45
        })
        
        setWeeklyProgress([
          { day: "จ", studyTime: 2.5, score: 78 },
          { day: "อ", studyTime: 1.8, score: 82 },
          { day: "พ", studyTime: 3.2, score: 85 },
          { day: "พฤ", studyTime: 2.1, score: 79 },
          { day: "ศ", studyTime: 4.0, score: 88 },
          { day: "ส", studyTime: 1.5, score: 84 },
          { day: "อา", studyTime: 2.8, score: 86 },
        ])
        
        setBloomTaxonomy([
          { level: "จำ (Remember)", score: 92, questions: 45 },
          { level: "เข้าใจ (Understand)", score: 88, questions: 38 },
          { level: "ประยุกต์ (Apply)", score: 82, questions: 32 },
          { level: "วิเคราะห์ (Analyze)", score: 75, questions: 28 },
          { level: "ประเมิน (Evaluate)", score: 68, questions: 22 },
          { level: "สร้างสรรค์ (Create)", score: 62, questions: 18 },
        ])
      } finally {
        setLoading(false)
      }
    }

    loadReportsData()
  }, [timeRange, status])  // Add status dependency

  return (
    <AuthWrapper>
      <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
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
          <div className="flex items-center space-x-2">
            <Button
              variant={timeRange === "week" ? "default" : "outline"}
              size="sm"
              onClick={() => setTimeRange("week")}
              className={
                timeRange === "week"
                  ? "bg-blue-600 text-white"
                  : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
              }
            >
              สัปดาห์นี้
            </Button>
            <Button
              variant={timeRange === "month" ? "default" : "outline"}
              size="sm"
              onClick={() => setTimeRange("month")}
              className={
                timeRange === "month"
                  ? "bg-blue-600 text-white"
                  : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
              }
            >
              เดือนนี้
            </Button>
          </div>
        </div>
      </nav>
      

      <div className="container mx-auto px-4 py-8">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">รายงานความก้าวหน้า</h1>
            <p className="text-gray-600">ติดตามและวิเคราะห์ผลการเรียนรู้ของคุณ</p>
          </div>

          {/* Error Display */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-center space-x-2 text-red-700">
                <AlertCircle className="h-5 w-5" />
                <span className="font-medium">เกิดข้อผิดพลาด</span>
              </div>
              <p className="text-red-600 text-sm mt-1">{error}</p>
            </div>
          )}

          {/* Loading Display */}
          {loading && !error && (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <span className="ml-3 text-gray-600">กำลังโหลดข้อมูล...</span>
            </div>
          )}

          {/* Main Content - Only show when not loading and no error */}
          {!loading && !error && (
            <>
              {/* Overview Stats */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <Card className="border-0 shadow-sm">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">เวลาเรียนรวม</p>
                    <p className="text-2xl font-bold text-gray-900">{stats.totalStudyTime}ชม.</p>
                  </div>
                  <Clock className="h-8 w-8 text-blue-600" />
                </div>
              </CardContent>
            </Card>

            <Card className="border-0 shadow-sm">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">คะแนนเฉลี่ย</p>
                    <p className="text-2xl font-bold text-gray-900">{stats.averageScore}%</p>
                  </div>
                  <Award className="h-8 w-8 text-yellow-600" />
                </div>
              </CardContent>
            </Card>

            <Card className="border-0 shadow-sm">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">เรียนต่อเนื่อง</p>
                    <p className="text-2xl font-bold text-gray-900">{stats.studyStreak} วัน</p>
                  </div>
                  <Target className="h-8 w-8 text-green-600" />
                </div>
              </CardContent>
            </Card>

            <Card className="border-0 shadow-sm">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">การพัฒนา</p>
                    <p className="text-2xl font-bold text-green-600">+{stats.improvementRate || 0}%</p>
                  </div>
                  <TrendingUp className="h-8 w-8 text-green-600" />
                </div>
              </CardContent>
            </Card>
          </div>

          <Tabs defaultValue="overview" className="space-y-6">
            <TabsList className="grid w-full grid-cols-7">
              <TabsTrigger value="overview">ภาพรวม</TabsTrigger>
  

              <TabsTrigger value="activities">กิจกรรม</TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="space-y-6">
              {/* Weekly Progress Chart */}
              <Card className="border-0 shadow-sm">
                <CardHeader>
                  <CardTitle>ความก้าวหน้ารายสัปดาห์</CardTitle>
                  <CardDescription>เวลาเรียนและคะแนนเฉลี่ยในแต่ละวัน</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {weeklyProgress.map((day, index) => (
                      <div key={index} className="flex items-center space-x-4">
                        <div className="w-8 text-center font-medium text-gray-600">{day.day}</div>
                        <div className="flex-1">
                          <div className="flex justify-between items-center mb-1">
                            <span className="text-sm text-gray-600">เวลาเรียน: {day.studyTime} ชม.</span>
                          </div>
                          <div className="flex space-x-2">
                            <Progress value={(day.studyTime / 4) * 100} className="flex-1 h-2" />
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Study Goals */}
              <Card className="border-0 shadow-sm">
                <CardHeader>
                  <CardTitle>เป้าหมายการเรียน</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm text-gray-600">เป้าหมายรายสัปดาห์ (5 วัน)</span>
                        <span className="text-sm font-medium">5/7 วัน</span>
                      </div>
                      <Progress value={(5 / 7) * 100} className="h-2" />
                    </div>

                    <div>
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm text-gray-600">เป้าหมายเวลาเรียน (20 ชม./สัปดาห์)</span>
                        <span className="text-sm font-medium">18/20 ชม.</span>
                      </div>
                      <Progress value={(18 / 20) * 100} className="h-2" />
                    </div>

                    <div>
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm text-gray-600">เป้าหมายคะแนนเฉลี่ย (80%)</span>
                        <span className="text-sm font-medium">{stats.averageScore}/80%</span>
                      </div>
                      <Progress value={(stats.averageScore / 80) * 100} className="h-2" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="performance" className="space-y-6">
              {/* Performance Analysis */}
              <div className="grid md:grid-cols-2 gap-6">
                <Card className="border-0 shadow-sm">
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <Star className="h-5 w-5 text-yellow-600" />
                      <span>จุดแข็ง</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {performanceAnalysis.strengths.map((strength, index) => (
                        <div key={index} className="flex items-center space-x-3 p-3 bg-green-50 rounded-lg">
                          <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                          <span className="text-green-800 font-medium">{strength}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card className="border-0 shadow-sm">
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <AlertCircle className="h-5 w-5 text-red-600" />
                      <span>จุดที่ต้องพัฒนา</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {performanceAnalysis.weaknesses.map((weakness, index) => (
                        <div key={index} className="flex items-center space-x-3 p-3 bg-red-50 rounded-lg">
                          <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                          <span className="text-red-800 font-medium">{weakness}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Performance Trends */}
              <Card className="border-0 shadow-sm">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <TrendingUp className="h-5 w-5 text-blue-600" />
                    <span>แนวโน้มผลงาน</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {performanceAnalysis.trends.map((trend, index) => (
                      <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                        <div className="flex items-center space-x-3">
                          <div className={`w-3 h-3 rounded-full ${
                            trend.trend === 'เพิ่มขึ้น' ? 'bg-green-500' : 
                            trend.trend === 'ลดลง' ? 'bg-red-500' : 'bg-gray-500'
                          }`}></div>
                          <span className="font-medium">{trend.metric}</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className={`text-sm font-medium ${
                            trend.trend === 'เพิ่มขึ้น' ? 'text-green-600' : 
                            trend.trend === 'ลดลง' ? 'text-red-600' : 'text-gray-600'
                          }`}>
                            {trend.trend === 'เพิ่มขึ้น' ? '+' : trend.trend === 'ลดลง' ? '-' : ''}{trend.change}%
                          </span>
                          <span className="text-sm text-gray-500">{trend.trend}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Learning Velocity */}
              <Card className="border-0 shadow-sm">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Activity className="h-5 w-5 text-purple-600" />
                    <span>ความเร็วการเรียนรู้</span>
                  </CardTitle>
                  <CardDescription>ความเร็วและอัตราการจำในแต่ละสัปดาห์</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {learningVelocity.map((week, index) => (
                      <div key={index} className="space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="font-medium">{week.week}</span>
                          <div className="flex items-center space-x-4">
                            <div className="flex items-center space-x-2">
                              <span className="text-sm text-gray-600">ความเร็ว:</span>
                              <span className="font-medium">{week.velocity} การ์ด/ชม.</span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <span className="text-sm text-gray-600">การจำ:</span>
                              <span className="font-medium">{week.retention}%</span>
                            </div>
                          </div>
                        </div>
                        <div className="flex space-x-2">
                          <Progress value={(week.velocity / 30) * 100} className="flex-1 h-2" />
                          <Progress value={week.retention} className="flex-1 h-2" />
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="skills" className="space-y-6">
              <Card className="border-0 shadow-sm">
                <CardHeader>
                  <CardTitle>ทักษะการคิดตาม Bloom&apos;s Taxonomy</CardTitle>
                  <CardDescription>ประเมินความสามารถในแต่ละระดับการคิด</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {bloomTaxonomy.map((level, index) => (
                      <div key={index} className="space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="font-medium">{level.level}</span>
                          <div className="flex items-center space-x-2">
                            <span className="text-sm text-gray-600">{level.questions} คำถาม</span>
                            <span className="font-bold">{level.score}%</span>
                          </div>
                        </div>
                        <Progress value={level.score} className="h-2" />
                        <div className="text-xs text-gray-500">
                          {level.score >= 80 ? 'เก่งมาก' : level.score >= 60 ? 'ดี' : 'ต้องปรับปรุง'}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Bloom's Taxonomy Radar Chart Representation */}
              <Card className="border-0 shadow-sm">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <BarChart3 className="h-5 w-5 text-blue-600" />
                    <span>การกระจายทักษะการคิด</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    {bloomTaxonomy.map((level, index) => (
                      <div key={index} className="text-center">
                        <div className="relative w-16 h-16 mx-auto mb-2">
                          <div className="absolute inset-0 rounded-full bg-gray-200"></div>
                          <div 
                            className={`absolute inset-0 rounded-full ${
                              level.score >= 80 ? 'bg-green-500' : 
                              level.score >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                            }`}
                            style={{ 
                              clipPath: `polygon(50% 50%, 50% 0%, ${50 + (level.score / 100) * 50}% 0%, 50% 50%)`,
                              transform: `rotate(${index * 60}deg)` 
                            }}
                          ></div>
                          <div className="absolute inset-0 flex items-center justify-center">
                            <span className="text-sm font-bold">{level.score}%</span>
                          </div>
                        </div>
                        <div className="text-xs text-gray-600">{level.level.split(' ')[0]}</div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="patterns" className="space-y-6">
              {/* Study Patterns Analysis */}
              <Card className="border-0 shadow-sm">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <PieChart className="h-5 w-5 text-purple-600" />
                    <span>รูปแบบการเรียน</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid md:grid-cols-2 gap-6">
                    <div className="space-y-4">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">รูปแบบการเรียน</span>
                        <span className="font-medium capitalize">
                          {studyPatterns.pattern === 'consistent' ? 'สม่ำเสมอ' : 
                           studyPatterns.pattern === 'intensive' ? 'เข้มข้น' : 'หลากหลาย'}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">ความสม่ำเสมอ</span>
                        <span className="font-medium">{studyPatterns.consistency}%</span>
                      </div>
                      <Progress value={studyPatterns.consistency} className="h-2" />
                    </div>
                    <div className="space-y-4">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">ระยะเวลาเซชชั่นเฉลี่ย</span>
                        <span className="font-medium">{studyPatterns.sessionLength} นาที</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">เวลาที่เหมาะสม</span>
                        <span className="font-medium">{studyPatterns.optimalTimes?.join(', ')}</span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Study Schedule Optimization */}
              <Card className="border-0 shadow-sm">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Clock className="h-5 w-5 text-green-600" />
                    <span>การเพิ่มประสิทธิภาพการเรียน</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid md:grid-cols-3 gap-4">
                    <div className="text-center p-4 bg-blue-50 rounded-lg">
                      <div className="text-2xl font-bold text-blue-600 mb-2">{studyPatterns.sessionLength}นาที</div>
                      <div className="text-sm text-blue-800">ระยะเวลาเซชชั่นที่เหมาะสม</div>
                    </div>
                    <div className="text-center p-4 bg-green-50 rounded-lg">
                      <div className="text-2xl font-bold text-green-600 mb-2">15นาที</div>
                      <div className="text-sm text-green-800">ควรพักทุก</div>
                    </div>
                    <div className="text-center p-4 bg-purple-50 rounded-lg">
                      <div className="text-2xl font-bold text-purple-600 mb-2">{studyPatterns.optimalTimes?.length || 2}</div>
                      <div className="text-sm text-purple-800">ช่วงเวลาที่เหมาะสม</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="advanced" className="space-y-6">
              {/* Forgetting Curve Analysis */}
              <ForgettingCurveChart />

              {/* Advanced Learning Statistics */}
              <Card className="border-0 shadow-sm">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <BarChart3 className="h-5 w-5 text-purple-600" />
                    <span>สถิติการเรียนรู้ขั้นสูง</span>
                  </CardTitle>
                  <CardDescription>ข้อมูลเชิงลึกจากระบบ Spaced Repetition</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="p-4 bg-blue-50 rounded-lg">
                      <div className="text-2xl font-bold text-blue-600 mb-1">2.4</div>
                      <div className="text-sm text-blue-800">ค่า Ease Factor เฉลี่ย</div>
                      <div className="text-xs text-gray-600 mt-1">ความยากเฉลี่ยของการ์ด</div>
                    </div>
                    
                    <div className="p-4 bg-green-50 rounded-lg">
                      <div className="text-2xl font-bold text-green-600 mb-1">85%</div>
                      <div className="text-sm text-green-800">อัตราการจำ</div>
                      <div className="text-xs text-gray-600 mt-1">เฉลี่ย 30 วันล่าสุด</div>
                    </div>
                    
                    <div className="p-4 bg-yellow-50 rounded-lg">
                      <div className="text-2xl font-bold text-yellow-600 mb-1">1.8</div>
                      <div className="text-sm text-yellow-800">ความเร็วการเรียน</div>
                      <div className="text-xs text-gray-600 mt-1">การ์ดที่จำได้ต่อวัน</div>
                    </div>
                    
                    <div className="p-4 bg-purple-50 rounded-lg">
                      <div className="text-2xl font-bold text-purple-600 mb-1">78%</div>
                      <div className="text-sm text-purple-800">คะแนนความสม่ำเสมอ</div>
                      <div className="text-xs text-gray-600 mt-1">การเรียนอย่างต่อเนื่อง</div>
                    </div>
                  </div>

                  <div className="mt-6 grid md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-3">การพยากรณ์ภาระงาน (7 วันข้างหน้า)</h4>
                      <div className="space-y-3">
                        {[
                          { day: 'วันนี้', cards: 25 },
                          { day: 'พรุ่งนี้', cards: 18 },
                          { day: 'มะรืนนี้', cards: 32 },
                          { day: 'วันที่ 4', cards: 15 },
                          { day: 'วันที่ 5', cards: 28 },
                          { day: 'วันที่ 6', cards: 22 },
                          { day: 'วันที่ 7', cards: 19 }
                        ].map((item, index) => (
                          <div key={index} className="flex items-center justify-between">
                            <span className="text-sm text-gray-600">{item.day}</span>
                            <div className="flex items-center space-x-2">
                              <div className="w-24 bg-gray-200 rounded-full h-2">
                                <div 
                                  className="bg-blue-600 h-2 rounded-full"
                                  style={{ width: `${(item.cards / 50) * 100}%` }}
                                ></div>
                              </div>
                              <span className="text-sm font-medium w-8">{item.cards}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div>
                      <h4 className="font-semibold text-gray-900 mb-3">การกระจายระดับความยาก</h4>
                      <div className="space-y-3">
                        {[
                          { level: 'ง่าย (EF > 2.5)', percentage: 45, color: 'bg-green-500' },
                          { level: 'ปานกลาง (EF 2.0-2.5)', percentage: 35, color: 'bg-yellow-500' },
                          { level: 'ยาก (EF < 2.0)', percentage: 20, color: 'bg-red-500' }
                        ].map((item, index) => (
                          <div key={index} className="space-y-1">
                            <div className="flex justify-between text-sm">
                              <span className="text-gray-700">{item.level}</span>
                              <span className="font-medium">{item.percentage}%</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div 
                                className={`${item.color} h-2 rounded-full transition-all duration-300`}
                                style={{ width: `${item.percentage}%` }}
                              ></div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Learning Velocity Over Time */}
              <Card className="border-0 shadow-sm">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <TrendingUp className="h-5 w-5 text-green-600" />
                    <span>แนวโน้มความเร็วการเรียนรู้</span>
                  </CardTitle>
                  <CardDescription>ความเร็วในการเรียนรู้และอัตราการจำในช่วง 4 สัปดาห์ล่าสุด</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {learningVelocity.map((week, index) => (
                      <div key={index} className="relative">
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium text-gray-900">{week.week}</span>
                          <div className="flex items-center space-x-4 text-sm text-gray-600">
                            <span>เร็ว: {week.velocity} การ์ด/ชม.</span>
                            <span>จำได้: {week.retention}%</span>
                          </div>
                        </div>
                        <div className="flex space-x-2">
                          <div className="flex-1 bg-gray-200 rounded-full h-3 relative overflow-hidden">
                            <div 
                              className="bg-gradient-to-r from-blue-500 to-blue-600 h-full rounded-full transition-all duration-500"
                              style={{ width: `${(week.velocity / 30) * 100}%` }}
                            ></div>
                          </div>
                          <div className="flex-1 bg-gray-200 rounded-full h-3 relative overflow-hidden">
                            <div 
                              className="bg-gradient-to-r from-green-500 to-green-600 h-full rounded-full transition-all duration-500"
                              style={{ width: `${week.retention}%` }}
                            ></div>
                          </div>
                        </div>
                        {index === learningVelocity.length - 1 && (
                          <div className="absolute -right-2 -top-1">
                            <div className="bg-blue-600 text-white text-xs px-2 py-1 rounded-full">ล่าสุด</div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                  
                  <div className="mt-6 p-4 bg-gradient-to-r from-green-50 to-blue-50 rounded-lg">
                    <h4 className="font-semibold text-gray-900 mb-2">การวิเคราะห์แนวโน้ม</h4>
                    <div className="grid md:grid-cols-2 gap-4 text-sm text-gray-700">
                      <div>
                        <div className="flex items-center space-x-2 mb-1">
                          <TrendingUp className="h-4 w-4 text-green-600" />
                          <span className="font-medium">ความเร็วการเรียนรู้</span>
                        </div>
                        <p>เพิ่มขึ้น 67% ในช่วง 4 สัปดาห์ล่าสุด</p>
                      </div>
                      <div>
                        <div className="flex items-center space-x-2 mb-1">
                          <Target className="h-4 w-4 text-blue-600" />
                          <span className="font-medium">อัตราการจำ</span>
                        </div>
                        <p>ปรับปรุงขึ้น 13% และมีเสถียรภาพ</p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="recommendations" className="space-y-6">
              {/* AI-Powered Recommendations */}
              <LearningRecommendations />

              {/* Study Plan Generator */}
              <Card className="border-0 shadow-sm">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Target className="h-5 w-5 text-blue-600" />
                    <span>แผนการเรียนแนะนำ</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="p-4 bg-blue-50 rounded-lg">
                      <h4 className="font-semibold text-blue-900 mb-2">แผนสำหรับสัปดาห์หน้า</h4>
                      <div className="space-y-2 text-sm text-blue-800">
                        <div className="flex justify-between">
                          <span>• ทบทวนแฟลชการ์ดเคมี</span>
                          <span>จันทร์-พุธ (30 นาที/วัน)</span>
                        </div>
                        <div className="flex justify-between">
                          <span>• แบบทดสอบ Bloom&apos;s ระดับสูง</span>
                          <span>พฤหัสบดี-ศุกร์ (45 นาที/วัน)</span>
                        </div>
                        <div className="flex justify-between">
                          <span>• ทบทวนจุดอ่อนชีววิทยา</span>
                          <span>เสาร์-อาทิตย์ (60 นาที/วัน)</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="activities" className="space-y-6">
              <div className="grid md:grid-cols-2 gap-6">
                <Card className="border-0 shadow-sm">
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <BookOpen className="h-5 w-5 text-blue-600" />
                      <span>การอ่านเอกสาร</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">เอกสารที่ศึกษา</span>
                        <span className="font-medium">{stats.documentsStudied} ไฟล์</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">เวลาเฉลี่ยต่อเอกสาร</span>
                        <span className="font-medium">3.8 ชม.</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">ความเข้าใจเฉลี่ย</span>
                        <span className="font-medium text-green-600">85%</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="border-0 shadow-sm">
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <Zap className="h-5 w-5 text-purple-600" />
                      <span>แฟลชการ์ด</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">การ์ดที่ทบทวน</span>
                        <span className="font-medium">{stats.flashcardsReviewed} ใบ</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">อัตราการจำ</span>
                        <span className="font-medium text-green-600">78%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">เวลาเฉลี่ยต่อการ์ด</span>
                        <span className="font-medium">8 วิ</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="border-0 shadow-sm">
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <Award className="h-5 w-5 text-green-600" />
                      <span>แบบทดสอบ</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">แบบทดสอบที่ทำ</span>
                        <span className="font-medium">{stats.quizzesTaken} ครั้ง</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">คะแนนเฉลี่ย</span>
                        <span className="font-medium text-green-600">{stats.averageScore}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">เวลาเฉลี่ยต่อข้อ</span>
                        <span className="font-medium">45 วิ</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="border-0 shadow-sm">
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <MessageSquare className="h-5 w-5 text-orange-600" />
                      <span>การถาม AI</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">คำถามที่ถาม</span>
                        <span className="font-medium">{stats.questionsAsked} คำถาม</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">ความพึงพอใจ</span>
                        <span className="font-medium text-green-600">4.2/5</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">เวลาตอบเฉลี่ย</span>
                        <span className="font-medium">2.3 วิ</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>
          </Tabs>

          {/* Quick Analytics Summary */}
          <Card className="border-0 shadow-sm bg-gradient-to-r from-blue-50 to-purple-50">
            <CardHeader>
              <CardTitle className="text-blue-900">สรุปผลการเรียน</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 gap-6">
                <div className="space-y-3">
                  <h4 className="font-semibold text-blue-900">ไฮไลท์</h4>
                  <div className="space-y-2 text-sm text-blue-800">
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      <span>คะแนนเฉลี่ยเพิ่มขึ้น {stats.improvementRate}% ใน{timeRange === 'week' ? 'สัปดาห์' : 'เดือน'}นี้</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                      <span>เรียนต่อเนื่อง {stats.studyStreak} วัน</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                      <span>ทำแบบทดสอบ {stats.quizzesTaken} ครั้ง</span>
                    </div>
                  </div>
                </div>
                <div className="space-y-3">
                  <h4 className="font-semibold text-blue-900">เป้าหมายถัดไป</h4>
                  <div className="space-y-2 text-sm text-blue-800">
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                      <span>เพิ่มทักษะการคิดระดับ &quot;สร้างสรรค์&quot;</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                      <span>ปรับปรุงคะแนนวิชาเคมี</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      <span>รักษาความสม่ำเสมอในการเรียน</span>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
            </>
          )}
        </div>
      </div>
      </div>
    </AuthWrapper>
  )
}
