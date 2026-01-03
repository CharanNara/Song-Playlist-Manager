import React, { useState, useEffect } from 'react';
import './App.css';

const API = 'http://localhost:8000/api';
const PAGE_SIZE = 10;

function App() {
  const [songs, setSongs] = useState([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [sortBy, setSortBy] = useState('title');
  const [sortOrder, setSortOrder] = useState('asc');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  // NEW: track whether we are showing search results or full paginated list
  const [isSearching, setIsSearching] = useState(false);

  useEffect(() => {
    // Only auto-fetch paginated list when NOT in search mode
    if (!isSearching) fetchSongs();
  }, [page, sortBy, sortOrder, isSearching]);

  const fetchSongs = async () => {
    setLoading(true);
    try {
      const res = await fetch(
        `${API}/songs?page=${page}&limit=${PAGE_SIZE}&sort_by=${sortBy}&sort_order=${sortOrder}`
      );
      const data = await res.json();

      setSongs(data.songs);
      setTotal(data.total);
      setTotalPages(data.total_pages);
      setMessage(`Loaded ${data.songs.length} songs`);
    } catch (err) {
      setMessage('Error loading songs');
    }
    setLoading(false);
  };

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    setLoading(true);
    try {
      const res = await fetch(`${API}/load-data`, { method: 'POST', body: formData });
      const data = await res.json();

      setMessage(`Loaded ${data.songs_loaded} songs`);

      // After upload, exit search mode and refresh list
      setIsSearching(false);
      setSearch('');
      setPage(1);
      await fetchSongs();
    } catch (err) {
      setMessage('Error uploading file');
    }
    setLoading(false);
  };

  const handleSort = (col) => {
    // If searching, ignore sorting (optional choice for MVP)
    // You can also choose to allow client-side sorting during search.
    if (isSearching) return;

    if (sortBy === col) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(col);
      setSortOrder('asc');
    }
    setPage(1);
  };

  const handleSearch = async () => {
    if (!search.trim()) return;

    setLoading(true);
    try {
      // Ask backend for up to 100 matches (bounded)
      const res = await fetch(`${API}/songs/search?title=${encodeURIComponent(search)}&limit=100`);
      const data = await res.json();

      setIsSearching(true);
      setPage(1); // freeze UI at page 1 for search mode

      const foundSongs = data.songs || [];
      setSongs(foundSongs);

      // Freeze pagination numbers to reflect current view
      setTotal(data.count || foundSongs.length);
      setTotalPages(1);

      setMessage((data.count || 0) > 0 ? `Found ${data.count} song(s)` : 'Song not found');
    } catch (err) {
      setMessage('Search error');
    }
    setLoading(false);
  };

  const handleClear = async () => {
    setSearch('');
    setIsSearching(false);
    setPage(1);
    await fetchSongs();
  };

  const handleRate = async (id, rating) => {
    try {
      await fetch(`${API}/songs/${id}/rating`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rating })
      });
      setSongs(songs.map(s => (s.id === id ? { ...s, rating } : s)));
    } catch (err) {
      console.error('Rating error');
    }
  };

  const handleExport = async () => {
    try {
      const res = await fetch(`${API}/songs/export`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'songs.csv';
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setMessage('Export error');
    }
  };

  return (
    <div className="app">
      <h1>🎵 Song Playlist Manager</h1>

      <div className="controls">
        <input type="file" accept=".json" onChange={handleUpload} />

        <div className="search">
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Search song..."
          />
          <button onClick={handleSearch}>Search</button>
          <button onClick={handleClear}>Clear</button>
        </div>

        <button onClick={handleExport}>Download CSV</button>
      </div>

      {message && <div className="message">{message}</div>}

      {loading ? (
        <div>Loading...</div>
      ) : (
        <>
          <table>
            <thead>
              <tr>
                <th onClick={() => handleSort('title')}>
                  Title {sortBy === 'title' && !isSearching && (sortOrder === 'asc' ? '↑' : '↓')}
                </th>
                <th onClick={() => handleSort('danceability')}>
                  Dance {sortBy === 'danceability' && !isSearching && (sortOrder === 'asc' ? '↑' : '↓')}
                </th>
                <th onClick={() => handleSort('energy')}>
                  Energy {sortBy === 'energy' && !isSearching && (sortOrder === 'asc' ? '↑' : '↓')}
                </th>
                <th onClick={() => handleSort('tempo')}>
                  Tempo {sortBy === 'tempo' && !isSearching && (sortOrder === 'asc' ? '↑' : '↓')}
                </th>
                <th onClick={() => handleSort('duration_ms')}>
                  Duration {sortBy === 'duration_ms' && !isSearching && (sortOrder === 'asc' ? '↑' : '↓')}
                </th>
                <th>Rating</th>
              </tr>
            </thead>

            <tbody>
              {songs.map((s) => (
                <tr key={s.id}>
                  <td>{s.title}</td>
                  <td>{s.danceability?.toFixed(3)}</td>
                  <td>{s.energy?.toFixed(3)}</td>
                  <td>{s.tempo?.toFixed(2)}</td>
                  <td>{s.duration_ms}</td>
                  <td>
                    {[1, 2, 3, 4, 5].map((star) => (
                      <span
                        key={star}
                        className={star <= (s.rating || 0) ? 'star filled' : 'star'}
                        onClick={() => handleRate(s.id, star)}
                      >
                        ★
                      </span>
                    ))}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="pagination">
            <button
              onClick={() => setPage(page - 1)}
              disabled={page === 1 || isSearching}
            >
              Previous
            </button>

            <span>
              Page {page} of {totalPages} ({total} songs){isSearching ? ' • Search results' : ''}
            </span>

            <button
              onClick={() => setPage(page + 1)}
              disabled={page === totalPages || isSearching}
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  );
}

export default App;
