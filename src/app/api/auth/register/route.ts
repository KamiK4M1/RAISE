import { type NextRequest, NextResponse } from "next/server"
import { MongoClient } from "mongodb"
import bcrypt from "bcryptjs"

const client = new MongoClient(process.env.MONGODB_URI!)

// Validation helper
function validateEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

function validatePassword(password: string): string | null {
  if (password.length < 6) {
    return "รหัสผ่านต้องมีอย่างน้อย 6 ตัวอักษร"
  }
  if (password.length > 128) {
    return "รหัสผ่านยาวเกินไป"
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
    const existingUser = await users.findOne({ 
      email: email.toLowerCase() 
    })
    
    if (existingUser) {
      return NextResponse.json(
        { error: "อีเมลนี้ถูกใช้งานแล้ว" },
        { status: 409 }
      )
    }

    // Hash password
    const saltRounds = 12
    const hashedPassword = await bcrypt.hash(password, saltRounds)

    // Create user
    const result = await users.insertOne({
      name: name.trim(),
      email: email.toLowerCase(),
      password: hashedPassword,
      createdAt: new Date(),
      updatedAt: new Date(),
      emailVerified: null, // For future email verification
      role: "user"
    })

    // Remove password from response
    return NextResponse.json(
      { 
        message: "สมัครสมาชิกสำเร็จ",
        user: {
          id: result.insertedId,
          name: name.trim(),
          email: email.toLowerCase()
        }
      },
      { status: 201 }
    )

  } catch (error) {
    console.error("Registration error:", error)
    
    // Handle MongoDB duplicate key error
    if (error instanceof Error && error.message.includes("E11000")) {
      return NextResponse.json(
        { error: "อีเมลนี้ถูกใช้งานแล้ว" },
        { status: 409 }
      )
    }

    return NextResponse.json(
      { error: "เกิดข้อผิดพลาดภายในเซิร์ฟเวอร์" },
      { status: 500 }
    )
  } finally {
    await client.close()
  }
}