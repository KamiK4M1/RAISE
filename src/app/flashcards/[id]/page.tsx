"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Flashcard } from "@/types/api"
import { apiService } from "@/lib/api"
import { Loader2, AlertCircle, ArrowLeft, RefreshCw, Lightbulb, Check } from "lucide-react"
import Link from "next/link"

export default function FlashcardPage() {
  const params = useParams()
  const router = useRouter()
  const id = params.id as string

  const [flashcards, setFlashcards] = useState<Flashcard[]>([])
  const [currentCardIndex, setCurrentCardIndex] = useState(0)
  const [isFlipped, setIsFlipped] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (id) {
      fetchReviewSession()
    }
  }, [id])

  const fetchReviewSession = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await apiService.getReviewSession(id, 10) // Fetch 10 cards for the session
      if (response.success && response.data && response.data.cards.length > 0) {
        setFlashcards(response.data.cards)
        setCurrentCardIndex(0)
        setIsFlipped(false)
      } else if (response.data && response.data.cards.length === 0) {
        setError("No flashcards available for this document. Try generating them first.")
      } else {
        throw new Error(response.message || "Failed to fetch review session.")
      }
    } catch (err: any) {
      setError(err.message || "An unexpected error occurred.")
    } finally {
      setLoading(false)
    }
  }

  const handleNextCard = () => {
    if (currentCardIndex < flashcards.length - 1) {
      setCurrentCardIndex(currentCardIndex + 1)
      setIsFlipped(false)
    } else {
      // End of session
      alert("You have completed this session!")
      router.push(`/documents/${id}`)
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <Loader2 className="h-16 w-16 animate-spin text-blue-600" />
      </div>
    )
  }

  const currentCard = flashcards[currentCardIndex]

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
      <nav className="bg-white border-b w-full">
        <div className="container mx-auto px-4 py-3 flex items-center justify-between">
          <Link href={`/documents/${id}`}>
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Document
            </Button>
          </Link>
          <div className="text-sm font-semibold">
            Card {currentCardIndex + 1} of {flashcards.length}
          </div>
          <Button variant="outline" size="sm" onClick={fetchReviewSession}>
            <RefreshCw className="h-4 w-4 mr-2" />
            New Session
          </Button>
        </div>
      </nav>

      <div className="flex-grow flex items-center justify-center p-4">
        <div className="w-full max-w-2xl">
          {error && (
            <Alert variant="destructive" className="mb-6">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {!currentCard && !error && (
              <Card className="text-center">
                  <CardHeader>
                      <CardTitle>All Done!</CardTitle>
                  </CardHeader>
                  <CardContent>
                      <p>You've reviewed all available cards for now.</p>
                      <Button onClick={() => router.push(`/documents/${id}`)} className="mt-4">Back to Document</Button>
                  </CardContent>
              </Card>
          )}

          {currentCard && (
            <Card className="min-h-[300px] flex flex-col shadow-lg">
              <CardContent className="flex-grow flex items-center justify-center p-6 text-center">
                <p className="text-2xl font-medium">
                  {isFlipped ? currentCard.answer : currentCard.question}
                </p>
              </CardContent>
              <div className="p-4 border-t flex flex-col sm:flex-row items-center justify-center gap-4">
                <Button 
                    onClick={() => setIsFlipped(!isFlipped)} 
                    variant="outline" 
                    className="w-full sm:w-auto"
                    disabled={isFlipped}
                >
                  <Lightbulb className="mr-2 h-4 w-4" /> Show Answer
                </Button>
                <Button 
                    onClick={handleNextCard} 
                    className="w-full sm:w-auto bg-green-600 hover:bg-green-700"
                    disabled={!isFlipped}
                >
                  <Check className="mr-2 h-4 w-4" /> Next Card
                </Button>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
