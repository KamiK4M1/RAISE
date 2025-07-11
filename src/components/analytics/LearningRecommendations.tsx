"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Lightbulb, ChevronRight, TrendingUp, Target, AlertCircle, CheckCircle2, Clock, Star } from "lucide-react"
import { apiService } from "@/lib/api"

interface LearningRecommendation {
  type: string
  priority: "high" | "medium" | "low"
  title: string
  description: string
  action_items: string[]
  estimated_improvement: number
}

// interface LearningRecommendationsData {
//   recommendations: LearningRecommendation[]
//   total_recommendations: number
// }

export function LearningRecommendations() {
  const [recommendations, setRecommendations] = useState<LearningRecommendation[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedRec, setExpandedRec] = useState<number | null>(null)

  useEffect(() => {
    loadRecommendations()
  }, [])

  const loadRecommendations = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await apiService.getLearningRecommendations()
      
      if (response.success && response.data) {
        const recommendations = (response.data as { recommendations?: LearningRecommendation[] }).recommendations
        setRecommendations(Array.isArray(recommendations) ? recommendations : [])
      } else {
        throw new Error(response.message || 'Failed to load recommendations')
      }
    } catch (error) {
      console.error('Error loading recommendations:', error)
      setError('ไม่สามารถโหลดคำแนะนำได้')
      
      // Fallback mock data
      setRecommendations([
        {
          type: "focus_area",
          priority: "high",
          title: "ปรับปรุงความแม่นยำ",
          description: "อัตราความถูกต้องของคุณต่ำกว่า 70% ควรลดการ์ดใหม่และเน้นทบทวน",
          action_items: [
            "ลดจำนวนการ์ดใหม่ต่อวันลง 50%",
            "เพิ่มเวลาในการทบทวนการ์ดเก่า",
            "ใช้เทคนิคการจำที่หลากหลาย"
          ],
          estimated_improvement: 15
        },
        {
          type: "review_schedule",
          priority: "high",
          title: "จัดการภาระงานที่สะสม",
          description: "คุณมีการ์ดค้างเยอะ ควรปรับตารางการเรียน",
          action_items: [
            "ทบทวนการ์ด 30 ใบต่อวัน",
            "หยุดเพิ่มการ์ดใหม่ชั่วคราว",
            "แบ่งเซสชันการเรียนเป็น 2-3 ครั้งต่อวัน"
          ],
          estimated_improvement: 20
        },
        {
          type: "difficulty_adjustment",
          priority: "medium",
          title: "ปรับความยากของการ์ด",
          description: "การ์ดส่วนใหญ่มีความยากสูง ควรทบทวนบ่อยขึ้น",
          action_items: [
            "เพิ่มความถี่ในการทบทวน",
            "แบ่งการ์ดยากออกเป็นส่วนเล็ก ๆ",
            "ใช้เทคนิค Active Recall มากขึ้น"
          ],
          estimated_improvement: 10
        },
        {
          type: "review_schedule",
          priority: "medium",
          title: "เพิ่มความสม่ำเสมอ",
          description: "ควรเรียนให้สม่ำเสมอมากขึ้นเพื่อผลลัพธ์ที่ดีขึ้น",
          action_items: [
            "กำหนดเวลาเรียนประจำวัน",
            "ตั้งการแจ้งเตือนสำหรับการทบทวน",
            "เรียนทุกวันแม้จะเพียงเล็กน้อย"
          ],
          estimated_improvement: 25
        },
        {
          type: "focus_area",
          priority: "low",
          title: "ผลงานดีเยี่ยม!",
          description: "คุณมีความแม่นยำสูงมาก สามารถเพิ่มการ์ดใหม่ได้",
          action_items: [
            "เพิ่มการ์ดใหม่ 20-30% ต่อวัน",
            "ทดลองเนื้อหาที่ท้าทายมากขึ้น",
            "ช่วยเหลือผู้เรียนคนอื่น"
          ],
          estimated_improvement: 5
        }
      ])
    } finally {
      setLoading(false)
    }
  }

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'high':
        return <AlertCircle className="h-4 w-4 text-red-600" />
      case 'medium':
        return <Clock className="h-4 w-4 text-yellow-600" />
      case 'low':
        return <CheckCircle2 className="h-4 w-4 text-green-600" />
      default:
        return <Target className="h-4 w-4 text-blue-600" />
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'border-red-500 bg-red-50'
      case 'medium':
        return 'border-yellow-500 bg-yellow-50'
      case 'low':
        return 'border-green-500 bg-green-50'
      default:
        return 'border-blue-500 bg-blue-50'
    }
  }

  const getPriorityText = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'สำคัญมาก'
      case 'medium':
        return 'สำคัญ'
      case 'low':
        return 'ทั่วไป'
      default:
        return 'ปกติ'
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'focus_area':
        return <Target className="h-4 w-4" />
      case 'review_schedule':
        return <Clock className="h-4 w-4" />
      case 'difficulty_adjustment':
        return <TrendingUp className="h-4 w-4" />
      default:
        return <Lightbulb className="h-4 w-4" />
    }
  }

  if (loading) {
    return (
      <Card className="border-0 shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Lightbulb className="h-5 w-5 text-yellow-600" />
            <span>คำแนะนำเฉพาะบุคคล</span>
          </CardTitle>
          <CardDescription>คำแนะนำจาก AI ตามผลการเรียนของคุณ</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-yellow-600"></div>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="border-0 shadow-sm">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Lightbulb className="h-5 w-5 text-yellow-600" />
            <span>คำแนะนำเฉพาะบุคคล</span>
          </div>
          <Button 
            variant="outline" 
            size="sm"
            onClick={loadRecommendations}
            disabled={loading}
          >
            รีเฟรช
          </Button>
        </CardTitle>
        <CardDescription>คำแนะนำจาก AI ตามผลการเรียนของคุณ</CardDescription>
      </CardHeader>
      <CardContent>
        {error && (
          <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="flex items-center space-x-2 text-yellow-700">
              <AlertCircle className="h-4 w-4" />
              <span className="text-sm">{error} - แสดงข้อมูลตัวอย่าง</span>
            </div>
          </div>
        )}

        <div className="space-y-4">
          {recommendations.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              <Star className="h-12 w-12 text-gray-300 mx-auto mb-3" />
              <p>ยังไม่มีคำแนะนำ</p>
              <p className="text-sm">เริ่มใช้งานระบบเพื่อรับคำแนะนำ</p>
            </div>
          ) : (
            recommendations.map((rec, index) => (
              <div 
                key={index} 
                className={`p-4 rounded-lg border-l-4 ${getPriorityColor(rec.priority)} transition-all duration-200 hover:shadow-md`}
              >
                <div 
                  className="flex items-start justify-between cursor-pointer"
                  onClick={() => setExpandedRec(expandedRec === index ? null : index)}
                >
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className={`text-xs font-medium px-2 py-1 rounded ${
                        rec.priority === 'high' ? 'bg-red-100 text-red-800' :
                        rec.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        {getPriorityText(rec.priority)}
                      </span>
                      {getTypeIcon(rec.type)}
                      <span className="text-xs text-gray-600 capitalize">{rec.type.replace('_', ' ')}</span>
                    </div>
                    <h4 className="font-semibold text-gray-900 mb-1 flex items-center space-x-2">
                      {getPriorityIcon(rec.priority)}
                      <span>{rec.title}</span>
                    </h4>
                    <p className="text-sm text-gray-600 mb-2">{rec.description}</p>
                    
                    {rec.estimated_improvement > 0 && (
                      <div className="flex items-center space-x-2 text-xs text-gray-500">
                        <TrendingUp className="h-3 w-3" />
                        <span>คาดว่าจะปรับปรุง: +{rec.estimated_improvement}%</span>
                      </div>
                    )}
                  </div>
                  <ChevronRight 
                    className={`h-5 w-5 text-gray-400 transition-transform duration-200 ${
                      expandedRec === index ? 'rotate-90' : ''
                    }`} 
                  />
                </div>

                {expandedRec === index && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <h5 className="font-medium text-gray-900 mb-3">แผนปฏิบัติ:</h5>
                    <div className="space-y-2">
                      {rec.action_items.map((item, itemIndex) => (
                        <div key={itemIndex} className="flex items-start space-x-3">
                          <div className="flex-shrink-0 w-5 h-5 rounded-full bg-blue-100 flex items-center justify-center mt-0.5">
                            <span className="text-xs font-medium text-blue-600">{itemIndex + 1}</span>
                          </div>
                          <span className="text-sm text-gray-700">{item}</span>
                        </div>
                      ))}
                    </div>
                    
                    <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                      <div className="flex items-center space-x-2 text-blue-800">
                        <Star className="h-4 w-4" />
                        <span className="text-sm font-medium">
                          ลำดับความสำคัญ: {getPriorityText(rec.priority)}
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        {recommendations.length > 0 && (
          <div className="mt-6 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg">
            <h4 className="font-semibold text-blue-900 mb-2">เคล็ดลับการใช้คำแนะนำ</h4>
            <div className="space-y-1 text-sm text-blue-800">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <span>เริ่มจากคำแนะนำที่มีความสำคัญสูงก่อน</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                <span>ทำทีละข้อเพื่อให้เห็นผลชัดเจน</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span>คำแนะนำจะอัปเดตตามผลการเรียนของคุณ</span>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}