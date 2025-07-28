"use client"
import { motion, easeInOut } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Upload, Brain, MessageSquare, BarChart3, BookOpen, Zap, Target, Sparkles, FileText, X } from "lucide-react"
import Link from "next/link"
import { useState } from "react"

type Language = 'th' | 'en'

export default function HomePage() {
  const [showTerms, setShowTerms] = useState(false)
  const [language, setLanguage] = useState<Language>('th')
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

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

  const floatingAnimation = {
    y: [-10, 10, -10],
    transition: {
      duration: 3,
      repeat: Infinity,
      ease: easeInOut,
    },
  }

  const termsContent: Record<Language, { title: string; content: string }> = {
    th: {
      title: "ข้อตกลงในการใช้ซอฟต์แวร์",
      content: `ซอฟต์แวร์นี้เป็นผลงานที่พัฒนาขึ้นโดย นายชิติพัทธ์ สร้อยสังวาลย์ จาก โรงเรียนสตรีวิทยา ๒ ในพระราชูปถัมภ์สมเด็จพระศรีนครินทราบรมราชชนนี ภายใต้การดูแลของ อาจารย์ที่ปรึกษา นายวรพันธ์ เรืองโอชา ภายใต้โครงการ เว็บแอปพลิเคชันปัญญาประดิษฐ์สำหรับส่งเสริมการเรียนรู้ด้วยตนเอง (Self-Learning) ผ่านเทคโนโลยี RAG (Retrieval-Augmented Generation) ซึ่งสนับสนุนโดย สำนักงานพัฒนาวิทยาศาสตร์และเทคโนโลยีแห่งชาติโดยมี วัตถุประสงค์เพื่อส่งเสริมให้นักเรียนและนักศึกษาได้เรียนรู้และฝึกทักษะในการพัฒนา ซอฟต์แวร์ลิขสิทธิ์ของซอฟต์แวร์นี้จึงเปน็ ของผู้พัฒนา ซึ่งผู้พัฒนาได้อนุญาตให้สำนักงาน พัฒนาวิทยาศาสตร์และเทคโนโลยีแห่งชาติเผยแพร่ซอฟต์แวร์นี้ตาม "ต้นฉบับ" โดยไม่มี การแก้ไขดัดแปลงใด ๆ ท้ังสิ้น ให้แก่บุคคลทั่วไปได้ใช้เพื่อประโยชน์ส่วนบุคคลหรือ ประโยชน์ทางการศึกษาที่ไม่มีวัตถุประสงค์ในเชิงพาณิชย์โดยไม่คิดค่าตอบแทนการใช้ ซอฟต์แวร์ดังน้ัน สำนักงานพัฒนาวิทยาศาสตร์และเทคโนโลยีแห่งชาติจึงไม่มีหน้าที่ใน การดูแล บำรุงรักษา จัดการอบรมการใช้งาน หรือพัฒนาประสิทธิภาพซอฟต์แวร์ รวมทั้ง ไม่รับรองความถูกต้องหรือประสิทธิภาพการท างานของซอฟต์แวร์ ตลอดจนไม่รับประกัน ความเสียหายต่าง ๆ อันเกิดจากการใช้ซอฟต์แวร์นี้ท้ังสิ้น`
    },
    en: {
      title: "License Agreement",
      content: `This software is a work developed by Shitiphat Soysangwarn from Satriwitthaya 2 School under the provision of Worapun Ruabgocha under AI Web Application for Enhancing Self-Learning through Retrieval-Augmented Generation (RAG) Technology, which has been supported by the National Science and Technology Development Agency (NSTDA), in order to encourage pupils and students to learn and practice their skills in developing software. Therefore, the intellectual property of this software shall belong to the developer and the developer gives NSTDA a permission to distribute this software as an "as is" and non-modified software for a temporary and non-exclusive use without remuneration to anyone for his or her own purpose or academic purpose, which are not commercial purposes. In this connection, NSTDA shall not be responsible to the user for taking care, maintaining, training, or developing the efficiency of this software. Moreover, NSTDA shall not be liable for any error, software efficiency and damages in connection with or arising out of the use of the software.`
    }
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
        <div className="container mx-auto px-4 py-3 sm:py-4">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <motion.div className="flex items-center space-x-2" whileHover={{ scale: 1.05 }}>
              <motion.div whileHover={{ rotate: 360 }} transition={{ duration: 0.5 }}>
                <Brain className="h-6 w-6 sm:h-8 sm:w-8 text-blue-600" />
              </motion.div>
              <span className="text-xl sm:text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                RAISE
              </span>
            </motion.div>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center space-x-3 lg:space-x-4">
              <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                <Button 
                  variant="outline" 
                  size="sm"
                  className="bg-white text-gray-700 border-gray-300 hover:bg-gray-50 text-xs lg:text-sm"
                  onClick={() => setShowTerms(true)}
                >
                  <FileText className="h-3 w-3 lg:h-4 lg:w-4 mr-1 lg:mr-2" />
                  <span className="hidden lg:inline">ข้อตกลงการใช้งาน</span>
                  <span className="lg:hidden">ข้อตกลง</span>
                </Button>
              </motion.div>
              <Link href="/login">
                <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                  <Button variant="outline" size="sm" className="bg-white text-gray-700 border-gray-300 hover:bg-gray-50 text-xs lg:text-sm">
                    เข้าสู่ระบบ
                  </Button>
                </motion.div>
              </Link>
              <Link href="/register">
                <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                  <Button size="sm" className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white border-0 text-xs lg:text-sm">
                    สมัครสมาชิก
                  </Button>
                </motion.div>
              </Link>
            </div>

            {/* Mobile Menu Button */}
            <motion.button
              className="md:hidden p-2 rounded-lg hover:bg-gray-100 relative"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              whileTap={{ scale: 0.95 }}
            >
              <motion.div
                animate={mobileMenuOpen ? "open" : "closed"}
                className="w-6 h-6 flex flex-col justify-center items-center"
              >
                <motion.span
                  className="w-6 h-0.5 bg-gray-600 block absolute"
                  variants={{
                    closed: { rotate: 0, y: -2 },
                    open: { rotate: 45, y: 0 }
                  }}
                  transition={{ duration: 0.3 }}
                />
                <motion.span
                  className="w-6 h-0.5 bg-gray-600 block absolute"
                  variants={{
                    closed: { opacity: 1 },
                    open: { opacity: 0 }
                  }}
                  transition={{ duration: 0.3 }}
                />
                <motion.span
                  className="w-6 h-0.5 bg-gray-600 block absolute"
                  variants={{
                    closed: { rotate: 0, y: 2 },
                    open: { rotate: -45, y: 0 }
                  }}
                  transition={{ duration: 0.3 }}
                />
              </motion.div>
            </motion.button>
          </div>

          {/* Mobile Navigation Menu */}
          {mobileMenuOpen && (
            <motion.div
              className="md:hidden mt-4 pb-4 border-t pt-4 overflow-hidden"
              initial={{ opacity: 0, height: 0, y: -20 }}
              animate={{ opacity: 1, height: "auto", y: 0 }}
              exit={{ opacity: 0, height: 0, y: -20 }}
              transition={{ duration: 0.3, ease: "easeInOut" }}
            >
              <motion.div 
                className="flex flex-col space-y-3"
                initial="closed"
                animate="open"
                variants={{
                  open: {
                    transition: {
                      staggerChildren: 0.1,
                      delayChildren: 0.1
                    }
                  },
                  closed: {
                    transition: {
                      staggerChildren: 0.05,
                      staggerDirection: -1
                    }
                  }
                }}
              >
                <motion.div
                  variants={{
                    open: { opacity: 1, x: 0 },
                    closed: { opacity: 0, x: -20 }
                  }}
                  transition={{ duration: 0.3 }}
                >
                  <Button 
                    variant="outline" 
                    size="sm"
                    className="bg-white text-gray-700 border-gray-300 hover:bg-gray-50 justify-start w-full"
                    onClick={() => {
                      setShowTerms(true)
                      setMobileMenuOpen(false)
                    }}
                  >
                    <FileText className="h-4 w-4 mr-2" />
                    ข้อตกลงการใช้งาน
                  </Button>
                </motion.div>
                <motion.div
                  variants={{
                    open: { opacity: 1, x: 0 },
                    closed: { opacity: 0, x: -20 }
                  }}
                  transition={{ duration: 0.3 }}
                >
                  <Link href="/login">
                    <Button variant="outline" size="sm" className="bg-white text-gray-700 border-gray-300 hover:bg-gray-50 w-full justify-start">
                      เข้าสู่ระบบ
                    </Button>
                  </Link>
                </motion.div>
                <motion.div
                  variants={{
                    open: { opacity: 1, x: 0 },
                    closed: { opacity: 0, x: -20 }
                  }}
                  transition={{ duration: 0.3 }}
                >
                  <Link href="/register">
                    <Button size="sm" className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white border-0 w-full justify-start">
                      สมัครสมาชิก
                    </Button>
                  </Link>
                </motion.div>
              </motion.div>
            </motion.div>
          )}
        </div>
      </motion.nav>

      {/* Terms of Service Modal */}
      {showTerms && (
        <motion.div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <motion.div
            className="bg-white rounded-2xl max-w-4xl max-h-[90vh] sm:max-h-[80vh] w-full overflow-hidden shadow-2xl"
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between p-4 sm:p-6 border-b">
              <h2 className="text-lg sm:text-2xl font-bold text-gray-900 pr-4">
                {termsContent[language].title}
              </h2>
              <div className="flex items-center space-x-2 sm:space-x-4 flex-shrink-0">
                {/* Language Toggle */}
                <div className="flex items-center space-x-1 sm:space-x-2 bg-gray-100 p-1 rounded-lg">
                  <button
                    onClick={() => setLanguage('th')}
                    className={`px-2 sm:px-3 py-1 rounded-md text-xs sm:text-sm font-medium transition-colors ${
                      language === 'th' 
                        ? 'bg-blue-600 text-white' 
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    TH
                  </button>
                  <button
                    onClick={() => setLanguage('en')}
                    className={`px-2 sm:px-3 py-1 rounded-md text-xs sm:text-sm font-medium transition-colors ${
                      language === 'en' 
                        ? 'bg-blue-600 text-white' 
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    EN
                  </button>
                </div>
                {/* Close Button */}
                <button
                  onClick={() => setShowTerms(false)}
                  className="p-1 sm:p-2 hover:bg-gray-100 rounded-full transition-colors"
                >
                  <X className="h-4 w-4 sm:h-5 sm:w-5 text-gray-500" />
                </button>
              </div>
            </div>

            {/* Modal Content */}
            <div className="p-4 sm:p-6 overflow-y-auto max-h-[50vh] sm:max-h-[60vh]">
              <div className="prose prose-gray max-w-none prose-sm sm:prose-base">
                <p className="text-gray-700 leading-relaxed whitespace-pre-wrap text-sm sm:text-base">
                  {termsContent[language].content}
                </p>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="flex justify-end p-4 sm:p-6 border-t bg-gray-50">
              <Button
                onClick={() => setShowTerms(false)}
                size="sm"
                className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white"
              >
                ปิด
              </Button>
            </div>
          </motion.div>
        </motion.div>
      )}

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-8 sm:py-12 lg:py-16 xl:py-24 text-center relative">
        {/* Floating Elements - Hidden on mobile for performance */}
        <motion.div
          className="hidden sm:block absolute top-20 left-10 w-12 h-12 lg:w-20 lg:h-20 bg-blue-200 rounded-full opacity-20"
          animate={floatingAnimation}
        />
        <motion.div
          className="hidden sm:block absolute top-40 right-20 w-10 h-10 lg:w-16 lg:h-16 bg-purple-200 rounded-full opacity-20"
          animate={{
            ...floatingAnimation,
            transition: { ...floatingAnimation.transition, delay: 1 }
          }}
        />
        <motion.div
          className="hidden sm:block absolute bottom-20 left-1/4 w-8 h-8 lg:w-12 lg:h-12 bg-green-200 rounded-full opacity-20"
          animate={{
            ...floatingAnimation,
            transition: { ...floatingAnimation.transition, delay: 2 }
          }}
        />

        <motion.div className="max-w-5xl mx-auto" initial="hidden" animate="visible" variants={containerVariants}>
          <motion.div
            className="inline-flex items-center space-x-2 bg-gradient-to-r from-blue-100 to-purple-100 px-3 py-2 sm:px-4 rounded-full mb-6 sm:mb-8"
            variants={itemVariants}
          >
            <Sparkles className="h-3 w-3 sm:h-4 sm:w-4 text-blue-600" />
            <span className="text-xs sm:text-sm font-medium text-gray-700">ขับเคลื่อนด้วย AI</span>
          </motion.div>

          <motion.h1
            className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl xl:text-7xl font-bold text-gray-900 mb-4 sm:mb-6 leading-tight"
            variants={itemVariants}
          >
            ยกระดับการเรียนรู้
            <br />
            <span className="bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
              ด้วย RAISE
            </span>
          </motion.h1>

          <motion.p
            className="text-base sm:text-lg md:text-xl lg:text-2xl text-gray-600 mb-8 sm:mb-12 leading-relaxed max-w-4xl mx-auto px-2"
            variants={itemVariants}
          >
            แพลตฟอร์มการเรียนรู้อัจฉริยะที่ใช้เทคโนโลยี RAG และ AI เพื่อสร้างแฟลชการ์ด แบบทดสอบ และระบบถาม-ตอบ
            ที่ปรับเปลี่ยนตามสไตล์การเรียนรู้ของคุณ
          </motion.p>

          <motion.div className="flex flex-col sm:flex-row gap-4 justify-center items-center" variants={itemVariants}>
            <Link href="/register">
              <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                <Button
                  size="lg"
                  className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-6 sm:px-8 py-3 sm:py-4 text-base sm:text-lg border-0 w-full sm:w-auto"
                >
                  เริ่มต้นใช้งานฟรี
                  <Sparkles className="ml-2 h-4 w-4 sm:h-5 sm:w-5" />
                </Button>
              </motion.div>
            </Link>
          </motion.div>
        </motion.div>
      </section>

      {/* Features Section */}
      <section className="container mx-auto px-4 py-12 sm:py-16 lg:py-24">
        <motion.div
          className="text-center mb-12 sm:mb-16"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={containerVariants}
        >
          <motion.h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-gray-900 mb-3 sm:mb-4" variants={itemVariants}>
            คุณสมบัติเด่นของ RAISE
          </motion.h2>
          <motion.p className="text-base sm:text-lg md:text-xl text-gray-600 max-w-3xl mx-auto px-2" variants={itemVariants}>
            เครื่องมือการเรียนรู้ครบครันที่ออกแบบมาเพื่อเพิ่มประสิทธิภาพการศึกษา
          </motion.p>
        </motion.div>

        <motion.div
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8"
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
              whileHover={{ scale: 1.02, y: -5 }}
              transition={{ duration: 0.2 }}
              className="h-full"
            >
              <Card
                className={`border-0 shadow-lg hover:shadow-xl transition-all duration-300 ${feature.bgColor} h-full`}
              >
                <CardHeader className="text-center p-6 sm:p-8">
                  <motion.div
                    className={`w-12 h-12 sm:w-16 sm:h-16 rounded-2xl bg-gradient-to-r ${feature.color} flex items-center justify-center mx-auto mb-4 sm:mb-6`}
                    whileHover={{ rotate: [-10, 10, -10] }}
                    transition={{ duration: 0.5, repeat: Number.POSITIVE_INFINITY }}
                  >
                    <feature.icon className="h-6 w-6 sm:h-8 sm:w-8 text-white" />
                  </motion.div>
                  <CardTitle className="text-lg sm:text-xl mb-3 sm:mb-4">{feature.title}</CardTitle>
                  <CardDescription className="text-gray-600 leading-relaxed text-sm sm:text-base">{feature.description}</CardDescription>
                </CardHeader>
              </Card>
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* CTA Section */}
      <motion.section
        className="container mx-auto px-4 py-12 sm:py-16 lg:py-24 pb-16 sm:pb-24 lg:pb-32 text-center"
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
        variants={containerVariants}
      >
        <motion.div className="max-w-4xl mx-auto">
          <motion.h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-gray-900 mb-4 sm:mb-6 px-2" variants={itemVariants}>
            พร้อมที่จะยกระดับการเรียนรู้ด้วย RAISE แล้วหรือยัง?
          </motion.h2>
          <motion.p className="text-base sm:text-lg md:text-xl text-gray-600 mb-8 sm:mb-12 max-w-3xl mx-auto px-2" variants={itemVariants}>
            เข้าร่วมกับนักเรียนหลายพันคนที่ใช้ RAISE เพื่อพัฒนาทักษะการเรียนรู้ และเพิ่มประสิทธิภาพในการศึกษา
          </motion.p>
          <motion.div variants={itemVariants}>
            <Link href="/register">
              <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                <Button
                  size="lg"
                  className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-8 sm:px-12 py-3 sm:py-4 text-base sm:text-lg border-0 w-full sm:w-auto"
                >
                  สมัครสมาชิกฟรี
                  <Sparkles className="ml-2 h-4 w-4 sm:h-5 sm:w-5" />
                </Button>
              </motion.div>
            </Link>
          </motion.div>
        </motion.div>
      </motion.section>
    </div>
  )
}