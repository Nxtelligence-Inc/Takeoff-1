"use client"

import { useState, useEffect } from "react"
import { X } from "lucide-react"

interface ImageLightboxProps {
  src: string
  alt: string
  onClose: () => void
}

export function ImageLightbox({ src, alt, onClose }: ImageLightboxProps) {
  // Close on escape key press
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose()
      }
    }
    
    window.addEventListener("keydown", handleEscape)
    
    // Prevent scrolling of the body when lightbox is open
    document.body.style.overflow = "hidden"
    
    return () => {
      window.removeEventListener("keydown", handleEscape)
      document.body.style.overflow = "auto"
    }
  }, [onClose])
  
  // Close when clicking outside the image
  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose()
    }
  }
  
  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80"
      onClick={handleBackdropClick}
    >
      <div className="relative max-h-[90vh] max-w-[90vw]">
        <button 
          className="absolute -right-4 -top-4 rounded-full bg-white p-2 text-black shadow-md hover:bg-gray-200"
          onClick={onClose}
        >
          <X className="h-6 w-6" />
        </button>
        <img 
          src={src} 
          alt={alt} 
          className="max-h-[90vh] max-w-[90vw] object-contain" 
        />
      </div>
    </div>
  )
}
