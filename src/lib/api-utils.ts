import { NextResponse } from "next/server"

export interface ApiError {
  message: string
  code?: string
  statusCode: number
}

export class ApiException extends Error {
  public statusCode: number
  public code?: string

  constructor(message: string, statusCode: number = 500, code?: string) {
    super(message)
    this.name = "ApiException"
    this.statusCode = statusCode
    this.code = code
  }
}

export function createErrorResponse(error: unknown): NextResponse {
  console.error("API Error:", error)

  if (error instanceof ApiException) {
    return NextResponse.json(
      {
        error: error instanceof Error ? error.message : String(error),
        code: error.code,
      },
      { status: error.statusCode }
    )
  }

  if (error instanceof Error) {
    // Handle specific MongoDB errors
    if (error.message.includes("E11000")) {
      return NextResponse.json(
        { error: "ข้อมูลซ้ำในระบบ" },
        { status: 409 }
      )
    }

    // Handle validation errors
    if (error.message.includes("ValidationError")) {
      return NextResponse.json(
        { error: "ข้อมูลไม่ถูกต้อง" },
        { status: 400 }
      )
    }
  }

  // Generic error response
  return NextResponse.json(
    { error: "เกิดข้อผิดพลาดภายในเซิร์ฟเวอร์" },
    { status: 500 }
  )
}

export function createSuccessResponse(data: unknown, status: number = 200): NextResponse {
  return NextResponse.json(data, { status })
}

// Rate limiting helper (for future implementation)
export interface RateLimitResult {
  success: boolean
  limit: number
  remaining: number
  reset: number
}

export async function checkRateLimit(
  identifier: string,
  limit: number = 10,
  windowMs: number = 60000
): Promise<RateLimitResult> {
  // Implementation would depend on your rate limiting strategy
  // Could use Redis, MongoDB, or in-memory store
  return {
    success: true,
    limit,
    remaining: limit - 1,
    reset: Date.now() + windowMs,
  }
}

// Validation helpers
export const validators = {
  email: (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(email)
  },

  password: (password: string): string | null => {
    if (password.length < 6) {
      return "รหัสผ่านต้องมีอย่างน้อย 6 ตัวอักษร"
    }
    if (password.length > 128) {
      return "รหัสผ่านยาวเกินไป"
    }
    if (!/(?=.*[a-zA-Z])/.test(password)) {
      return "รหัสผ่านต้องมีตัวอักษรอย่างน้อย 1 ตัว"
    }
    return null
  },

  name: (name: string): string | null => {
    if (name.trim().length < 2) {
      return "ชื่อต้องมีอย่างน้อย 2 ตัวอักษร"
    }
    if (name.trim().length > 50) {
      return "ชื่อยาวเกินไป"
    }
    return null
  },
}

// Database connection helper
export async function withDatabase<T>(
  operation: (db: unknown) => Promise<T>
): Promise<T> {
  const { MongoClient } = await import("mongodb")
  const client = new MongoClient(process.env.MONGODB_URI!)
  
  try {
    await client.connect()
    const db = client.db()
    return await operation(db)
  } finally {
    await client.close()
  }
}