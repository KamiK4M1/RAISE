"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Document } from "@/types/api"
import { apiService } from "@/lib/api"
import { FileText, BrainCircuit, Puzzle, Loader2, AlertCircle, ArrowLeft, Trash2 } from "lucide-react"
import Link from "next/link"

export default function DocumentPage() {
  const params = useParams()
  const router = useRouter()
  const id = params.id as string

  const [document, setDocument] = useState<Document | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)

  useEffect(() => {
    if (id) {
      const fetchDocument = async () => {
        try {
          setLoading(true)
          const response = await apiService.getDocument(id)
          if (response.success && response.data) {
            setDocument(response.data)
          } else {
            throw new Error(response.message || "Failed to fetch document.")
          }
        } catch (err: any) {
          setError(err.message || "An unexpected error occurred.")
        } finally {
          setLoading(false)
        }
      }
      fetchDocument()
    }
  }, [id])

  const handleGenerateFlashcards = () => {
    // Navigate to flashcard generation page with this document pre-selected
    router.push(`/flashcards/generate?document=${id}`)
  }

  const handleStartQuiz = () => {
    // Placeholder for quiz functionality
    alert("Quiz functionality coming soon!")
    // router.push(`/quiz/${id}`)
  }

  const handleDeleteDocument = async () => {
    if (!id) return
    
    if (!confirm('คุณแน่ใจหรือไม่ว่าต้องการลบเอกสารนี้? การกระทำนี้ไม่สามารถยกเลิกได้')) {
      return
    }

    setIsDeleting(true)
    setError(null)
    
    try {
      const response = await apiService.deleteDocument(id)
      if (response.success) {
        router.push('/dashboard')
      } else {
        throw new Error(response.message || 'Failed to delete document')
      }
    } catch (err: any) {
      setError(err.message || 'เกิดข้อผิดพลาดในการลบเอกสาร')
    } finally {
      setIsDeleting(false)
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <Loader2 className="h-16 w-16 animate-spin text-blue-600" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
       <nav className="bg-white border-b">
        <div className="container mx-auto px-4 py-4 flex items-center">
          <Link href="/dashboard">
            <Button variant="ghost" size="sm" className="text-gray-600 hover:text-gray-900">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Dashboard
            </Button>
          </Link>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-8">
        <div className="max-w-3xl mx-auto">
          {error && (
            <Alert variant="destructive" className="mb-6">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {document && (
            <Card>
              <CardHeader>
                <div className="flex items-start space-x-4">
                    <FileText className="h-10 w-10 text-blue-600 mt-1" />
                    <div>
                        <CardTitle className="text-2xl">{document.filename}</CardTitle>
                        <CardDescription>
                            Status: <span className={`font-semibold ${document.processing_status === 'completed' ? 'text-green-600' : 'text-yellow-600'}`}>{document.processing_status}</span>
                        </CardDescription>
                    </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                    <Button 
                        onClick={handleGenerateFlashcards} 
                        disabled={document.processing_status !== 'completed'}
                        size="lg"
                    >
                        <BrainCircuit className="mr-2 h-5 w-5" /> Generate Flashcards
                    </Button>
                    <Button 
                        onClick={handleStartQuiz} 
                        disabled={document.processing_status !== 'completed'}
                        variant="outline"
                        size="lg"
                    >
                        <Puzzle className="mr-2 h-5 w-5" /> Start Quiz
                    </Button>
                </div>
                {document.processing_status !== 'completed' && (
                    <p className="text-sm text-center text-yellow-700 mt-4">Please wait for the document to finish processing before generating study materials.</p>
                )}
                
                {/* Delete Button */}
                <div className="border-t pt-4 mt-6">
                  <Button 
                      onClick={handleDeleteDocument} 
                      disabled={isDeleting}
                      variant="destructive"
                      size="sm"
                      className="w-full"
                  >
                      {isDeleting ? (
                          <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> กำลังลบ...</>
                      ) : (
                          <><Trash2 className="mr-2 h-4 w-4" /> ลบเอกสาร</>
                      )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
