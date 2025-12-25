import { useState, useEffect } from 'react'

export function useApi<T>(fn: () => Promise<T>, deps: any[] = []) {
    const [data, setData] = useState<T | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        let isMounted = true

        const fetch = async () => {
            try {
                setLoading(true)
                const result = await fn()
                if (isMounted) {
                    setData(result)
                    setError(null)
                }
            } catch (err: any) {
                if (isMounted) {
                    setError(err.message || 'API Error')
                    setData(null)
                }
            } finally {
                if (isMounted) {
                    setLoading(false)
                }
            }
        }

        fetch()
        return () => { isMounted = false }
    }, deps)

    return { data, loading, error }
}
