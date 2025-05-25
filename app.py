# app.py - Main Flask application
from flask import Flask, render_template, request, redirect, url_for
import requests
from config import API_KEY

app = Flask(__name__)

# Base URL for OMDB API
OMDB_API_URL = "http://www.omdbapi.com/"

# Default poster URL for when no poster is available
DEFAULT_POSTER = "N/A"

@app.route('/')
def index():
    """Home page showing popular movies (predefined list since OMDB doesn't have a 'popular' endpoint)"""
    # Using a predefined list of popular movies since OMDB doesn't have a 'popular' endpoint
    popular_titles = ["Inception", "The Dark Knight", "Interstellar", "Pulp Fiction", 
                      "The Shawshank Redemption", "Avengers: Endgame", "The Matrix", "Fight Club"]
    
    movies = []
    for title in popular_titles:
        # Get movie details from API
        params = {
            "apikey": API_KEY,
            "t": title,
            "plot": "short",
            "r": "json"
        }
        response = requests.get(OMDB_API_URL, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("Response") == "True":
                # Format movie data
                movie = format_movie_data(data)
                movies.append(movie)
    
    return render_template('index.html', movies=movies)

@app.route('/search')
def search():
    """Search for movies by title"""
    query = request.args.get('query', '')
    
    if not query:
        return redirect(url_for('index'))
    
    # Search for movies matching the query
    params = {
        "apikey": API_KEY,
        "s": query,  # OMDB uses 's' parameter for search
        "r": "json",
        "type": "movie"
    }
    response = requests.get(OMDB_API_URL, params=params)
    
    movies = []
    if response.status_code == 200:
        data = response.json()
        if data.get("Response") == "True" and "Search" in data:
            results = data["Search"][:8]  # Get top 8 results
            
            # For each result, we need to make another API call to get full details
            for result in results:
                detail_params = {
                    "apikey": API_KEY,
                    "i": result["imdbID"],  # Using IMDB ID for accurate results
                    "plot": "short",
                    "r": "json"
                }
                detail_response = requests.get(OMDB_API_URL, params=detail_params)
                
                if detail_response.status_code == 200:
                    detail_data = detail_response.json()
                    if detail_data.get("Response") == "True":
                        movie = format_movie_data(detail_data)
                        movies.append(movie)
    
    return render_template('index.html', movies=movies, search_query=query)

@app.route('/movie/<imdb_id>')
def movie_detail(imdb_id):
    """Show details for a specific movie"""
    # Get movie details using IMDB ID
    params = {
        "apikey": API_KEY,
        "i": imdb_id,
        "plot": "full",  # Get full plot for the detail page
        "r": "json"
    }
    response = requests.get(OMDB_API_URL, params=params)
    
    movie = None
    recommendations = []
    
    if response.status_code == 200:
        data = response.json()
        if data.get("Response") == "True":
            movie = format_movie_data(data)
            
            # Since OMDB doesn't have a recommendations endpoint,
            # we'll search for movies with the same genre as a simple recommendation system
            if movie["genres"]:
                primary_genre = movie["genres"][0]["name"]  # Use the first genre
                
                # Search for movies with the same primary genre
                rec_params = {
                    "apikey": API_KEY,
                    "s": primary_genre,  # Using the genre as a search term
                    "type": "movie",
                    "r": "json"
                }
                rec_response = requests.get(OMDB_API_URL, params=rec_params)
                
                if rec_response.status_code == 200:
                    rec_data = rec_response.json()
                    if rec_data.get("Response") == "True" and "Search" in rec_data:
                        # Filter out the current movie from recommendations
                        rec_results = [r for r in rec_data["Search"] if r["imdbID"] != imdb_id][:4]
                        
                        # Get full details for each recommendation
                        for rec in rec_results:
                            detail_params = {
                                "apikey": API_KEY,
                                "i": rec["imdbID"],
                                "plot": "short",
                                "r": "json"
                            }
                            detail_response = requests.get(OMDB_API_URL, params=detail_params)
                            
                            if detail_response.status_code == 200:
                                detail_data = detail_response.json()
                                if detail_data.get("Response") == "True":
                                    rec_movie = format_movie_data(detail_data)
                                    recommendations.append(rec_movie)
    
    return render_template('movie.html', movie=movie, recommendations=recommendations)

def format_movie_data(data):
    """Format OMDB API data to match the template's expected structure"""
    # Process genres into the format expected by the template
    genres = []
    if "Genre" in data and data["Genre"] != "N/A":
        genre_list = data["Genre"].split(", ")
        genres = [{"name": genre} for genre in genre_list]
    
    # Calculate rating out of 10 (OMDB uses different rating systems)
    rating = 0
    if "imdbRating" in data and data["imdbRating"] != "N/A":
        rating = float(data["imdbRating"])
    
    # Format the movie data
    movie = {
        "id": data["imdbID"],
        "title": data["Title"],
        "release_date": data["Year"] + "-01-01" if data.get("Year", "N/A") != "N/A" else "",
        "overview": data.get("Plot", "No overview available"),
        "genres": genres,
        "vote_average": rating,
        "poster_url": data["Poster"] if data["Poster"] != "N/A" else None,
    }
    
    return movie

if __name__ == '__main__':
    app.run(debug=True)
