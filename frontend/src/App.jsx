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
  const [isSearching, setIsSearching] = useState(false);
  const [showCharts, setShowCharts] = useState(false);

  useEffect(() => {
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
      const res = await fetch(`${API}/songs/search?title=${encodeURIComponent(search)}&limit=100`);
      const data = await res.json();

      setIsSearching(true);
      setPage(1);

      const foundSongs = data.songs || [];
      setSongs(foundSongs);

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
      let url = `${API}/songs/export?sort_by=${sortBy}&sort_order=${sortOrder}`;
      
      if (isSearching && search.trim()) {
        url += `&title=${encodeURIComponent(search.trim())}`;
      }

      const res = await fetch(url);
      const blob = await res.blob();
      const downloadUrl = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = isSearching ? `songs_filtered.csv` : 'songs.csv';
      a.click();
      URL.revokeObjectURL(downloadUrl);

      setMessage(isSearching ? `Exported ${songs.length} filtered song(s)` : 'Exported all songs');
    } catch (err) {
      setMessage('Export error');
    }
  };

  const toggleCharts = () => {
    setShowCharts(!showCharts);
  };

  const SortIcon = ({ column }) => {
    if (sortBy !== column || isSearching) return null;
    return sortOrder === 'asc' ? ' ↑' : ' ↓';
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

        <button onClick={toggleCharts}>
          {showCharts ? 'Hide Charts' : 'Show Charts'}
        </button>

        <button onClick={handleExport}>
          Download CSV {isSearching && '(filtered)'}
        </button>
      </div>

      {message && <div className="message">{message}</div>}

      {showCharts && (
        <div className="charts-container">
          <h2>📊 Advanced Analytics (Matplotlib Charts)</h2>
          
          <div className="matplotlib-charts">
            <div className="chart-image">
              <h3>Danceability Scatter Plot</h3>
              <img 
                src={`${API}/charts/danceability-scatter`} 
                alt="Danceability Scatter Plot"
                onError={(e) => e.target.style.display = 'none'}
              />
            </div>

            <div className="chart-image">
              <h3>Song Duration Histogram</h3>
              <img 
                src={`${API}/charts/duration-histogram`} 
                alt="Duration Histogram"
                onError={(e) => e.target.style.display = 'none'}
              />
            </div>

            <div className="chart-image">
              <h3>Average Acousticness vs Tempo</h3>
              <img 
                src={`${API}/charts/acousticness-tempo-bar`} 
                alt="Acousticness vs Tempo"
                onError={(e) => e.target.style.display = 'none'}
              />
            </div>
          </div>
        </div>
      )}

      {loading ? (
        <div>Loading...</div>
      ) : (
        <>
          <div style={{ overflowX: 'auto' }}>
            <table>
              <thead>
                <tr>
                  <th onClick={() => handleSort('title')}>Title<SortIcon column="title" /></th>
                  <th onClick={() => handleSort('danceability')}>Dance<SortIcon column="danceability" /></th>
                  <th onClick={() => handleSort('energy')}>Energy<SortIcon column="energy" /></th>
                  <th onClick={() => handleSort('key')}>Key<SortIcon column="key" /></th>
                  <th onClick={() => handleSort('loudness')}>Loudness<SortIcon column="loudness" /></th>
                  <th onClick={() => handleSort('mode')}>Mode<SortIcon column="mode" /></th>
                  <th onClick={() => handleSort('acousticness')}>Acoustic<SortIcon column="acousticness" /></th>
                  <th onClick={() => handleSort('instrumentalness')}>Instrumental<SortIcon column="instrumentalness" /></th>
                  <th onClick={() => handleSort('liveness')}>Liveness<SortIcon column="liveness" /></th>
                  <th onClick={() => handleSort('valence')}>Valence<SortIcon column="valence" /></th>
                  <th onClick={() => handleSort('tempo')}>Tempo<SortIcon column="tempo" /></th>
                  <th onClick={() => handleSort('duration_ms')}>Duration (ms)<SortIcon column="duration_ms" /></th>
                  <th onClick={() => handleSort('time_signature')}>Time Sig<SortIcon column="time_signature" /></th>
                  <th onClick={() => handleSort('num_bars')}>Bars<SortIcon column="num_bars" /></th>
                  <th onClick={() => handleSort('num_sections')}>Sections<SortIcon column="num_sections" /></th>
                  <th onClick={() => handleSort('num_segments')}>Segments<SortIcon column="num_segments" /></th>
                  <th onClick={() => handleSort('class')}>Class<SortIcon column="class" /></th>
                  <th>Rating</th>
                </tr>
              </thead>

              <tbody>
                {songs.map((s) => (
                  <tr key={s.id}>
                    <td>{s.title}</td>
                    <td>{s.danceability?.toFixed(3)}</td>
                    <td>{s.energy?.toFixed(3)}</td>
                    <td>{s.key}</td>
                    <td>{s.loudness?.toFixed(2)}</td>
                    <td>{s.mode}</td>
                    <td>{s.acousticness?.toFixed(3)}</td>
                    <td>{s.instrumentalness?.toFixed(3)}</td>
                    <td>{s.liveness?.toFixed(3)}</td>
                    <td>{s.valence?.toFixed(3)}</td>
                    <td>{s.tempo?.toFixed(2)}</td>
                    <td>{s.duration_ms}</td>
                    <td>{s.time_signature}</td>
                    <td>{s.num_bars}</td>
                    <td>{s.num_sections}</td>
                    <td>{s.num_segments}</td>
                    <td>{s.class}</td>
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
          </div>

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