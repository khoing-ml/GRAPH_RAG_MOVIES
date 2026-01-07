# 📁 Crawled Movie Data - Ready for UI/UX Development

This folder contains all crawled movie data saved locally before uploading to databases.

## 📂 Folder Structure

```
crawled_data/
├── movies/              # Individual movie JSON files (one per movie)
│   ├── 550.json        # Fight Club
│   ├── 680.json        # Pulp Fiction
│   └── ...
├── posters/            # Poster URL references (one per movie)
│   ├── 550.txt         # Contains poster URL for Fight Club
│   ├── 680.txt         # Contains poster URL for Pulp Fiction
│   └── ...
├── movies_index.json   # Master index file (all movies overview)
└── README.md           # This file
```

## 📄 File Formats

### movies_index.json
Master index with quick overview of all movies:
```json
{
  "total_movies": 1000,
  "crawl_date": "2026-01-05 10:30:00",
  "movies": [
    {
      "id": 550,
      "title": "Fight Club",
      "year": "1999",
      "rating": 8.433,
      "genres": ["Drama", "Thriller", "Comedy"],
      "poster_url": "https://image.tmdb.org/t/p/w500/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg",
      "file": "550.json"
    }
  ]
}
```

### movies/{id}.json
Complete movie data including:
- **movie**: Full TMDB movie object (title, overview, genres, budget, revenue, poster, backdrop, etc.)
- **credits**: Cast and crew information
- **keywords**: Thematic tags (heist, revenge, time travel, etc.)
- **similar**: Similar/recommended movies

Example structure:
```json
{
  "movie": {
    "id": 550,
    "title": "Fight Club",
    "overview": "A ticking-time-bomb insomniac...",
    "genres": [{"id": 18, "name": "Drama"}],
    "release_date": "1999-10-15",
    "vote_average": 8.433,
    "runtime": 139,
    "budget": 63000000,
    "revenue": 100853753,
    "tagline": "Mischief. Mayhem. Soap.",
    "poster_path": "/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg",
    "backdrop_path": "/fCayJrkfRaCRCTh8GqN30f8oyQF.jpg",
    "production_companies": [...],
    "production_countries": [...],
    "belongs_to_collection": null
  },
  "credits": {
    "cast": [
      {
        "id": 819,
        "name": "Edward Norton",
        "character": "The Narrator",
        "order": 0
      },
      {
        "id": 287,
        "name": "Brad Pitt",
        "character": "Tyler Durden",
        "order": 1
      }
    ],
    "crew": [
      {
        "id": 7467,
        "name": "David Fincher",
        "job": "Director"
      },
      {
        "name": "Jeff Cronenweth",
        "job": "Director of Photography"
      }
    ]
  },
  "keywords": {
    "keywords": [
      {"id": 825, "name": "support group"},
      {"id": 849, "name": "dual identity"},
      {"id": 1721, "name": "nihilism"}
    ]
  },
  "similar": {
    "results": [
      {
        "id": 680,
        "title": "Pulp Fiction",
        "vote_average": 8.5
      }
    ]
  }
}
```

### posters/{id}.txt
Simple text file containing the full poster URL:
```
https://image.tmdb.org/t/p/w500/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg
```

## 🎨 UI/UX Usage Examples

### 1. Display Movie Grid
```javascript
// Load index
fetch('crawled_data/movies_index.json')
  .then(res => res.json())
  .then(data => {
    data.movies.forEach(movie => {
      // Create card
      const card = `
        <div class="movie-card">
          <img src="${movie.poster_url}" alt="${movie.title}">
          <h3>${movie.title} (${movie.year})</h3>
          <p>⭐ ${movie.rating.toFixed(1)}/10</p>
          <p>${movie.genres.join(', ')}</p>
        </div>
      `;
    });
  });
```

### 2. Load Detailed Movie Page
```javascript
// Load full movie data
fetch(`crawled_data/movies/${movieId}.json`)
  .then(res => res.json())
  .then(data => {
    const movie = data.movie;
    const credits = data.credits;
    const keywords = data.keywords.keywords;
    
    // Display movie info
    document.title = movie.title;
    document.getElementById('poster').src = 
      `https://image.tmdb.org/t/p/w500${movie.poster_path}`;
    document.getElementById('overview').textContent = movie.overview;
    
    // Display cast
    const cast = credits.cast.slice(0, 5).map(c => c.name);
    document.getElementById('cast').textContent = cast.join(', ');
    
    // Display keywords
    const keywordTags = keywords.map(k => 
      `<span class="tag">${k.name}</span>`
    ).join('');
    document.getElementById('keywords').innerHTML = keywordTags;
  });
```

### 3. Search/Filter Movies
```javascript
// Load index and filter
fetch('crawled_data/movies_index.json')
  .then(res => res.json())
  .then(data => {
    // Filter by genre
    const actionMovies = data.movies.filter(m => 
      m.genres.includes('Action')
    );
    
    // Filter by rating
    const topRated = data.movies.filter(m => m.rating >= 8.0);
    
    // Filter by year
    const recent = data.movies.filter(m => 
      parseInt(m.year) >= 2020
    );
  });
```

### 4. Create Movie Recommendations
```javascript
// Load movie and its similar movies
async function getRecommendations(movieId) {
  const response = await fetch(`crawled_data/movies/${movieId}.json`);
  const data = await response.json();
  
  // Get similar movie IDs
  const similarIds = data.similar.results.map(s => s.id);
  
  // Load details for similar movies
  const recommendations = await Promise.all(
    similarIds.slice(0, 5).map(id => 
      fetch(`crawled_data/movies/${id}.json`).then(r => r.json())
    )
  );
  
  return recommendations;
}
```

### 5. Python/Flask Backend
```python
import json
from flask import Flask, jsonify

app = Flask(__name__)

# Load index once at startup
with open('crawled_data/movies_index.json', 'r') as f:
    movies_index = json.load(f)

@app.route('/api/movies')
def get_movies():
    return jsonify(movies_index)

@app.route('/api/movies/<int:movie_id>')
def get_movie(movie_id):
    with open(f'crawled_data/movies/{movie_id}.json', 'r') as f:
        return jsonify(json.load(f))

@app.route('/api/movies/genre/<genre>')
def get_by_genre(genre):
    filtered = [m for m in movies_index['movies'] 
                if genre in m['genres']]
    return jsonify(filtered)
```

## 🖼️ Image URLs

All poster and backdrop URLs use TMDB's CDN with different sizes available:

### Poster Sizes
- `w92` - 92px wide (thumbnail)
- `w154` - 154px wide (small)
- `w185` - 185px wide (default)
- `w342` - 342px wide (medium)
- `w500` - 500px wide (large) ⭐ **Used by default**
- `w780` - 780px wide (extra large)
- `original` - Original size

### Example
```
Base URL: https://image.tmdb.org/t/p/
Poster path: /pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg

Sizes:
- Small: https://image.tmdb.org/t/p/w185/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg
- Large: https://image.tmdb.org/t/p/w500/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg
- Original: https://image.tmdb.org/t/p/original/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg
```

## 📊 Data Fields Reference

### Key Movie Fields
- `id` - TMDB movie ID
- `title` - Movie title
- `overview` - Plot summary
- `genres` - Array of genre objects
- `release_date` - Release date (YYYY-MM-DD)
- `vote_average` - Rating (0-10)
- `vote_count` - Number of votes
- `runtime` - Duration in minutes
- `budget` - Production budget ($)
- `revenue` - Box office revenue ($)
- `tagline` - Marketing tagline
- `poster_path` - Poster image path
- `backdrop_path` - Backdrop image path
- `production_companies` - Array of production companies
- `production_countries` - Array of countries
- `belongs_to_collection` - Movie collection/franchise info

### Key Credits Fields
- `cast` - Array of actors (name, character, order)
- `crew` - Array of crew (name, job, department)
  - Directors: job = "Director"
  - Writers: job in ["Screenplay", "Writer", "Story"]
  - Cinematographers: job = "Director of Photography"
  - Composers: job = "Original Music Composer"

### Keywords
Array of thematic tags:
- `id` - Keyword ID
- `name` - Keyword text

### Similar Movies
Array of recommended movies:
- `id` - Movie ID
- `title` - Movie title
- `vote_average` - Rating

## 🔧 Tips

1. **Performance**: Load `movies_index.json` once for listings, then load individual files on demand
2. **Caching**: Cache frequently accessed movie files in memory
3. **Image Loading**: Use lazy loading for posters to improve page load time
4. **Filtering**: Use the index for fast filtering, avoid loading all individual files
5. **Pagination**: The index is pre-sorted by rating - slice for pagination

## 📝 Notes

- All data is from TMDB (The Movie Database)
- Data is in JSON format with UTF-8 encoding
- File names are TMDB movie IDs
- Poster URLs are valid and ready to use
- Data is complete and includes all relationships needed for the graph database

## 🎯 Ready for UI/UX Development!

This data structure is optimized for building movie UIs:
- Fast loading with index file
- Detailed information on demand
- Ready-to-use image URLs
- Rich metadata for filtering and search
- Complete relationship data for recommendations

Start building your movie app! 🎬
