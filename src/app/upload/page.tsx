"use client"

import type React from "react"
import { useState, useCallback } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Brain, Upload, FileText, AlertCircle, ArrowLeft, X } from "lucide-react"
import Link from "next/link"
import { apiService } from "@/lib/api"

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()

  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile && ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"].includes(droppedFile.type)) {
      setFile(droppedFile)
      setError(null)
    } else {
      setError("Invalid file type. Please upload a PDF, DOCX, or TXT file.")
    }
  }, [])

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
  }, [])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0]
      if (["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"].includes(selectedFile.type)) {
        setFile(selectedFile)
        setError(null)
      } else {
        setError("Invalid file type. Please upload a PDF, DOCX, or TXT file.")
      }
    }
  }

  const removeFile = () => {
    setFile(null)
  }

  const handleUpload = async () => {
    if (!file) {
      setError("Please select a file to upload.")
      return
    }

    setUploading(true)
    setUploadProgress(0)
    setError(null)

    try {
      // This is a mock progress, in a real app you'd use a library that supports upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev >= 95) {
            clearInterval(progressInterval)
            return 95
          }
          return prev + 5
        })
      }, 200)

      const response = await apiService.uploadDocument(file)
      
      clearInterval(progressInterval)
      setUploadProgress(100)

      if (response.success && response.data) {
        console.log("Upload successful:", response.data)
        router.push(`documents/${response.data.document_id}`)
      } else {
        throw new Error(response.message || 'Upload failed')
      }
    } catch (err: any) {
      console.error("Upload error:", err)
      setError(err.message || "An unexpected error occurred during upload.")
      setUploadProgress(0)
    } finally {
      setUploading(false)
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes"
    const k = 1024
    const sizes = ["Bytes", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Link href="/dashboard">
              <Button variant="ghost" size="sm" className="text-gray-600 hover:text-gray-900">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back
              </Button>
            </Link>
            <div className="flex items-center space-x-2">
              <Brain className="h-8 w-8 text-blue-600" />
              <span className="text-2xl font-bold text-gray-900">RAISE</span>
            </div>
          </div>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-8">
        <div className="max-w-2xl mx-auto">
          <div className="mb-8 text-center">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Upload Document</h1>
            <p className="text-gray-600">Upload a document to let AI create flashcards, quizzes, and more.</p>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Select File</CardTitle>
              <CardDescription>Supports PDF, DOCX, TXT. Max size 20MB.</CardDescription>
            </CardHeader>
            <CardContent>
              <div
                className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors"
                onDrop={handleDrop}
                onDragOver={handleDragOver}
              >
                <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-lg font-medium text-gray-900 mb-2">Drag and drop your file here</p>
                <p className="text-gray-600 mb-4">or</p>
                <label htmlFor="file-upload">
                  <Button asChild variant="outline">
                    <span>Choose File</span>
                  </Button>
                  <input
                    id="file-upload"
                    type="file"
                    accept=".pdf,.docx,.txt"
                    onChange={handleFileSelect}
                    className="hidden"
                    disabled={uploading}
                  />
                </label>
              </div>

              {error && (
                <div className="mt-4 text-red-600 flex items-center justify-center">
                  <AlertCircle className="h-4 w-4 mr-2" />
                  <span>{error}</span>
                </div>
              )}

              {file && !uploading && (
                <div className="mt-6">
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <FileText className="h-5 w-5 text-blue-600" />
                      <div>
                        <p className="font-medium text-gray-900">{file.name}</p>
                        <p className="text-sm text-gray-600">{formatFileSize(file.size)}</p>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={removeFile}
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}

              {uploading && (
                <div className="mt-6">
                  <Progress value={uploadProgress} className="h-2" />
                  <p className="text-sm text-gray-600 text-center mt-2">{Math.round(uploadProgress)}% Complete</p>
                </div>
              )}

              <div className="mt-6">
                <Button
                  onClick={handleUpload}
                  disabled={!file || uploading}
                  className="w-full bg-blue-600 hover:bg-blue-700"
                >
                  {uploading ? "Uploading..." : "Upload and Process"}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}