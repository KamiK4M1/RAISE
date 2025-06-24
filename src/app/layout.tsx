import type React from "react"
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { AuthProvider } from "@/components/providers/session-provider"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "AI Learning - เรียนรู้อย่างชาญฉลาดด้วย AI",
  description: "แพลตฟอร์มการเรียนรู้ที่ขับเคลื่อนด้วยปัญญาประดิษฐ์ ใช้เทคโนโลยี RAG ในการสร้างแฟลชการ์ด แบบทดสอบ และระบบถาม-ตอบอัจฉริยะ",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="th">
      <body className={inter.className}>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  )
}
