"use client"
import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Upload, Brain, MessageSquare, BarChart3, BookOpen, Zap, Target, Sparkles, Users, Award } from "lucide-react"
import Link from "next/link"
import { ModernFooter } from "@/components/ui/modern-footer"

export default function HomePage() {
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

  const floatingVariants = {
    animate: {
      y: [-10, 10, -10],
      transition: {
        duration: 3,
        repeat: Number.POSITIVE_INFINITY,
        ease: [0.42, 0, 0.58, 1], // cubic-bezier for easeInOut
      },
    },
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 overflow-hidden">
      {/* Navigation */}
      <motion.nav
        className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50"
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <motion.div className="flex items-center space-x-2" whileHover={{ scale: 1.05 }}>
            <motion.div whileHover={{ rotate: 360 }} transition={{ duration: 0.5 }}>
              <Brain className="h-8 w-8 text-blue-600" />
            </motion.div>
            <span className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              AI Learning
            </span>
          </motion.div>
          <div className="flex items-center space-x-4">
            <Link href="/login">
              <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                <Button variant="outline" className="bg-white text-gray-700 border-gray-300 hover:bg-gray-50">
                  เข้าสู่ระบบ
                </Button>
              </motion.div>
            </Link>
            <Link href="/register">
              <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                <Button className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white border-0">
                  สมัครสมาชิก
                </Button>
              </motion.div>
            </Link>
          </div>
        </div>
      </motion.nav>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-16 lg:py-24 text-center relative">
        {/* Floating Elements */}
        <motion.div
          className="absolute top-20 left-10 w-20 h-20 bg-blue-200 rounded-full opacity-20"
          variants={floatingVariants}
          animate="animate"
        />
        <motion.div
          className="absolute top-40 right-20 w-16 h-16 bg-purple-200 rounded-full opacity-20"
          variants={floatingVariants}
          animate="animate"
          transition={{ delay: 1 }}
        />
        <motion.div
          className="absolute bottom-20 left-1/4 w-12 h-12 bg-green-200 rounded-full opacity-20"
          variants={floatingVariants}
          animate="animate"
          transition={{ delay: 2 }}
        />

        <motion.div className="max-w-5xl mx-auto" initial="hidden" animate="visible" variants={containerVariants}>
          <motion.div
            className="inline-flex items-center space-x-2 bg-gradient-to-r from-blue-100 to-purple-100 px-4 py-2 rounded-full mb-8"
            variants={itemVariants}
          >
            <Sparkles className="h-4 w-4 text-blue-600" />
            <span className="text-sm font-medium text-gray-700">ขับเคลื่อนด้วย AI ล่าสุด</span>
          </motion.div>

          <motion.h1
            className="text-4xl md:text-6xl lg:text-7xl font-bold text-gray-900 mb-6 leading-tight"
            variants={itemVariants}
          >
            เรียนรู้อย่างชาญฉลาด
            <br />
            <span className="bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
              ด้วย AI
            </span>
          </motion.h1>

          <motion.p
            className="text-xl md:text-2xl text-gray-600 mb-12 leading-relaxed max-w-4xl mx-auto"
            variants={itemVariants}
          >
            แพลตฟอร์มการเรียนรู้ที่ขับเคลื่อนด้วยปัญญาประดิษฐ์ ใช้เทคโนโลยี RAG ในการสร้างแฟลชการ์ด แบบทดสอบ และระบบถาม-ตอบอัจฉริยะ
            เพื่อส่งเสริมการเรียนรู้ด้วยตนเองอย่างมีประสิทธิภาพ
          </motion.p>

          <motion.div className="flex flex-col sm:flex-row gap-4 justify-center mb-16" variants={itemVariants}>
            <Link href="/register">
              <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                <Button
                  size="lg"
                  className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-8 py-4 text-lg border-0"
                >
                  เริ่มต้นใช้งานฟรี
                  <Sparkles className="ml-2 h-5 w-5" />
                </Button>
              </motion.div>
            </Link>
            <Link href="/demo">
              <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                <Button
                  size="lg"
                  variant="outline"
                  className="bg-white/80 backdrop-blur-sm text-gray-700 border-gray-300 hover:bg-white px-8 py-4 text-lg"
                >
                  ดูตัวอย่างการใช้งาน
                </Button>
              </motion.div>
            </Link>
          </motion.div>

          {/* Stats */}
          <motion.div className="grid grid-cols-2 md:grid-cols-4 gap-8 max-w-3xl mx-auto" variants={containerVariants}>
            {[
              { icon: Users, number: "10K+", label: "ผู้ใช้งาน" },
              { icon: BookOpen, number: "50K+", label: "เอกสาร" },
              { icon: Award, number: "95%", label: "ความพึงพอใจ" },
              { icon: Zap, number: "24/7", label: "พร้อมใช้งาน" },
            ].map((stat, index) => (
              <motion.div key={index} className="text-center" variants={itemVariants} whileHover={{ scale: 1.05 }}>
                <stat.icon className="h-8 w-8 text-blue-600 mx-auto mb-2" />
                <div className="text-2xl font-bold text-gray-900">{stat.number}</div>
                <div className="text-sm text-gray-600">{stat.label}</div>
              </motion.div>
            ))}
          </motion.div>
        </motion.div>
      </section>

      {/* Features Section */}
      <section className="container mx-auto px-4 py-16 lg:py-24">
        <motion.div
          className="text-center mb-16"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={containerVariants}
        >
          <motion.h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4" variants={itemVariants}>
            คุณสมบัติเด่นของระบบ
          </motion.h2>
          <motion.p className="text-lg md:text-xl text-gray-600 max-w-3xl mx-auto" variants={itemVariants}>
            เครื่องมือการเรียนรู้ครบครันที่ออกแบบมาเพื่อเพิ่มประสิทธิภาพการศึกษา
          </motion.p>
        </motion.div>

        <motion.div
          className="grid md:grid-cols-2 lg:grid-cols-3 gap-8"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={containerVariants}
        >
          {[
            {
              icon: Upload,
              title: "อัปโหลดเอกสาร",
              description: "รองรับไฟล์ PDF, DOCX, TXT ระบบจะประมวลผลและวิเคราะห์เนื้อหาโดยอัตโนมัติ",
              color: "from-blue-500 to-blue-600",
              bgColor: "bg-blue-50",
            },
            {
              icon: Zap,
              title: "แฟลชการ์ดอัจฉริยะ",
              description: "ใช้เทคนิค Spaced Repetition เพื่อเพิ่มประสิทธิภาพการจำและลดเวลาทบทวน",
              color: "from-purple-500 to-purple-600",
              bgColor: "bg-purple-50",
            },
            {
              icon: BookOpen,
              title: "แบบทดสอบอัตโนมัติ",
              description: "สร้างแบบทดสอบที่ครอบคลุมทุกระดับตาม Bloom's Taxonomy",
              color: "from-green-500 to-green-600",
              bgColor: "bg-green-50",
            },
            {
              icon: MessageSquare,
              title: "ระบบถาม-ตอบ AI",
              description: "ตอบคำถามเกี่ยวกับเนื้อหาได้อย่างแม่นยำ พร้อมแสดงแหล่งที่มา",
              color: "from-orange-500 to-orange-600",
              bgColor: "bg-orange-50",
            },
            {
              icon: BarChart3,
              title: "รายงานความก้าวหน้า",
              description: "ติดตามผลการเรียนรู้ วิเคราะห์จุดแข็ง-จุดอ่อน และแนะนำการปรับปรุง",
              color: "from-red-500 to-red-600",
              bgColor: "bg-red-50",
            },
            {
              icon: Target,
              title: "การเรียนรู้เฉพาะบุคคล",
              description: "ปรับแผนการเรียนรู้ตามความสามารถและพฤติกรรมของผู้ใช้แต่ละคน",
              color: "from-indigo-500 to-indigo-600",
              bgColor: "bg-indigo-50",
            },
          ].map((feature, index) => (
            <motion.div
              key={index}
              variants={itemVariants}
              whileHover={{ scale: 1.05, y: -5 }}
              transition={{ duration: 0.2 }}
            >
              <Card
                className={`border-0 shadow-lg hover:shadow-xl transition-all duration-300 ${feature.bgColor} h-full`}
              >
                <CardHeader className="text-center p-8">
                  <motion.div
                    className={`w-16 h-16 rounded-2xl bg-gradient-to-r ${feature.color} flex items-center justify-center mx-auto mb-6`}
                    whileHover={{ rotate: 360 }}
                    transition={{ duration: 0.5 }}
                  >
                    <feature.icon className="h-8 w-8 text-white" />
                  </motion.div>
                  <CardTitle className="text-xl mb-4">{feature.title}</CardTitle>
                  <CardDescription className="text-gray-600 leading-relaxed">{feature.description}</CardDescription>
                </CardHeader>
              </Card>
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* Stats Section */}
      <motion.section
        className="bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 text-white py-16 lg:py-24 relative overflow-hidden"
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
        variants={containerVariants}
      >
        {/* Background Pattern */}
        <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-10"></div>

        <div className="container mx-auto px-4 relative z-10">
          <motion.div className="text-center mb-12" variants={itemVariants}>
            <h2 className="text-3xl md:text-4xl font-bold mb-4">ผลลัพธ์ที่พิสูจน์แล้ว</h2>
            <p className="text-xl text-blue-100">ตัวเลขที่แสดงถึงประสิทธิภาพของระบบ</p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8 text-center">
            {[
              { number: "70%", label: "ลดการลืมเนื้อหาที่เรียน", description: "ด้วยเทคนิค Spaced Repetition" },
              { number: "50%", label: "ประหยัดเวลาในการทบทวน", description: "เรียนรู้อย่างมีประสิทธิภาพ" },
              { number: "6", label: "ระดับการคิดตาม Bloom's Taxonomy", description: "ครอบคลุมทุกทักษะการคิด" },
            ].map((stat, index) => (
              <motion.div key={index} className="text-center" variants={itemVariants} whileHover={{ scale: 1.05 }}>
                <motion.div
                  className="text-5xl md:text-6xl font-bold mb-2"
                  initial={{ scale: 0 }}
                  whileInView={{ scale: 1 }}
                  viewport={{ once: true }}
                  transition={{ delay: index * 0.2, type: "spring", stiffness: 100 }}
                >
                  {stat.number}
                </motion.div>
                <div className="text-xl font-semibold mb-2">{stat.label}</div>
                <div className="text-blue-100">{stat.description}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </motion.section>

      {/* CTA Section */}
      <motion.section
        className="container mx-auto px-4 py-16 lg:py-24 text-center"
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
        variants={containerVariants}
      >
        <motion.div className="max-w-4xl mx-auto">
          <motion.h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-6" variants={itemVariants}>
            พร้อมที่จะเริ่มต้นการเรียนรู้แบบใหม่แล้วหรือยัง?
          </motion.h2>
          <motion.p className="text-lg md:text-xl text-gray-600 mb-12 max-w-3xl mx-auto" variants={itemVariants}>
            เข้าร่วมกับนักเรียนหลายพันคนที่ใช้ AI Learning เพื่อพัฒนาทักษะการเรียนรู้ และเพิ่มประสิทธิภาพในการศึกษา
          </motion.p>
          <motion.div variants={itemVariants}>
            <Link href="/register">
              <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                <Button
                  size="lg"
                  className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-12 py-4 text-lg border-0"
                >
                  สมัครสมาชิกฟรี
                  <Sparkles className="ml-2 h-5 w-5" />
                </Button>
              </motion.div>
            </Link>
          </motion.div>
        </motion.div>
      </motion.section>

      {/* Modern Footer */}
      <ModernFooter />
    </div>
  )
}
