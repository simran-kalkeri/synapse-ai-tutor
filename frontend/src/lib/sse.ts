/**
 * SSE streaming client for tutor / chat endpoints.
 * Uses fetch() with ReadableStream to process server-sent events.
 */

const BASE_URL = import.meta.env.VITE_API_URL || ''
const STREAM_TIMEOUT_MS = 120_000

export interface SSEOptions {
  onChunk:    (text: string) => void
  onSources?: (sources: unknown[]) => void
  onMetadata?: (meta: Record<string, unknown>) => void
  onDone:     () => void
  onError:    (err: string) => void
  onEvent?:   (event: { type: string; content?: unknown; steps?: string[] }) => void
}

export async function streamSSE(
  path: string,
  body: Record<string, unknown>,
  options: SSEOptions
): Promise<() => void> {
  const controller = new AbortController()
  const token = localStorage.getItem('synapse_access_token') ?? ''

  try {
    const response = await fetch(`${BASE_URL}${path}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(body),
      signal: controller.signal,
    })

    if (!response.ok) {
      options.onError(`HTTP ${response.status}: ${response.statusText}`)
      return () => controller.abort()
    }

    if (!response.body) {
      options.onError('No response body')
      return () => controller.abort()
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    let buffer = ''

    // Timeout watchdog — fires if no data received for STREAM_TIMEOUT_MS
    let lastDataTime = Date.now()
    const timeoutId = setInterval(() => {
      if (Date.now() - lastDataTime > STREAM_TIMEOUT_MS) {
        controller.abort()
        options.onError('Stream timed out — no data received for 120s')
      }
    }, 30_000)

    const pump = async () => {
      while (true) {
        const { value, done } = await reader.read()
        if (done) { clearInterval(timeoutId); options.onDone(); break }

        lastDataTime = Date.now()

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const raw = line.slice(6).trim()
          if (!raw) continue
          try {
            const event = JSON.parse(raw) as {
              type: string
              content?: string
              sources?: unknown[]
              metadata?: Record<string, unknown>
            }
            options.onEvent?.(event)
            switch (event.type) {
              case 'chunk':
                if (event.content) options.onChunk(event.content)
                break
              case 'sources':
                if (event.sources && options.onSources) options.onSources(event.sources)
                break
              case 'metadata':
                if (event.metadata && options.onMetadata) options.onMetadata(event.metadata)
                break
              case 'done':
                clearInterval(timeoutId)
                options.onDone()
                return
              case 'error':
                clearInterval(timeoutId)
                options.onError(event.content ?? 'Stream error')
                return
            }
          } catch {
            // ignore malformed lines
          }
        }
      }
    }

    pump().catch((err) => {
      clearInterval(timeoutId)
      if (err.name !== 'AbortError') options.onError(String(err))
    })
  } catch (err) {
    if ((err as Error).name !== 'AbortError') {
      options.onError(String(err))
    }
  }

  return () => controller.abort()
}
