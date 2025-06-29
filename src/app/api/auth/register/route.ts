import { type NextRequest, NextResponse } from "next/server"
import { MongoClient } from "mongodb"
import prisma from "@/lib/prisma"
import bcrypt from "bcryptjs"

const client = new MongoClient(process.env.MONGODB_URI!)

// Validation helpers
function validateEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

function validatePassword(password: string): string | null {
  if (password.length < 8) {
    return "รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร"
  }
  if (password.length > 128) {
    return "รหัสผ่านยาวเกินไป"
  }
  
  // Check for uppercase letter
  if (!/[A-Z]/.test(password)) {
    return "รหัสผ่านต้องมีอักษรตัวใหญ่อย่างน้อย 1 ตัว"
  }
  
  // Check for lowercase letter  
  if (!/[a-z]/.test(password)) {
    return "รหัสผ่านต้องมีอักษรตัวเล็กอย่างน้อย 1 ตัว"
  }
  
  // Check for number
  if (!/\d/.test(password)) {
    return "รหัสผ่านต้องมีตัวเลขอย่างน้อย 1 ตัว"
  }
  
  // Check for special character
  if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
    return "รหัสผ่านต้องมีอักขระพิเศษอย่างน้อย 1 ตัว (!@#$%^&*)"
  }
  
  return null
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { name, email, password } = body

    // Validate required fields
    if (!name || !email || !password) {
      return NextResponse.json(
        { error: "กรุณากรอกข้อมูลให้ครบทุกช่อง" },
        { status: 400 }
      )
    }

    // Validate name
    if (name.trim().length < 2) {
      return NextResponse.json(
        { error: "ชื่อต้องมีอย่างน้อย 2 ตัวอักษร" },
        { status: 400 }
      )
    }

    // Validate email
    if (!validateEmail(email)) {
      return NextResponse.json(
        { error: "รูปแบบอีเมลไม่ถูกต้อง" },
        { status: 400 }
      )
    }

    // Validate password
    const passwordError = validatePassword(password)
    if (passwordError) {
      return NextResponse.json(
        { error: passwordError },
        { status: 400 }
      )
    }

    await client.connect()
    const db = client.db()
    const users = db.collection("users")

    // Check if user already exists
    const existingUser = await prisma.user.findUnique({
      where: { email: email.toLowerCase() },
    })
    
    if (existingUser) {
      return NextResponse.json(
        { error: "อีเมลนี้ถูกใช้งานแล้ว" },
        { status: 409 }
      )
    }


    // Hash password
   const hashedPassword = await bcrypt.hash(password, 12)


    // Create user
    const user = await prisma.user.create({
      data: {
        name: name.trim(),
        email: email.toLowerCase(),
        password: hashedPassword,
      },
    })

    const { password: _, ...userWithoutPassword } = user


    // Remove password from response
    return NextResponse.json(
      {
        message: "สมัครสมาชิกสำเร็จ",
        user: userWithoutPassword,
      },
      { status: 201 }
    )
  } catch (error) {
    console.error("Registration error:", error)
    return NextResponse.json(
      { error: "เกิดข้อผิดพลาดภายในเซิร์ฟเวอร์" },
      { status: 500 }
    )
  } finally {
    await client.close()
  }
}