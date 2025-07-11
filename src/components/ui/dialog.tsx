import * as React from "react"
import { cn } from "@/lib/utils"
// import { Button } from "./button"

interface DialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  children: React.ReactNode
}

function Dialog({ open, onOpenChange, children }: DialogProps) {
  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm"
        onClick={() => onOpenChange(false)}
      />
      <div className="relative z-50 w-full max-w-md mx-4">
        {children}
      </div>
    </div>
  )
}

interface DialogContentProps {
  className?: string
  children: React.ReactNode
}

function DialogContent({ className, children }: DialogContentProps) {
  return (
    <div
      className={cn(
        "bg-white rounded-lg shadow-lg border animate-in fade-in-0 zoom-in-95",
        className
      )}
    >
      {children}
    </div>
  )
}

interface DialogHeaderProps {
  className?: string
  children: React.ReactNode
}

function DialogHeader({ className, children }: DialogHeaderProps) {
  return (
    <div className={cn("px-6 py-4 border-b", className)}>
      {children}
    </div>
  )
}

interface DialogTitleProps {
  className?: string
  children: React.ReactNode
}

function DialogTitle({ className, children }: DialogTitleProps) {
  return (
    <h3 className={cn("text-lg font-semibold text-gray-900", className)}>
      {children}
    </h3>
  )
}

interface DialogDescriptionProps {
  className?: string
  children: React.ReactNode
}

function DialogDescription({ className, children }: DialogDescriptionProps) {
  return (
    <p className={cn("text-sm text-gray-600 mt-1", className)}>
      {children}
    </p>
  )
}

interface DialogFooterProps {
  className?: string
  children: React.ReactNode
}

function DialogFooter({ className, children }: DialogFooterProps) {
  return (
    <div className={cn("px-6 py-4 border-t bg-gray-50 rounded-b-lg flex justify-end gap-2", className)}>
      {children}
    </div>
  )
}

export {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
}