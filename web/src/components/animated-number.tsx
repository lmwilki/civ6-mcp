"use client"

import { useEffect, useRef, useState } from "react"

export function AnimatedNumber({
  value,
  duration = 400,
  decimals = 1,
}: {
  value: number
  duration?: number
  decimals?: number
}) {
  const [displayed, setDisplayed] = useState(value)
  const displayedRef = useRef(value)
  const frameRef = useRef(0)

  useEffect(() => {
    const from = displayedRef.current
    const to = value

    if (Math.abs(from - to) < 0.001) {
      displayedRef.current = to
      setDisplayed(to)
      return
    }

    const start = performance.now()
    const animate = (now: number) => {
      const elapsed = now - start
      const progress = Math.min(elapsed / duration, 1)
      // ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3)
      const current = from + (to - from) * eased
      displayedRef.current = current
      setDisplayed(current)
      if (progress < 1) {
        frameRef.current = requestAnimationFrame(animate)
      } else {
        displayedRef.current = to
        setDisplayed(to)
      }
    }
    frameRef.current = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(frameRef.current)
  }, [value, duration])

  const factor = Math.pow(10, decimals)
  return <>{Math.round(displayed * factor) / factor}</>
}
