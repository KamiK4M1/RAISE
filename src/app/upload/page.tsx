"use client"

import type React from "react"

import { useState, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Brain, Upload, FileText, CheckCircle, AlertCircle, ArrowLeft } from "lucide-react"
import Link from "next/link"
import { apiService } from "@/lib/api"
import { useAsyncApi } from "@/hooks/useApi"

export default function UploadPage() {
  const [files, setFiles] = useState<File[]>([])
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadedFiles, setUploadedFiles] = useState<{ name: string; status: "processing" | "completed" | "error" }[]>(
    [],
  )

  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    const droppedFiles = Array.from(e.dataTransfer.files)
    const validFiles = droppedFiles.filter((file) =>
      [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
      ].includes(file.type),
    )
    setFiles((prev) => [...prev, ...validFiles])
  }, [])

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
  }, [])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files)
      setFiles((prev) => [...prev, ...selectedFiles])
    }
  }

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index))
  }

  const handleUpload = async () => {
    if (files.length === 0) return

    setUploading(true)
    setUploadProgress(0)

    try {
      for (let i = 0; i < files.length; i++) {
        const file = files[i]
        
        // Update UI to show processing
        setUploadedFiles((prev) => [...prev, { name: file.name, status: "processing" }])

        try {
          // Upload to backend
          const response = await apiService.uploadDocument(file)
          
          if (response.success) {
            // Update progress
            setUploadProgress(((i + 1) / files.length) * 100)
            
            // Update status to completed
            setUploadedFiles((prev) => 
              prev.map((f) => 
                f.name === file.name ? { ...f, status: "completed" } : f
              )
            )
            
            console.log(`Successfully uploaded: ${file.name}`, response.data)
          } else {
            throw new Error(response.message || 'Upload failed')
          }
        } catch (error) {
          console.error(`Upload error for ${file.name}:`, error)
          
          // Update status to error
          setUploadedFiles((prev) => 
            prev.map((f) => 
              f.name === file.name ? { ...f, status: "error" } : f
            )
          )
        }
      }
    } catch (error) {
      console.error('Upload process error:', error)
    } finally {
      setUploading(false)
      setFiles([])
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
      {/* Navigation */}
      <nav className="bg-white border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Link href="/dashboard">
              <Button variant="ghost" size="sm" className="text-gray-600 hover:text-gray-900">
                <ArrowLeft className="h-4 w-4 mr-2" />
                กลับ
              </Button>
            </Link>
            <div className="flex items-center space-x-2">
              <Brain className="h-8 w-8 text-blue-600" />
              <span className="text-2xl font-bold text-gray-900">AI Learning</span>
            </div>
          </div>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">อัปโหลดเอกสาร</h1>
            <p className="text-gray-600">อัปโหลดเอกสารการเรียนรู้เพื่อให้ AI สร้างแฟลชการ์ด แบบทดสอบ และเครื่องมือการเรียนรู้อื่นๆ</p>
          </div>

          <div className="grid lg:grid-cols-2 gap-8">
            {/* Upload Area */}
            <div className="space-y-6">
              <Card className="border-0 shadow-sm">
                <CardHeader>
                  <CardTitle>เลือกไฟล์</CardTitle>
                  <CardDescription>รองรับไฟล์ PDF, DOCX, TXT ขนาดไม่เกิน 20 MB</CardDescription>
                </CardHeader>
                <CardContent>
                  <div
                    className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors"
                    onDrop={handleDrop}
                    onDragOver={handleDragOver}
                  >
                    <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-lg font-medium text-gray-900 mb-2">ลากไฟล์มาวางที่นี่</p>
                    <p className="text-gray-600 mb-4">หรือ</p>
                    <label htmlFor="file-upload">
                      <Button variant="outline" className="bg-white text-gray-700 border-gray-300 hover:bg-gray-50">
                        เลือกไฟล์
                      </Button>
                      <input
                        id="file-upload"
                        type="file"
                        multiple
                        accept=".pdf,.docx,.txt"
                        onChange={handleFileSelect}
                        className="hidden"
                      />
                    </label>
                  </div>
                </CardContent>
              </Card>

              {/* Selected Files */}
              {files.length > 0 && (
                <Card className="border-0 shadow-sm">
                  <CardHeader>
                    <CardTitle>ไฟล์ที่เลือก ({files.length})</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {files.map((file, index) => (
                        <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
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
                            onClick={() => removeFile(index)}
                            className="text-red-600 hover:text-red-700 hover:bg-red-50"
                          >
                            ลบ
                          </Button>
                        </div>
                      ))}
                    </div>

                    <div className="mt-6">
                      <Button
                        onClick={handleUpload}
                        disabled={uploading}
                        className="w-full bg-blue-600 hover:bg-blue-700"
                      >
                        {uploading ? "กำลังอัปโหลด..." : "อัปโหลดไฟล์"}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Upload Progress */}
              {uploading && (
                <Card className="border-0 shadow-sm">
                  <CardHeader>
                    <CardTitle>กำลังประมวลผล</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <Progress value={uploadProgress} className="h-2" />
                      <p className="text-sm text-gray-600 text-center">{Math.round(uploadProgress)}% เสร็จสิ้น</p>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>

            {/* Instructions & Status */}
            <div className="space-y-6">
              <Card className="border-0 shadow-sm">
                <CardHeader>
                  <CardTitle>วิธีการใช้งาน</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-start space-x-3">
                      <div className="w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold">
                        1
                      </div>
                      <div>
                        <h4 className="font-medium">อัปโหลดเอกสาร</h4>
                        <p className="text-sm text-gray-600">เลือกไฟล์เอกสารที่ต้องการเรียนรู้</p>
                      </div>
                    </div>
                    <div className="flex items-start space-x-3">
                      <div className="w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold">
                        2
                      </div>
                      <div>
                        <h4 className="font-medium">ประมวลผลด้วย AI</h4>
                        <p className="text-sm text-gray-600">ระบบจะวิเคราะห์เนื้อหาและสร้างเครื่องมือการเรียนรู้</p>
                      </div>
                    </div>
                    <div className="flex items-start space-x-3">
                      <div className="w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold">
                        3
                      </div>
                      <div>
                        <h4 className="font-medium">เริ่มเรียนรู้</h4>
                        <p className="text-sm text-gray-600">ใช้แฟลชการ์ด แบบทดสอบ และระบบถาม-ตอบ</p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Upload History */}
              {uploadedFiles.length > 0 && (
                <Card className="border-0 shadow-sm">
                  <CardHeader>
                    <CardTitle>สถานะการประมวลผล</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {uploadedFiles.map((file, index) => (
                        <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                          <div className="flex items-center space-x-3">
                            <FileText className="h-5 w-5 text-blue-600" />
                            <span className="font-medium text-gray-900">{file.name}</span>
                          </div>
                          <div className="flex items-center space-x-2">
                            {file.status === "processing" && (
                              <>
                                <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse"></div>
                                <span className="text-sm text-yellow-600">กำลังประมวลผล</span>
                              </>
                            )}
                            {file.status === "completed" && (
                              <>
                                <CheckCircle className="h-4 w-4 text-green-600" />
                                <span className="text-sm text-green-600">เสร็จสิ้น</span>
                              </>
                            )}
                            {file.status === "error" && (
                              <>
                                <AlertCircle className="h-4 w-4 text-red-600" />
                                <span className="text-sm text-red-600">เกิดข้อผิดพลาด</span>
                              </>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Tips */}
              <Card className="border-0 shadow-sm bg-blue-50">
                <CardHeader>
                  <CardTitle className="text-blue-900">เคล็ดลับ</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2 text-sm text-blue-800">
                    <li>• ไฟล์ที่มีเนื้อหาชัดเจนจะให้ผลลัพธ์ที่ดีกว่า</li>
                    <li>• หลีกเลี่ยงไฟล์ที่มีรูปภาพหรือตารางซับซ้อน</li>
                    <li>• แบ่งเอกสารยาวเป็นหลายไฟล์เพื่อประสิทธิภาพที่ดีขึ้น</li>
                    <li>• ตรวจสอบให้แน่ใจว่าข้อความในไฟล์อ่านได้ชัดเจน</li>
                  </ul>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
