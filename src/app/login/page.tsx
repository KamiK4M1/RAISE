"use client"

import type React from "react"
import { useState } from "react"
import { motion } from "framer-motion"
import { signIn, getSession } from "next-auth/react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Brain, Eye, EyeOff, Loader2, Chrome } from "lucide-react"
import Link from "next/link"

export default function LoginPage() {
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  })
  const [error, setError] = useState("")
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError("")

    try {
      const result = await signIn("credentials", {
        email: formData.email,
        password: formData.password,
        redirect: false,
      })

      if (result?.error) {
        setError("อีเมลหรือรหัสผ่านไม่ถูกต้อง")
      } else {
        const session = await getSession()
        if (session) {
          router.push("/dashboard")
        }
      }
    } catch {
      setError("เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง")
    } finally {
      setIsLoading(false)
    }
  }

  const handleGoogleSignIn = async () => {
    setIsLoading(true)
    try {
      await signIn("google", { callbackUrl: "/dashboard" })
    } catch {
      setError("เกิดข้อผิดพลาดในการเข้าสู่ระบบด้วย Google")
    } finally {
      setIsLoading(false)
    }
  }

  const containerVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.6,
        staggerChildren: 0.1,
      },
    },
  }

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.5 },
    },
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center p-4 relative overflow-hidden">
      {/* Background Elements */}
      <div className="absolute inset-0">
        <motion.div
          className="absolute top-20 left-20 w-32 h-32 bg-blue-200 rounded-full opacity-20"
          animate={{
            y: [-10, 10, -10],
            x: [-5, 5, -5],
          }}
          transition={{
            duration: 6,
            repeat: Number.POSITIVE_INFINITY,
            ease: "easeInOut",
          }}
        />
        <motion.div
          className="absolute bottom-20 right-20 w-24 h-24 bg-purple-200 rounded-full opacity-20"
          animate={{
            y: [10, -10, 10],
            x: [5, -5, 5],
          }}
          transition={{
            duration: 8,
            repeat: Number.POSITIVE_INFINITY,
            ease: "easeInOut",
          }}
        />
      </div>

      <motion.div
        className="w-full max-w-md relative z-10"
        initial="hidden"
        animate="visible"
        variants={containerVariants}
      >
        {/* Logo */}
        <motion.div className="text-center mb-8" variants={itemVariants}>
          <Link href="/" className="inline-flex items-center space-x-2">
            <motion.div whileHover={{ rotate: 360 }} transition={{ duration: 0.5 }}>
              <Brain className="h-12 w-12 text-blue-600" />
            </motion.div>
            <span className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              RAISE
            </span>
          </Link>
        </motion.div>

        <motion.div variants={itemVariants}>
          <Card className="border-0 shadow-2xl bg-white/80 backdrop-blur-sm">
            <CardHeader className="text-center pb-6">
              <CardTitle className="text-2xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
                เข้าสู่ระบบ
              </CardTitle>
              <CardDescription className="text-gray-600">เข้าสู่บัญชีของคุณเพื่อเริ่มต้นการเรียนรู้</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {error && (
                <motion.div
                  className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm"
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                >
                  {error}
                </motion.div>
              )}

              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="email" className="text-gray-700 font-medium">
                    อีเมล
                  </Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="กรอกอีเมลของคุณ"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    required
                    className="bg-white/50 border-gray-200 focus:border-blue-400 focus:ring-blue-400"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password" className="text-gray-700 font-medium">
                    รหัสผ่าน
                  </Label>
                  <div className="relative">
                    <Input
                      id="password"
                      type={showPassword ? "text" : "password"}
                      placeholder="กรอกรหัสผ่านของคุณ"
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      required
                      className="bg-white/50 border-gray-200 focus:border-blue-400 focus:ring-blue-400 pr-12"
                    />
                    <motion.button
                      type="button"
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                      onClick={() => setShowPassword(!showPassword)}
                      whileHover={{ scale: 1.1 }}
                      whileTap={{ scale: 0.9 }}
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </motion.button>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <Link href="/forgot-password" className="text-sm text-blue-600 hover:text-blue-700 hover:underline">
                    ลืมรหัสผ่าน?
                  </Link>
                </div>

                <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
                  <Button
                    type="submit"
                    className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white border-0 py-3"
                    disabled={isLoading}
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        กำลังเข้าสู่ระบบ...
                      </>
                    ) : (
                      "เข้าสู่ระบบ"
                    )}
                  </Button>
                </motion.div>
              </form>

              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t border-gray-200" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-white px-2 text-gray-500">หรือ</span>
                </div>
              </div>

              <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleGoogleSignIn}
                  disabled={isLoading}
                  className="w-full bg-white hover:bg-gray-50 border-gray-200 py-3"
                >
                  <Chrome className="mr-2 h-4 w-4" />
                  เข้าสู่ระบบด้วย Google
                </Button>
              </motion.div>

              <div className="text-center">
                <p className="text-sm text-gray-600">
                  ยังไม่มีบัญชี?{" "}
                  <Link href="/register" className="text-blue-600 hover:text-blue-700 font-medium hover:underline">
                    สมัครสมาชิก
                  </Link>
                </p>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </motion.div>
    </div>
  )
}
