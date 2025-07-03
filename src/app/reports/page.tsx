"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Brain, ArrowLeft, TrendingUp, Target, Clock, Award, BookOpen, Zap, MessageSquare } from "lucide-react"
import Link from "next/link"
import { apiService } from "@/lib/api"
import { UserAnalytics } from "@/types/api"

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
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="overview">ภาพรวม</TabsTrigger>
              <TabsTrigger value="subjects">รายวิชา</TabsTrigger>
              <TabsTrigger value="skills">ทักษะการคิด</TabsTrigger>
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

            <TabsContent value="subjects" className="space-y-6">
              <Card className="border-0 shadow-sm">
                <CardHeader>
                  <CardTitle>ผลการเรียนรายวิชา</CardTitle>
                  <CardDescription>คะแนนและการพัฒนาในแต่ละวิชา</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {subjectPerformance.map((subject, index) => (
                      <div key={index} className="flex items-center space-x-4 p-4 bg-gray-50 rounded-lg">
                        <div className={`w-4 h-4 rounded-full ${subject.color}`}></div>
                        <div className="flex-1">
                          <div className="flex justify-between items-center mb-2">
                            <span className="font-medium">{subject.subject}</span>
                            <div className="flex items-center space-x-2">
                              <span className="text-sm text-green-600 font-medium">{subject.improvement}</span>
                              <span className="font-bold">{subject.score}%</span>
                            </div>
                          </div>
                          <Progress value={subject.score} className="h-2" />
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
                      </div>
                    ))}
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

          {/* Recommendations */}
          <Card className="border-0 shadow-sm bg-blue-50">
            <CardHeader>
              <CardTitle className="text-blue-900">คำแนะนำสำหรับการพัฒนา</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 text-blue-800">
                <div className="flex items-start space-x-2">
                  <div className="w-2 h-2 bg-blue-600 rounded-full mt-2 flex-shrink-0"></div>
                  <p>ควรเพิ่มเวลาในการทำแบบทดสอบระดับ "สร้างสรรค์" เพื่อพัฒนาทักษะการคิดขั้นสูง</p>
                </div>
                <div className="flex items-start space-x-2">
                  <div className="w-2 h-2 bg-blue-600 rounded-full mt-2 flex-shrink-0"></div>
                  <p>แนะนำให้ทบทวนแฟลชการ์ดวิชาฟิสิกส์เพิ่มเติม เนื่องจากมีอัตราการจำต่ำกว่าค่าเฉลี่ย</p>
                </div>
                <div className="flex items-start space-x-2">
                  <div className="w-2 h-2 bg-blue-600 rounded-full mt-2 flex-shrink-0"></div>
                  <p>การเรียนต่อเนื่อง 7 วันแสดงให้เห็นถึงความมุ่งมั่น ควรรักษาจังหวะนี้ต่อไป</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
