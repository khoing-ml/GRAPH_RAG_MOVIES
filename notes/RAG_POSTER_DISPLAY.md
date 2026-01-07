# 🎨 Displaying Movies with Posters in RAG System

## Quick Answer: YES! ✅
Every movie has its ID linked to the poster URL, so the RAG system can display beautiful posters when recommending movies!

---

## 📊 Data Structure

### In Qdrant (Vector DB)
```json
{
  "tmdb_id": 550,
  "title": "Fight Club",
  "year": "1999",
  "rating": 8.4,
  "poster_url": "https://image.tmdb.org/t/p/w500/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg",
  "backdrop_url": "https://image.tmdb.org/t/p/w500/fCayJrkfRaCRCTh8GqN30f8oyQF.jpg",
  "overview": "...",
  "genres": ["Drama", "Thriller"],
  "cast": ["Brad Pitt", "Edward Norton"],
  "directors": ["David Fincher"]
}
```

### In Neo4j (Graph DB)
```cypher
(m:Movie {
  id: 550,
  title: "Fight Club",
  poster_url: "https://...",
  backdrop_url: "https://...",
  ...
})
```

---

## 🎯 How to Use in RAG System

### Method 1: Vector Search with Posters (Simple)
```python
# Search for movies
movies = get_movie_with_poster_from_qdrant("action movies", limit=5)

# Each movie has:
for movie in movies:
    print(f"ID: {movie['id']}")
    print(f"Title: {movie['title']}")
    print(f"Poster: {movie['poster_url']}")  # ← Ready to display!
```

### Method 2: Get Movie by ID
```python
# If you have movie ID
movie = get_movie_with_poster_from_neo4j(550)

print(movie['title'])        # "Fight Club"
print(movie['poster_url'])   # "https://..."
```

### Method 3: Format for UI (JSON)
```python
# Get recommendations
movies = get_movie_with_poster_from_qdrant("sci-fi movies", limit=5)

# Convert to JSON for frontend
json_data = create_movie_card_json(movies)

# Returns:
# [
#   {
#     "id": 603,
#     "title": "The Matrix",
#     "poster": "https://image.tmdb.org/t/p/w500/...",
#     "rating": 8.7,
#     "year": "1999",
#     "genres": ["Action", "Science Fiction"]
#   },
#   ...
# ]
```

---

## 💬 RAG Response Format

### Text + Visual Response
```python
# User asks: "Recommend me action movies"

# 1. Get movies with posters
movies = get_movie_with_poster_from_qdrant("action movies", limit=5)

# 2. Create response
response = {
    "text": "Here are 5 excellent action movies I recommend:",
    "movies": [
        {
            "id": 550,
            "title": "Fight Club",
            "year": "1999",
            "rating": 8.4,
            "poster": "https://image.tmdb.org/t/p/w500/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg",
            "genres": ["Drama", "Thriller", "Action"]
        },
        # ... more movies
    ],
    "display_mode": "cards"  # Tell UI to show as cards with posters
}
```

---

## 🎨 Frontend Display Examples

### HTML/JavaScript
```html
<div class="movie-recommendations">
    <p>Here are 5 excellent action movies I recommend:</p>
    <div class="movie-grid">
        <!-- For each movie -->
        <div class="movie-card">
            <img src="https://image.tmdb.org/t/p/w500/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg" 
                 alt="Fight Club">
            <h3>Fight Club</h3>
            <p>⭐ 8.4/10 • 1999</p>
            <div class="genres">
                <span>Drama</span>
                <span>Thriller</span>
            </div>
        </div>
    </div>
</div>
```

### React Component
```jsx
function MovieRecommendation({ movies }) {
  return (
    <div className="recommendations">
      {movies.map(movie => (
        <div key={movie.id} className="movie-card">
          <img src={movie.poster} alt={movie.title} />
          <h3>{movie.title}</h3>
          <p>⭐ {movie.rating}/10 • {movie.year}</p>
          <div className="genres">
            {movie.genres.map(g => <span key={g}>{g}</span>)}
          </div>
        </div>
      ))}
    </div>
  );
}
```

### Vue Component
```vue
<template>
  <div class="recommendations">
    <div v-for="movie in movies" :key="movie.id" class="movie-card">
      <img :src="movie.poster" :alt="movie.title">
      <h3>{{ movie.title }}</h3>
      <p>⭐ {{ movie.rating }}/10 • {{ movie.year }}</p>
      <div class="genres">
        <span v-for="genre in movie.genres" :key="genre">{{ genre }}</span>
      </div>
    </div>
  </div>
</template>
```

---

## 🔧 Integration with RAG Pipeline

### Step 1: Update `src/rag_pipeline.py`
```python
from src.vector_db import get_movie_with_poster_from_qdrant
from src.graph_db import get_movie_with_poster_from_neo4j

class RAGPipeline:
    def generate_response(self, query):
        # 1. Search for relevant movies (with posters!)
        movies = get_movie_with_poster_from_qdrant(query, limit=5)
        
        # 2. Enrich with graph data if needed
        for movie in movies:
            graph_data = get_movie_with_poster_from_neo4j(movie['id'])
            movie.update(graph_data)
        
        # 3. Generate text response
        text_response = self.llm.generate(
            f"Based on these movies: {movies}, answer: {query}"
        )
        
        # 4. Return text + visual data
        return {
            "text": text_response,
            "movies": movies,  # ← Includes poster URLs!
            "display_mode": "cards"
        }
```

### Step 2: Update API Endpoint
```python
@app.route('/api/ask', methods=['POST'])
def ask():
    query = request.json['query']
    
    # Get response with movies + posters
    response = rag_pipeline.generate_response(query)
    
    # Format movies for display
    response['movies'] = [
        {
            'id': m['id'],
            'title': m['title'],
            'poster': m['poster_url'],
            'backdrop': m['backdrop_url'],
            'rating': m['rating'],
            'year': m['year'],
            'genres': m['genres']
        }
        for m in response['movies']
    ]
    
    return jsonify(response)
```

### Step 3: Frontend Display
```javascript
// Call API
const response = await fetch('/api/ask', {
    method: 'POST',
    body: JSON.stringify({ query: "Recommend action movies" })
});

const data = await response.json();

// Display text
document.getElementById('response-text').textContent = data.text;

// Display movies with posters
const moviesHtml = data.movies.map(movie => `
    <div class="movie-card">
        <img src="${movie.poster}" alt="${movie.title}">
        <h3>${movie.title}</h3>
        <p>⭐ ${movie.rating}/10 • ${movie.year}</p>
        <div class="genres">
            ${movie.genres.map(g => `<span>${g}</span>`).join('')}
        </div>
    </div>
`).join('');

document.getElementById('movies-grid').innerHTML = moviesHtml;
```

---

## 🎭 Different Display Modes

### 1. Card Grid (Posters)
```json
{
  "display_mode": "cards",
  "movies": [
    {
      "id": 550,
      "title": "Fight Club",
      "poster": "https://...",
      "rating": 8.4
    }
  ]
}
```

### 2. List View (Small Posters)
```json
{
  "display_mode": "list",
  "movies": [
    {
      "id": 550,
      "title": "Fight Club",
      "poster": "https://image.tmdb.org/t/p/w185/...",  // Smaller
      "year": "1999"
    }
  ]
}
```

### 3. Hero View (Large Backdrop)
```json
{
  "display_mode": "hero",
  "movie": {
    "id": 550,
    "title": "Fight Club",
    "backdrop": "https://image.tmdb.org/t/p/original/...",  // Full size
    "overview": "..."
  }
}
```

---

## 📏 Image Size Options

TMDB provides multiple sizes for posters:

### Poster Sizes
```python
POSTER_SIZES = {
    'thumbnail': 'w92',      # 92px - Very small
    'small': 'w154',         # 154px - Mobile
    'medium': 'w185',        # 185px - Default mobile
    'large': 'w342',         # 342px - Tablet
    'xlarge': 'w500',        # 500px - Desktop (default)
    'xxlarge': 'w780',       # 780px - Large screen
    'original': 'original'   # Full resolution
}

# Usage
base_url = "https://image.tmdb.org/t/p/"
poster_path = "/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg"

thumbnail = f"{base_url}w92{poster_path}"
desktop = f"{base_url}w500{poster_path}"
fullsize = f"{base_url}original{poster_path}"
```

### Responsive Images
```html
<img 
  srcset="
    https://image.tmdb.org/t/p/w185/poster.jpg 185w,
    https://image.tmdb.org/t/p/w342/poster.jpg 342w,
    https://image.tmdb.org/t/p/w500/poster.jpg 500w,
    https://image.tmdb.org/t/p/w780/poster.jpg 780w
  "
  sizes="(max-width: 640px) 185px, 
         (max-width: 1024px) 342px, 
         500px"
  src="https://image.tmdb.org/t/p/w500/poster.jpg"
  alt="Movie Poster"
>
```

---

## 💡 Smart Response Examples

### Example 1: Simple Recommendation
**User**: "Recommend me action movies"

**RAG Response**:
```json
{
  "text": "Here are 5 highly-rated action movies I recommend:",
  "movies": [
    {
      "id": 155,
      "title": "The Dark Knight",
      "poster": "https://image.tmdb.org/t/p/w500/...",
      "rating": 9.0,
      "year": "2008",
      "genres": ["Action", "Crime", "Drama"]
    },
    // ... 4 more
  ],
  "display_mode": "cards"
}
```

### Example 2: Similar Movies
**User**: "Movies like Inception"

**RAG Response**:
```json
{
  "text": "Based on Inception, here are similar mind-bending thrillers:",
  "reference_movie": {
    "id": 27205,
    "title": "Inception",
    "poster": "https://..."
  },
  "movies": [
    {
      "id": 603,
      "title": "The Matrix",
      "poster": "https://...",
      "similarity_reason": "Both explore reality vs simulation themes"
    },
    // ... more
  ],
  "display_mode": "comparison"
}
```

### Example 3: Director's Filmography
**User**: "Show me Christopher Nolan movies"

**RAG Response**:
```json
{
  "text": "Christopher Nolan has directed 11 acclaimed films:",
  "director": {
    "name": "Christopher Nolan",
    "photo": "https://..."
  },
  "movies": [
    {
      "id": 27205,
      "title": "Inception",
      "poster": "https://...",
      "year": "2010",
      "rating": 8.8
    },
    // ... sorted by year or rating
  ],
  "display_mode": "timeline"
}
```

---

## 🎨 CSS Styling Examples

### Beautiful Movie Cards
```css
.movie-card {
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transition: transform 0.3s, box-shadow 0.3s;
  cursor: pointer;
}

.movie-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
}

.movie-card img {
  width: 100%;
  height: 300px;
  object-fit: cover;
}

.movie-card .info {
  padding: 15px;
  background: linear-gradient(to top, rgba(0,0,0,0.9), transparent);
  position: absolute;
  bottom: 0;
  width: 100%;
  color: white;
}

.movie-card .rating {
  display: inline-block;
  background: #ffd700;
  color: #000;
  padding: 4px 10px;
  border-radius: 20px;
  font-weight: bold;
}
```

---

## 🚀 Performance Tips

### 1. Lazy Loading
```javascript
// Load posters as user scrolls
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const img = entry.target;
      img.src = img.dataset.src;
      observer.unobserve(img);
    }
  });
});

document.querySelectorAll('img[data-src]').forEach(img => {
  observer.observe(img);
});
```

### 2. Image Caching
```javascript
// Preload posters
function preloadPosters(movies) {
  movies.forEach(movie => {
    const img = new Image();
    img.src = movie.poster;
  });
}
```

### 3. Fallback Images
```html
<img 
  src="https://image.tmdb.org/t/p/w500/poster.jpg"
  onerror="this.src='https://via.placeholder.com/500x750?text=No+Poster'"
  alt="Movie Poster"
>
```

---

## ✅ Summary

### What You Get:
- ✅ **Movie ID** - Unique identifier (`tmdb_id`)
- ✅ **Poster URL** - High-quality image link
- ✅ **Backdrop URL** - Large background image
- ✅ **All metadata** - Title, rating, genres, year, etc.

### How It Works:
1. User asks for recommendations
2. RAG system searches vector DB
3. Returns movies **with poster URLs**
4. Frontend displays beautiful cards
5. User clicks → Full details with backdrop

### Display Options:
- 📱 **Mobile**: Small posters (w185)
- 💻 **Desktop**: Large posters (w500)
- 🖥️ **4K**: Original size
- 🎬 **Hero**: Full-width backdrops

### Integration Points:
- ✅ Vector search → Get movies with posters
- ✅ Graph queries → Enrich with relationships
- ✅ JSON format → Ready for any frontend
- ✅ Multiple sizes → Responsive design

**Your RAG system can now show beautiful movie posters when recommending films!** 🎬✨

---

## 🔗 References

- **Helper Functions**: Notebook Cell 13 (after preview cell)
- **Data Structure**: `crawled_data/movies_index.json`
- **Examples**: `crawled_data/preview.html`
- **Documentation**: This file

**Everything is ready to display movies with stunning visuals!** 🎨
