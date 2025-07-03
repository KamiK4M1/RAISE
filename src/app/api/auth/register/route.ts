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

    // Forward registration to backend
    const backendResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ name, email, password }),
    })

    const data = await backendResponse.json()

    if (!backendResponse.ok) {
      return NextResponse.json(
        { error: data.detail || "Registration failed" },
        { status: backendResponse.status }
      )
    }

    return NextResponse.json(data, { status: 201 })
  } catch (error) {
    console.error("Registration error:", error)
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    )
  }
}