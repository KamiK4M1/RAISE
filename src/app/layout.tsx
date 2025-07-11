import type React from "react"
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { AuthProvider } from "@/components/providers/session-provider"
import { SpeedInsights } from "@vercel/speed-insights/next"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "RAISE - ยกระดับการเรียนรู้ด้วย AI",
  description: "แพลตฟอร์มการเรียนรู้อัจฉริยะที่ใช้เทคโนโลยี RAG และ AI เพื่อสร้างแฟลชการ์ด แบบทดสอบ และระบบถาม-ตอบที่ปรับเปลี่ยนตามสไตล์การเรียนรู้ของคุณ",
  keywords: ["AI", "การเรียนรู้", "แฟลชการ์ด", "แบบทดสอบ", "RAG", "ปัญญาประดิษฐ์", "การศึกษา"],
  authors: [{ name: "RAISE Team" }],
  openGraph: {
    title: "RAISE - ยกระดับการเรียนรู้ด้วย AI",
    description: "แพลตฟอร์มการเรียนรู้อัจฉริยะที่ใช้เทคโนโลยี RAG และ AI เพื่อสร้างแฟลชการ์ด แบบทดสอบ และระบบถาม-ตอบที่ปรับเปลี่ยนตามสไตล์การเรียนรู้ของคุณ",
    type: "website",
    locale: "th_TH",
  },
  twitter: {
    card: "summary_large_image",
    title: "RAISE - ยกระดับการเรียนรู้ด้วย AI",
    description: "แพลตฟอร์มการเรียนรู้อัจฉริยะที่ใช้เทคโนโลยี RAG และ AI",
  },
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
        <SpeedInsights />
      </body>
    </html>
  )
}