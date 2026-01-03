import { describe, test, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import App from './App'

// Mock fetch
global.fetch = vi.fn()
global.URL.createObjectURL = vi.fn()

describe('Song Playlist Manager', () => {
  beforeEach(() => {
    fetch.mockClear()
  })

  test('renders app title', () => {
    fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ songs: [], total: 0, page: 1, limit: 10, total_pages: 0 })
    })
    
    render(<App />)
    expect(screen.getByText(/Song Playlist Manager/i)).toBeInTheDocument()
  })

  test('renders file upload input', () => {
    fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ songs: [], total: 0, page: 1, limit: 10, total_pages: 0 })
    })
    
    render(<App />)
    expect(document.querySelector('input[type="file"]')).toBeInTheDocument()
  })

  test('renders search input', () => {
    fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ songs: [], total: 0, page: 1, limit: 10, total_pages: 0 })
    })
    
    render(<App />)
    expect(screen.getByPlaceholderText(/search song/i)).toBeInTheDocument()
  })

  test('displays songs after loading', async () => {
    fetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        songs: [
          { id: '1', title: 'Test Song', danceability: 0.5, energy: 0.7, tempo: 120, duration_ms: 200000, rating: 0 }
        ],
        total: 1,
        page: 1,
        limit: 10,
        total_pages: 1
      })
    })

    render(<App />)
    
    await waitFor(() => {
      expect(screen.getByText('Test Song')).toBeInTheDocument()
    })
  })

  test('search input updates on typing', () => {
    fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ songs: [], total: 0, page: 1, limit: 10, total_pages: 0 })
    })
    
    render(<App />)
    
    const searchInput = screen.getByPlaceholderText(/search song/i)
    fireEvent.change(searchInput, { target: { value: 'Test' } })
    expect(searchInput.value).toBe('Test')
  })

  test('displays found message after search', async () => {
  fetch.mockResolvedValueOnce({
    ok: true,
    json: async () => ({ songs: [], total: 0, page: 1, limit: 10, total_pages: 0 })
  })

  fetch.mockResolvedValueOnce({
    ok: true,
    json: async () => ({
      count: 2,
      songs: [
        { id: '1', title: 'Found Song', danceability: 0.5, energy: 0.7, tempo: 120, duration_ms: 200000, rating: 0 },
        { id: '2', title: 'Found Song Remix', danceability: 0.6, energy: 0.8, tempo: 128, duration_ms: 210000, rating: 0 }
      ]
    })
  })

  render(<App />)

  const searchInput = screen.getByPlaceholderText(/search song/i)
  const searchButton = screen.getByText(/^search$/i)

  fireEvent.change(searchInput, { target: { value: 'Found' } })
  fireEvent.click(searchButton)

  await waitFor(() => {
    expect(screen.getByText(/found 2 song\(s\)/i)).toBeInTheDocument()
  })
})



  test('displays not found message', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ songs: [], total: 0, page: 1, limit: 10, total_pages: 0 })
    })
    
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ found: false, message: 'Song not found' })
    })

    render(<App />)
    
    const searchInput = screen.getByPlaceholderText(/search song/i)
    const searchButton = screen.getByText(/^search$/i)
    
    fireEvent.change(searchInput, { target: { value: 'Nothing' } })
    fireEvent.click(searchButton)

    await waitFor(() => {
      expect(screen.getByText(/song not found/i)).toBeInTheDocument()
    })
  })

  test('displays star ratings', async () => {
    fetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        songs: [
          { id: '1', title: 'Song', danceability: 0.5, energy: 0.7, tempo: 120, duration_ms: 200000, rating: 3 }
        ],
        total: 1,
        page: 1,
        limit: 10,
        total_pages: 1
      })
    })

    render(<App />)
    
    await waitFor(() => {
      const stars = screen.getAllByText('★')
      expect(stars.length).toBe(5)
    })
  })

  test('pagination buttons exist', async () => {
    fetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        songs: [{ id: '1', title: 'Song', danceability: 0.5, energy: 0.7, tempo: 120, duration_ms: 200000, rating: 0 }],
        total: 25,
        page: 1,
        limit: 10,
        total_pages: 3
      })
    })

    render(<App />)
    
    await waitFor(() => {
      expect(screen.getByText(/previous/i)).toBeInTheDocument()
      expect(screen.getByText(/next/i)).toBeInTheDocument()
    })
  })

  test('export triggers CSV download', async () => {
  const mockBlob = new Blob(['a,b\n1,2'], { type: 'text/csv' })

  fetch
    .mockResolvedValueOnce({ // initial load
      ok: true,
      json: async () => ({ songs: [], total: 0, page: 1, limit: 10, total_pages: 0 })
    })
    .mockResolvedValueOnce({ // export
      ok: true,
      blob: async () => mockBlob
    })

  render(<App />)

  fireEvent.click(screen.getByText(/download csv/i))

  await waitFor(() => {
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/songs/export'))
    expect(URL.createObjectURL).toHaveBeenCalled()
  })
})

test('fetches songs with pagination + sorting params', async () => {
  render(<App />)

  await waitFor(() => {
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/songs?page=1&limit=10')
    )
  })
})


})