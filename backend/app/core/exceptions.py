from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class RAISEException(Exception):
    """Base exception for RAISE application"""
    def __init__(self, message: str, code: str = "RAISE_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)

class DocumentProcessingError(RAISEException):
    """Exception raised when document processing fails"""
    def __init__(self, message: str = "เกิดข้อผิดพลาดในการประมวลผลเอกสาร"):
        super().__init__(message, "DOCUMENT_PROCESSING_ERROR")

class EmbeddingError(RAISEException):
    """Exception raised when embedding generation fails"""
    def __init__(self, message: str = "เกิดข้อผิดพลาดในการสร้าง embedding"):
        super().__init__(message, "EMBEDDING_ERROR")

class ModelError(RAISEException):
    """Exception raised when AI model requests fail"""
    def __init__(self, message: str = "เกิดข้อผิดพลาดในการเรียกใช้โมเดล AI"):
        super().__init__(message, "MODEL_ERROR")

class DatabaseError(RAISEException):
    """Exception raised for database operations"""
    def __init__(self, message: str = "เกิดข้อผิดพลาดในการเชื่อมต่อฐานข้อมูล"):
        super().__init__(message, "DATABASE_ERROR")

class FileUploadError(RAISEException):
    """Exception raised for file upload issues"""
    def __init__(self, message: str = "เกิดข้อผิดพลาดในการอัปโหลดไฟล์"):
        super().__init__(message, "FILE_UPLOAD_ERROR")

class AuthenticationError(RAISEException):
    """Exception raised for authentication issues"""
    def __init__(self, message: str = "การรับรองตัวตนไม่สำเร็จ"):
        super().__init__(message, "AUTHENTICATION_ERROR")

class ValidationError(RAISEException):
    """Exception raised for validation errors"""
    def __init__(self, message: str = "ข้อมูลไม่ถูกต้อง"):
        super().__init__(message, "VALIDATION_ERROR")

class UserNotFoundError(RAISEException):
    """Exception raised when user is not found"""
    def __init__(self, message: str = "ไม่พบผู้ใช้งาน"):
        super().__init__(message, "USER_NOT_FOUND")

class UserAlreadyExistsError(RAISEException):
    """Exception raised when user already exists"""
    def __init__(self, message: str = "ผู้ใช้งานนี้มีอยู่ในระบบแล้ว"):
        super().__init__(message, "USER_ALREADY_EXISTS")

class InvalidCredentialsError(RAISEException):
    """Exception raised for invalid login credentials"""
    def __init__(self, message: str = "อีเมลหรือรหัสผ่านไม่ถูกต้อง"):
        super().__init__(message, "INVALID_CREDENTIALS")

class TokenExpiredError(RAISEException):
    """Exception raised when JWT token is expired"""
    def __init__(self, message: str = "Token หมดอายุแล้ว"):
        super().__init__(message, "TOKEN_EXPIRED")

class InsufficientPermissionsError(RAISEException):
    """Exception raised when user lacks required permissions"""
    def __init__(self, message: str = "ไม่มีสิทธิ์เข้าถึงข้อมูลนี้"):
        super().__init__(message, "INSUFFICIENT_PERMISSIONS")

class RateLimitExceededError(RAISEException):
    """Exception raised when rate limit is exceeded"""
    def __init__(self, message: str = "คำขอเกินขีดจำกัดที่อนุญาต"):
        super().__init__(message, "RATE_LIMIT_EXCEEDED")

class RAGError(RAISEException):
    """Exception raised for RAG system errors"""
    def __init__(self, message: str = "เกิดข้อผิดพลาดในระบบ RAG"):
        super().__init__(message, "RAG_ERROR")

class DocumentNotFoundError(RAISEException):
    """Exception raised when document is not found"""
    def __init__(self, message: str = "ไม่พบเอกสาร"):
        super().__init__(message, "DOCUMENT_NOT_FOUND")

class FlashcardNotFoundError(RAISEException):
    """Exception raised when flashcard is not found"""
    def __init__(self, message: str = "ไม่พบการ์ดคำศัพท์"):
        super().__init__(message, "FLASHCARD_NOT_FOUND")

class QuizNotFoundError(RAISEException):
    """Exception raised when quiz is not found"""
    def __init__(self, message: str = "ไม่พบแบบทดสอบ"):
        super().__init__(message, "QUIZ_NOT_FOUND")

class VectorStoreError(RAISEException):
    """Exception raised for vector store operations"""
    def __init__(self, message: str = "เกิดข้อผิดพลาดในระบบจัดเก็บเวกเตอร์"):
        super().__init__(message, "VECTOR_STORE_ERROR")

def create_error_response(code: str, message: str, details: str = None):
    """Create standardized error response"""
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

async def raise_exception_handler(request: Request, exc: RAISEException):
    """Handle custom RAISE exceptions"""
    logger.error(f"RAISE Exception: {exc.code} - {exc.message}")
    return JSONResponse(
        status_code=400,
        content=create_error_response(exc.code, exc.message)
    )

async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions"""
    logger.error(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    
    # Map common HTTP status codes to Thai messages
    thai_messages = {
        400: "คำขอไม่ถูกต้อง",
        401: "ไม่ได้รับอนุญาต",
        403: "ไม่มีสิทธิ์เข้าถึง",
        404: "ไม่พบข้อมูลที่ร้องขอ",
        422: "ข้อมูลไม่ถูกต้อง",
        500: "เกิดข้อผิดพลาดภายในเซิร์ฟเวอร์"
    }
    
    message = thai_messages.get(exc.status_code, "เกิดข้อผิดพลาด")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(f"HTTP_{exc.status_code}", message, str(exc.detail))
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation exceptions"""
    logger.error(f"Validation Exception: {exc.errors()}")
    
    details = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        details.append(f"{field}: {error['msg']}")
    
    return JSONResponse(
        status_code=422,
        content=create_error_response(
            "VALIDATION_ERROR",
            "ข้อมูลที่ส่งมาไม่ถูกต้อง",
            "; ".join(details)
        )
    )

async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected Exception: {type(exc).__name__} - {str(exc)}")
    
    return JSONResponse(
        status_code=500,
        content=create_error_response(
            "INTERNAL_SERVER_ERROR",
            "เกิดข้อผิดพลาดภายในเซิร์ฟเวอร์",
            "กรุณาลองใหม่อีกครั้ง หากปัญหายังคงอยู่ กรุณาติดต่อผู้ดูแลระบบ"
        )
    )

def setup_exception_handlers(app):
    """Setup all exception handlers for the FastAPI app"""
    app.add_exception_handler(RAISEException, raise_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)