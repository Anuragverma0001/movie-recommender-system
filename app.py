import pickle
import streamlit as st
import requests
import time
from io import BytesIO
from PIL import Image
from concurrent.futures import ThreadPoolExecutor


# Function to fetch poster image

def fetch_poster(movie_id):
    bearer_token = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJjMjVkMmM1NGY2MzY2ZWNiMThjMmMwZDA1YmEwNTYyOCIsIm5iZiI6MTc1MDY2NDc5NC43ODgsInN1YiI6IjY4NTkwNjVhY2JmZTNkZjcwNmQxNTBkZSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.zDKaJjNGu88_zGiOB9tl9pHsH78q57LcD1lKO_zn1SE"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {bearer_token}"
    }
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?language=en-US"

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        poster_path = data.get('poster_path')

        if poster_path:
            image_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
            image_response = requests.get(image_url, timeout=10)
            image = Image.open(BytesIO(image_response.content))
            return image
        else:
            print(f"No poster path for movie_id {movie_id}")
            return Image.new('RGB', (500, 750), color='gray')  # Local fallback

    except Exception as e:
        print(f"Error fetching poster for movie_id {movie_id}: {e}")
        return Image.new('RGB', (500, 750), color='gray')  # Local fallback



# Function to recommend movies

def recommend(movie):
    index = movies[movies['title'] == movie].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])

    recommended_movie_names = []
    movie_ids = []

    for i in distances[1:6]:
        recommended_movie_names.append(movies.iloc[i[0]].title)
        movie_ids.append(movies.iloc[i[0]].movie_id)

    # Fetch posters in parallel
    with ThreadPoolExecutor() as executor:
        recommended_movie_posters = list(executor.map(fetch_poster, movie_ids))

    return recommended_movie_names, recommended_movie_posters




# Streamlit App Interface

st.header('🎬 Movie Recommender System')

# Load pickled data
movies = pickle.load(open('movie_list.pkl', 'rb'))
similarity = pickle.load(open('similarity.pkl', 'rb'))

# Movie selection dropdown
movie_list = movies['title'].values
selected_movie = st.selectbox(
    "Type or select a movie from the dropdown",
    movie_list
)

# Show recommendations
if st.button('Show Recommendation'):
    recommended_movie_names, recommended_movie_posters = recommend(selected_movie)

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.text(recommended_movie_names[0])
        st.image(recommended_movie_posters[0])
    with col2:
        st.text(recommended_movie_names[1])
        st.image(recommended_movie_posters[1])
    with col3:
        st.text(recommended_movie_names[2])
        st.image(recommended_movie_posters[2])
    with col4:
        st.text(recommended_movie_names[3])
        st.image(recommended_movie_posters[3])
    with col5:
        st.text(recommended_movie_names[4])
        st.image(recommended_movie_posters[4])
