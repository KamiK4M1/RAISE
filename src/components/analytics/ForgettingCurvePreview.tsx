"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { TrendingDown, ArrowRight } from "lucide-react"
import { apiService } from "@/lib/api"
import Link from "next/link"

interface ForgettingCurvePoint {
  interval_days: number
  retention_rate: number
  review_count: number
  average_quality: number
  confidence_interval: [number, number]
}

export function ForgettingCurvePreview() {
  const [curveData, setCurveData] = useState<ForgettingCurvePoint[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadPreviewData()
  }, [])

  const loadPreviewData = async () => {
    try {
      const response = await apiService.getForgettingCurve(90)
      
      if (response.success && response.data?.forgetting_curve) {
        // Take only first 4 points for preview
        setCurveData(response.data.forgetting_curve.slice(0, 4))
      } else {
        // Fallback data
        setCurveData([
          { interval_days: 1, retention_rate: 0.92, review_count: 45, average_quality: 4.2, confidence_interval: [0.88, 0.96] },
          { interval_days: 3, retention_rate: 0.85, review_count: 38, average_quality: 3.8, confidence_interval: [0.80, 0.90] },
          { interval_days: 7, retention_rate: 0.78, review_count: 32, average_quality: 3.5, confidence_interval: [0.72, 0.84] },
          { interval_days: 14, retention_rate: 0.72, review_count: 28, average_quality: 3.2, confidence_interval: [0.65, 0.79] }
        ])
      }
    } catch (error) {
      console.error('Error loading forgetting curve preview:', error)
      // Use fallback data
      setCurveData([
        { interval_days: 1, retention_rate: 0.92, review_count: 45, average_quality: 4.2, confidence_interval: [0.88, 0.96] },
        { interval_days: 3, retention_rate: 0.85, review_count: 38, average_quality: 3.8, confidence_interval: [0.80, 0.90] },
        { interval_days: 7, retention_rate: 0.78, review_count: 32, average_quality: 3.5, confidence_interval: [0.72, 0.84] },
        { interval_days: 14, retention_rate: 0.72, review_count: 28, average_quality: 3.2, confidence_interval: [0.65, 0.79] }
      ])
    } finally {
      setLoading(false)
    }
  }

  const getRetentionColor = (rate: number) => {
    if (rate >= 0.8) return 'bg-green-500'
    if (rate >= 0.6) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  const formatInterval = (days: number) => {
    if (days === 1) return '1 วัน'
    if (days < 30) return `${days} วัน`
    return `${Math.round(days / 30)} เดือน`
  }

  if (loading) {
    return (
      <Card className="border-0 shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <TrendingDown className="h-5 w-5 text-blue-600" />
            <span>กราฟการลืม</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="border-0 shadow-sm">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center space-x-2">
              <TrendingDown className="h-5 w-5 text-blue-600" />
              <span>กราฟการลืม</span>
            </CardTitle>
            <CardDescription>อัตราการจำตามช่วงเวลา</CardDescription>
          </div>
          <Link href="/reports">
            <Button variant="outline" size="sm">
              ดูทั้งหมด
              <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          </Link>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {curveData.map((point, index) => (
            <div key={index} className="flex items-center space-x-3">
              <div className="w-12 text-xs text-gray-600 font-medium">
                {formatInterval(point.interval_days)}
              </div>
              <div className="flex-1 bg-gray-200 rounded-full h-4 relative overflow-hidden">
                <div 
                  className={`h-full ${getRetentionColor(point.retention_rate)} transition-all duration-300`}
                  style={{ width: `${point.retention_rate * 100}%` }}
                ></div>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-xs font-medium text-white drop-shadow">
                    {Math.round(point.retention_rate * 100)}%
                  </span>
                </div>
              </div>
              <div className="w-8 text-xs text-gray-500 text-right">
                {point.review_count}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-4 flex items-center justify-between text-sm text-gray-600">
          <span>อัตราการจำ</span>
          <span>จำนวนทบทวน</span>
        </div>

        {/* Key insight */}
        <div className="mt-4 p-3 bg-blue-50 rounded-lg">
          <div className="flex items-center space-x-2 text-blue-800 text-sm">
            <TrendingDown className="h-4 w-4" />
            <span className="font-medium">
              {curveData[0]?.retention_rate > 0.9 
                ? 'อัตราการจำเริ่มต้นดีมาก - สามารถเพิ่มช่วงห่างการทบทวนได้'
                : curveData[curveData.length - 1]?.retention_rate < 0.7
                ? 'ควรเพิ่มการทบทวนเพื่อเสริมสร้างความจำ'
                : 'อัตราการจำอยู่ในเกณฑ์ดี - รักษาระบบการทบทวนปัจจุบัน'
              }
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}