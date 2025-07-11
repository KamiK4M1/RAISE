"use client"

import { useState, useEffect } from "react"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { apiService } from "@/lib/api"
import { UserAnalytics } from "@/types/api"

const processChartData = (data: UserAnalytics["forgetting_curve"]) => {
  if (!data || data.length === 0) return []

  return data.map(item => ({
    name: new Date(item.date).toLocaleDateString("th-TH", { month: "short", day: "numeric" }),
    "ความจำ": Math.round(item.retention_rate * 100),
    "คาดการณ์": Math.round(item.predicted_retention * 100),
  }))
}

export function ForgettingCurveChart() {
  const [analytics, setAnalytics] = useState<UserAnalytics | null>(null)
  const [timeFrame, setTimeFrame] = useState("30d")
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        setLoading(true)
        setError(null)
        const response = await apiService.getForgettingCurve()
        if (response.success && response.data) {
          setAnalytics(response.data as unknown as UserAnalytics)
        } else {
          throw new Error(response.message || "Failed to fetch analytics")
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "An unknown error occurred")
      } finally {
        setLoading(false)
      }
    }
    fetchAnalytics()
  }, [])

  const chartData = analytics ? processChartData(analytics.forgetting_curve) : []

  if (loading) {
    return (
      <Card className="border-0 shadow-sm">
        <CardHeader>
          <CardTitle>กราฟการลืม (Forgetting Curve)</CardTitle>
          <CardDescription>กำลังโหลดข้อมูล...</CardDescription>
        </CardHeader>
        <CardContent className="h-[300px] flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="border-0 shadow-sm">
        <CardHeader>
          <CardTitle>กราฟการลืม (Forgetting Curve)</CardTitle>
          <CardDescription>เกิดข้อผิดพลาด</CardDescription>
        </CardHeader>
        <CardContent className="h-[300px] flex items-center justify-center text-red-600">
          <p>{error}</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="border-0 shadow-sm">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>กราฟการลืม (Forgetting Curve)</CardTitle>
            <CardDescription>
              แสดงอัตราการจำและคาดการณ์การลืมของคุณ
            </CardDescription>
          </div>
          <Select value={timeFrame} onValueChange={setTimeFrame}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="เลือกระยะเวลา" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7d">7 วันล่าสุด</SelectItem>
              <SelectItem value="30d">30 วันล่าสุด</SelectItem>
              <SelectItem value="90d">90 วันล่าสุด</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart
            data={chartData}
            margin={{
              top: 5,
              right: 30,
              left: 20,
              bottom: 5,
            }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis unit="%" />
            <Tooltip
              contentStyle={{
                borderRadius: "0.5rem",
                boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
              }}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="ความจำ"
              stroke="#3b82f6"
              strokeWidth={2}
              activeDot={{ r: 8 }}
            />
            <Line
              type="monotone"
              dataKey="คาดการณ์"
              stroke="#8b5cf6"
              strokeDasharray="5 5"
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
