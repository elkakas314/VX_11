/**
 * useBookmarks Hook — Local bookmark management (localStorage/IndexedDB)
 * Persistent across sessions
 * No backend required
 */

import { useState, useEffect } from "react";
import { Bookmark } from "../types/v8_1_extensions";

const STORAGE_KEY = "vx11_operator_bookmarks";

export const useBookmarks = () => {
    const [bookmarks, setBookmarks] = useState<Bookmark[]>([]);
    const [loaded, setLoaded] = useState(false);

    // Load from localStorage on mount
    useEffect(() => {
        try {
            const stored = localStorage.getItem(STORAGE_KEY);
            if (stored) {
                setBookmarks(JSON.parse(stored));
            }
        } catch (e) {
            console.error("Failed to load bookmarks:", e);
        }
        setLoaded(true);
    }, []);

    // Save to localStorage whenever bookmarks change
    useEffect(() => {
        if (loaded) {
            try {
                localStorage.setItem(STORAGE_KEY, JSON.stringify(bookmarks));
            } catch (e) {
                console.error("Failed to save bookmarks:", e);
            }
        }
    }, [bookmarks, loaded]);

    const addBookmark = (eventId: string, timestamp: number, label?: string): string => {
        const id = `bm_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        const bookmark: Bookmark = {
            id,
            event_id: eventId,
            timestamp,
            label,
            created_at: Date.now(),
        };
        setBookmarks((prev) => [bookmark, ...prev]);
        return id;
    };

    const removeBookmark = (id: string) => {
        setBookmarks((prev) => prev.filter((bm) => bm.id !== id));
    };

    const updateBookmark = (id: string, label?: string) => {
        setBookmarks((prev) =>
            prev.map((bm) => (bm.id === id ? { ...bm, label } : bm))
        );
    };

    const isBookmarked = (eventId: string): boolean => {
        return bookmarks.some((bm) => bm.event_id === eventId);
    };

    const getBookmarkForEvent = (eventId: string): Bookmark | undefined => {
        return bookmarks.find((bm) => bm.event_id === eventId);
    };

    return {
        bookmarks,
        addBookmark,
        removeBookmark,
        updateBookmark,
        isBookmarked,
        getBookmarkForEvent,
        loaded,
    };
};
