"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Brain, ArrowLeft, TrendingUp, Target, Clock, Award, BookOpen, Zap, MessageSquare, BarChart3, PieChart, LineChart, Activity, Lightbulb, AlertCircle, Star, ChevronRight } from "lucide-react"
import Link from "next/link"
import { apiService } from "@/lib/api"
import { UserAnalytics } from "@/types/api"
import { AuthWrapper } from "@/components/providers/auth-wrpper"

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
  const [subjectPerformance, setSubjectPerformance] = useState<Array<{subject: string, score: number, improvement: string, color: string}>>([])
  const [bloomTaxonomy, setBloomTaxonomy] = useState<Array<{level: string, score: number, questions: number}>>([])
  const [recommendations, setRecommendations] = useState<Array<{type: string, title: string, description: string, priority: string}>>([])
  const [performanceAnalysis, setPerformanceAnalysis] = useState<{strengths: string[], weaknesses: string[], trends: Array<{metric: string, trend: string, change: number}>}>({strengths: [], weaknesses: [], trends: []})
  const [learningVelocity, setLearningVelocity] = useState<Array<{week: string, velocity: number, retention: number}>>([])
  const [studyPatterns, setStudyPatterns] = useState<{pattern: string, consistency: number, optimalTimes: string[], sessionLength: number}>({})
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    const loadReportsData = async () => {
      try {
        const days = timeRange === "week" ? 7 : 30
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
            strengths: data.flashcard_stats.strong_subjects || ['คณิตศาสตร์', 'ฟิสิกส์'],
            weaknesses: data.flashcard_stats.weak_subjects || ['เคมี', 'ชีววิทยา'],
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
            pattern: data.study_patterns.pattern || 'consistent',
            consistency: data.study_patterns.consistency_score || 85,
            optimalTimes: data.study_patterns.optimal_times || ['เช้า', 'เย็น'],
            sessionLength: data.study_patterns.average_session_length || 45
          })
          
          if (data.study_patterns.weekly_activity) {
            setWeeklyProgress(data.study_patterns.weekly_activity.map(item => ({
              day: item.day,
              studyTime: item.hours_studied,
              score: Math.round(Math.random() * 20 + 70) // Mock score for demo
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
  }, [timeRange])

  return (
    <AuthWrapper>
      <div className="min-h-screen bg-gray-50">
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
                    <p className="text-2xl font-bold text-green-600">+{stats.improvementRate}%</p>
                  </div>
                  <TrendingUp className="h-8 w-8 text-green-600" />
                </div>
              </CardContent>
            </Card>
          </div>

          <Tabs defaultValue="overview" className="space-y-6">
            <TabsList className="grid w-full grid-cols-6">
              <TabsTrigger value="overview">ภาพรวม</TabsTrigger>
              <TabsTrigger value="performance">ผลงาน</TabsTrigger>
              <TabsTrigger value="skills">ทักษะการคิด</TabsTrigger>
              <TabsTrigger value="patterns">รูปแบบการเรียน</TabsTrigger>
              <TabsTrigger value="recommendations">คำแนะนำ</TabsTrigger>
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
                            <span className="text-sm font-medium">คะแนน: {day.score}%</span>
                          </div>
                          <div className="flex space-x-2">
                            <Progress value={(day.studyTime / 4) * 100} className="flex-1 h-2" />
                            <Progress value={day.score} className="flex-1 h-2" />
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
                  <CardTitle>ทักษะการคิดตาม Bloom's Taxonomy</CardTitle>
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

            <TabsContent value="recommendations" className="space-y-6">
              {/* AI-Powered Recommendations */}
              <Card className="border-0 shadow-sm">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Lightbulb className="h-5 w-5 text-yellow-600" />
                    <span>คำแนะนำเฉพาะบุคคล</span>
                  </CardTitle>
                  <CardDescription>คำแนะนำจาก AI ตามผลการเรียนของคุณ</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {recommendations.map((rec, index) => (
                      <div key={index} className={`p-4 rounded-lg border-l-4 ${
                        rec.priority === 'high' ? 'border-red-500 bg-red-50' :
                        rec.priority === 'medium' ? 'border-yellow-500 bg-yellow-50' :
                        'border-green-500 bg-green-50'
                      }`}>
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center space-x-2 mb-2">
                              <span className={`text-sm font-medium px-2 py-1 rounded ${
                                rec.priority === 'high' ? 'bg-red-100 text-red-800' :
                                rec.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                                'bg-green-100 text-green-800'
                              }`}>
                                {rec.priority === 'high' ? 'สำคัญมาก' : 
                                 rec.priority === 'medium' ? 'สำคัญ' : 'ทั่วไป'}
                              </span>
                            </div>
                            <h4 className="font-semibold text-gray-900 mb-1">{rec.title}</h4>
                            <p className="text-sm text-gray-600">{rec.description}</p>
                          </div>
                          <ChevronRight className="h-5 w-5 text-gray-400" />
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

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
                          <span>• แบบทดสอบ Bloom's ระดับสูง</span>
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
                      <span>เพิ่มทักษะการคิดระดับ "สร้างสรรค์"</span>
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
        </div>
      </div>
      </div>
    </AuthWrapper>
  )
}
