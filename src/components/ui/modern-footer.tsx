"use client"

import { motion } from "framer-motion"
import { Brain, Github, Twitter, Linkedin, Mail, Phone, MapPin, ArrowUp } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import Link from "next/link"

export function ModernFooter() {
  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: "smooth" })
  }

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.2,
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
    <footer className="relative bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 text-white overflow-hidden">
      {/* Animated Background */}
      <div className="absolute inset-0">
        <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-10"></div>
        <motion.div
          className="absolute top-0 left-0 w-full h-full"
          animate={{
            background: [
              "radial-gradient(circle at 20% 50%, rgba(59, 130, 246, 0.1) 0%, transparent 50%)",
              "radial-gradient(circle at 80% 50%, rgba(147, 51, 234, 0.1) 0%, transparent 50%)",
              "radial-gradient(circle at 40% 80%, rgba(59, 130, 246, 0.1) 0%, transparent 50%)",
            ],
          }}
          transition={{
            duration: 8,
            repeat: Number.POSITIVE_INFINITY,
            repeatType: "reverse",
          }}
        />
      </div>

      <div className="relative z-10">
        {/* Newsletter Section */}
        <motion.div
          className="border-b border-white/10 py-12"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={containerVariants}
        >
          <div className="container mx-auto px-4">
            <div className="max-w-4xl mx-auto text-center">
              <motion.h3
                className="text-3xl font-bold mb-4 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent"
                variants={itemVariants}
              >
                อัปเดตข่าวสารและเทคนิคการเรียนรู้ใหม่ๆ
              </motion.h3>
              <motion.p className="text-gray-300 mb-8 text-lg" variants={itemVariants}>
                รับข้อมูลเกี่ยวกับฟีเจอร์ใหม่ เทคนิคการเรียนรู้ และเคล็ดลับจาก AI
              </motion.p>
              <motion.div className="flex flex-col sm:flex-row gap-4 max-w-md mx-auto" variants={itemVariants}>
                <Input
                  type="email"
                  placeholder="กรอกอีเมลของคุณ"
                  className="bg-white/10 border-white/20 text-white placeholder:text-gray-400 focus:border-blue-400"
                />
                <Button className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 border-0 px-8">
                  สมัครรับข่าวสาร
                </Button>
              </motion.div>
            </div>
          </div>
        </motion.div>

        {/* Main Footer Content */}
        <motion.div
          className="py-16"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={containerVariants}
        >
          <div className="container mx-auto px-4">
            <div className="grid lg:grid-cols-4 md:grid-cols-2 gap-8">
              {/* Brand Section */}
              <motion.div className="lg:col-span-1" variants={itemVariants}>
                <div className="flex items-center space-x-3 mb-6">
                  <motion.div whileHover={{ rotate: 360 }} transition={{ duration: 0.5 }}>
                    <Brain className="h-10 w-10 text-blue-400" />
                  </motion.div>
                  <span className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                    AI Learning
                  </span>
                </div>
                <p className="text-gray-300 mb-6 leading-relaxed">
                  แพลตฟอร์มการเรียนรู้ที่ขับเคลื่อนด้วยปัญญาประดิษฐ์ เพื่อการศึกษาที่มีประสิทธิภาพและเข้าถึงได้ทุกที่ทุกเวลา
                </p>
                <div className="flex space-x-4">
                  {[
                    { icon: Github, href: "#", color: "hover:text-gray-300" },
                    { icon: Twitter, href: "#", color: "hover:text-blue-400" },
                    { icon: Linkedin, href: "#", color: "hover:text-blue-500" },
                  ].map((social, index) => (
                    <motion.a
                      key={index}
                      href={social.href}
                      className={`text-gray-400 ${social.color} transition-colors`}
                      whileHover={{ scale: 1.2, y: -2 }}
                      whileTap={{ scale: 0.9 }}
                    >
                      <social.icon className="h-6 w-6" />
                    </motion.a>
                  ))}
                </div>
              </motion.div>

              {/* Products */}
              <motion.div variants={itemVariants}>
                <h4 className="text-lg font-semibold mb-6 text-blue-400">ผลิตภัณฑ์</h4>
                <ul className="space-y-3">
                  {[
                    { name: "แฟลชการ์ดอัจฉริยะ", href: "/flashcards" },
                    { name: "แบบทดสอบอัตโนมัติ", href: "/quiz" },
                    { name: "ระบบถาม-ตอบ AI", href: "/chat" },
                    { name: "รายงานความก้าวหน้า", href: "/reports" },
                    { name: "การวิเคราะห์การเรียนรู้", href: "/analytics" },
                  ].map((item, index) => (
                    <motion.li key={index} whileHover={{ x: 5 }}>
                      <Link href={item.href} className="text-gray-300 hover:text-white transition-colors">
                        {item.name}
                      </Link>
                    </motion.li>
                  ))}
                </ul>
              </motion.div>

              {/* Company */}
              <motion.div variants={itemVariants}>
                <h4 className="text-lg font-semibold mb-6 text-purple-400">บริษัท</h4>
                <ul className="space-y-3">
                  {[
                    { name: "เกี่ยวกับเรา", href: "/about" },
                    { name: "ทีมงาน", href: "/team" },
                    { name: "ข่าวสาร", href: "/news" },
                    { name: "อาชีพ", href: "/careers" },
                    { name: "พันธมิตร", href: "/partners" },
                  ].map((item, index) => (
                    <motion.li key={index} whileHover={{ x: 5 }}>
                      <Link href={item.href} className="text-gray-300 hover:text-white transition-colors">
                        {item.name}
                      </Link>
                    </motion.li>
                  ))}
                </ul>
              </motion.div>

              {/* Contact */}
              <motion.div variants={itemVariants}>
                <h4 className="text-lg font-semibold mb-6 text-green-400">ติดต่อเรา</h4>
                <div className="space-y-4">
                  <motion.div className="flex items-center space-x-3 text-gray-300" whileHover={{ x: 5 }}>
                    <Mail className="h-5 w-5 text-green-400" />
                    <span>support@ailearning.com</span>
                  </motion.div>
                  <motion.div className="flex items-center space-x-3 text-gray-300" whileHover={{ x: 5 }}>
                    <Phone className="h-5 w-5 text-green-400" />
                    <span>02-123-4567</span>
                  </motion.div>
                  <motion.div className="flex items-start space-x-3 text-gray-300" whileHover={{ x: 5 }}>
                    <MapPin className="h-5 w-5 text-green-400 mt-1" />
                    <span>
                      123 ถนนเทคโนโลยี แขวงนวัตกรรม
                      <br />
                      เขตอนาคต กรุงเทพฯ 10110
                    </span>
                  </motion.div>
                </div>

                {/* Quick Links */}
                <div className="mt-8">
                  <h5 className="font-medium mb-4 text-white">ลิงก์ด่วน</h5>
                  <div className="space-y-2">
                    {[
                      { name: "คู่มือการใช้งาน", href: "/guide" },
                      { name: "คำถามที่พบบ่อย", href: "/faq" },
                      { name: "ช่วยเหลือ", href: "/help" },
                    ].map((item, index) => (
                      <motion.div key={index} whileHover={{ x: 5 }}>
                        <Link href={item.href} className="text-gray-300 hover:text-white transition-colors text-sm">
                          {item.name}
                        </Link>
                      </motion.div>
                    ))}
                  </div>
                </div>
              </motion.div>
            </div>
          </div>
        </motion.div>

        {/* Bottom Bar */}
        <motion.div
          className="border-t border-white/10 py-8"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={containerVariants}
        >
          <div className="container mx-auto px-4">
            <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
              <motion.div className="text-gray-400 text-sm" variants={itemVariants}>
                <p>&copy; 2024 AI Learning. สงวนลิขสิทธิ์ทุกประการ</p>
              </motion.div>

              <motion.div
                className="flex flex-wrap justify-center md:justify-end space-x-6 text-sm"
                variants={itemVariants}
              >
                {[
                  { name: "นโยบายความเป็นส่วนตัว", href: "/privacy" },
                  { name: "เงื่อนไขการใช้งาน", href: "/terms" },
                  { name: "นโยบายคุกกี้", href: "/cookies" },
                ].map((item, index) => (
                  <motion.div key={index} whileHover={{ y: -2 }}>
                    <Link href={item.href} className="text-gray-400 hover:text-white transition-colors">
                      {item.name}
                    </Link>
                  </motion.div>
                ))}
              </motion.div>

              <motion.button
                onClick={scrollToTop}
                className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 p-3 rounded-full transition-all duration-300"
                whileHover={{ scale: 1.1, y: -2 }}
                whileTap={{ scale: 0.9 }}
                variants={itemVariants}
              >
                <ArrowUp className="h-5 w-5" />
              </motion.button>
            </div>
          </div>
        </motion.div>
      </div>
    </footer>
  )
}
