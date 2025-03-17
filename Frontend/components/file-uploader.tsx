"use client"

import type React from "react"
import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Upload, Loader2, AlertCircle } from "lucide-react"
import { useRouter } from "next/navigation"
import { Alert, AlertDescription } from "@/components/ui/alert"

interface FileUploaderProps {
  wallThickness?: string
  wallHeight?: string
  useLLM?: boolean
  visualize?: boolean
  drawingName?: string
  projectId?: string
}

export function FileUploader({
  wallThickness = '8"',
  wallHeight = "8.0",
  useLLM = false,
  visualize = true,
  drawingName = "",
  projectId = "default_project",
}: FileUploaderProps) {
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isLargeImage, setIsLargeImage] = useState(false)
  const [originalFileSize, setOriginalFileSize] = useState<number>(0)
  const [resizedFileSize, setResizedFileSize] = useState<number>(0)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const router = useRouter()
  
  // Maximum image dimension for LLM processing
  const MAX_IMAGE_DIMENSION = 2000

  // Function to resize an image
  const resizeImage = async (imageFile: File, maxDimension: number): Promise<File> => {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => {
        // Check if resizing is needed
        if (img.width <= maxDimension && img.height <= maxDimension) {
          setIsLargeImage(false);
          resolve(imageFile);
          return;
        }
        
        setIsLargeImage(true);
        setOriginalFileSize(imageFile.size);
        
        // Calculate new dimensions while maintaining aspect ratio
        let newWidth, newHeight;
        if (img.width > img.height) {
          newWidth = maxDimension;
          newHeight = Math.floor(img.height * (maxDimension / img.width));
        } else {
          newHeight = maxDimension;
          newWidth = Math.floor(img.width * (maxDimension / img.height));
        }
        
        // Create canvas and resize image
        const canvas = document.createElement('canvas');
        canvas.width = newWidth;
        canvas.height = newHeight;
        const ctx = canvas.getContext('2d');
        if (!ctx) {
          reject(new Error('Failed to get canvas context'));
          return;
        }
        
        ctx.drawImage(img, 0, 0, newWidth, newHeight);
        
        // Convert canvas to Blob
        canvas.toBlob((blob) => {
          if (!blob) {
            reject(new Error('Failed to create blob from canvas'));
            return;
          }
          
          // Create new File from Blob
          const resizedFile = new File([blob], imageFile.name, {
            type: 'image/png',
            lastModified: Date.now()
          });
          
          setResizedFileSize(resizedFile.size);
          resolve(resizedFile);
        }, 'image/png', 0.9);
      };
      
      img.onerror = () => {
        reject(new Error('Failed to load image'));
      };
      
      // Load image from File
      img.src = URL.createObjectURL(imageFile);
    });
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      try {
        // Reset states
        setIsLargeImage(false);
        setError(null);
        
        // Create preview
        const reader = new FileReader()
        reader.onload = () => {
          setPreview(reader.result as string)
        }
        reader.readAsDataURL(selectedFile)
        
        // Resize image if needed
        const resizedFile = await resizeImage(selectedFile, MAX_IMAGE_DIMENSION);
        setFile(resizedFile);
      } catch (err) {
        setError('Error processing image. Please try another file.');
        // Silently handle image processing errors
      }
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const droppedFile = e.dataTransfer.files?.[0]
    if (droppedFile) {
      try {
        // Reset states
        setIsLargeImage(false);
        setError(null);
        
        // Create preview
        const reader = new FileReader()
        reader.onload = () => {
          setPreview(reader.result as string)
        }
        reader.readAsDataURL(droppedFile)
        
        // Resize image if needed
        const resizedFile = await resizeImage(droppedFile, MAX_IMAGE_DIMENSION);
        setFile(resizedFile);
      } catch (err) {
        setError('Error processing image. Please try another file.');
        // Silently handle image processing errors
      }
    }
  }

  const handleClick = () => {
    fileInputRef.current?.click()
  }

  const handleSubmit = async () => {
    if (!file) return

    setIsUploading(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append("file", file)
      formData.append("wallThickness", wallThickness)
      formData.append("wallHeight", wallHeight)
      formData.append("useLLM", String(useLLM))
      formData.append("visualize", String(visualize))
      
      if (drawingName) {
        formData.append("drawingName", drawingName)
      }
      
      if (projectId) {
        formData.append("projectId", projectId)
      }

      const response = await fetch("/api/analyze", {
        method: "POST",
        body: formData,
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || "Failed to analyze foundation plan")
      }

      // Redirect to analysis results page
      router.push(`/analyses/${data.analysisId}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unknown error occurred")
      setIsUploading(false)
    }
  }

  return (
    <div>
      <input type="file" ref={fileInputRef} onChange={handleFileChange} accept="image/*" className="hidden" />
      <div
        className={`flex flex-col items-center justify-center rounded-md border-2 border-dashed p-8 transition-colors ${
          isDragging ? "border-primary bg-secondary/50" : "border-border/60"
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
      >
        {preview ? (
          <div className="flex flex-col items-center">
            <div className="relative mb-4 h-48 w-full overflow-hidden rounded-md">
              <img src={preview || "/placeholder.svg"} alt="Preview" className="h-full w-full object-contain" />
            </div>
            <p className="mb-2 text-sm font-medium">{file?.name}</p>
            {!isUploading && (
              <Button
                variant="outline"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation()
                  setFile(null)
                  setPreview(null)
                }}
                className="text-muted-foreground"
              >
                Remove
              </Button>
            )}
          </div>
        ) : (
          <>
            <Upload className="mb-4 h-12 w-12 text-muted-foreground" />
            <h3 className="mb-2 text-lg font-medium">Upload Foundation Plan</h3>
            <p className="mb-4 text-center text-sm text-muted-foreground">
              Drag and drop or click to upload
              <br />
              Supports PNG, JPG, or PDF
            </p>
            <Button className="notion-button notion-button-primary">Select File</Button>
          </>
        )}
      </div>

      {preview && (
        <Button
          onClick={(e) => {
            e.preventDefault()
            handleSubmit()
          }}
          disabled={isUploading}
          className="mt-4 w-full"
        >
          {isUploading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Analyzing...
            </>
          ) : (
            "Analyze Foundation Plan"
          )}
        </Button>
      )}

      {error && <div className="mt-2 text-red-500 text-sm">{error}</div>}
      
      {isLargeImage && (
        <Alert className="mt-2 border-amber-500">
          <AlertCircle className="h-4 w-4 text-amber-500" />
          <AlertDescription className="text-sm">
            Large image detected ({(originalFileSize / (1024 * 1024)).toFixed(1)} MB). 
            Image has been automatically resized to {MAX_IMAGE_DIMENSION}px for better processing 
            ({(resizedFileSize / (1024 * 1024)).toFixed(1)} MB).
          </AlertDescription>
        </Alert>
      )}
    </div>
  )
}
