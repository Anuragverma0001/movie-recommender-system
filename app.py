import pickle
import streamlit as st
import requests
import time
from io import BytesIO
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
import os

# ----------------------------
# ✅ Helper to download files from Google Drive
# ----------------------------
def download_from_gdrive(file_id, destination):
    URL = "https://drive.google.com/uc?export=download"
    with requests.Session() as session:
        response = session.get(URL, params={'id': file_id}, stream=True)
        token = get_confirm_token(response)

        if token:
            response = session.get(URL, params={'id': file_id, 'confirm': token}, stream=True)

        save_response_content(response, destination)

    if os.path.exists(destination):
        size = os.path.getsize(destination)
        print(f"✅ Downloaded {destination} ({size} bytes)")
        if size < 5000:
            print(f"⚠️ Warning: {destination} might be corrupted (too small)")
    else:
        print(f"❌ Failed to download {destination}")

def get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value
    return None

def save_response_content(response, destination):
    CHUNK_SIZE = 32768
    with open(destination, "wb") as f:
        for chunk in response.iter_content(CHUNK_SIZE):
            if chunk:
                f.write(chunk)

# ----------------------------
# ✅ Download .pkl files if not present
# ----------------------------
if not os.path.exists("movie_list.pkl"):
    print("⬇️ Downloading movie_list.pkl...")
    download_from_gdrive("1njRyATrUwtdm-2e5EUuKG9n-BEQwVbvq", "movie_list.pkl")

if not os.path.exists("similarity.pkl"):
    print("⬇️ Downloading similarity.pkl...")
    download_from_gdrive("1LVMYIfgMwS3QH8FYre7lSDqTgbgoLNvb", "similarity.pkl")

# ----------------------------
# ✅ Load pickle files safely
# ----------------------------
try:
    with open("movie_list.pkl", "rb") as f:
        movies = pickle.load(f)
    print("✅ movie_list.pkl loaded")
except Exception as e:
    print("❌ Failed to load movie_list.pkl:", e)
    st.error("movie_list.pkl could not be loaded.")
    st.stop()

try:
    with open("similarity.pkl", "rb") as f:
        similarity = pickle.load(f)
    print("✅ similarity.pkl loaded")
except Exception as e:
    print("❌ Failed to load similarity.pkl:", e)
    st.error("similarity.pkl could not be loaded.")
    st.stop()

# ----------------------------
# 🎬 Function to fetch poster image
# ----------------------------
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
            image_response.raise_for_status()
            return Image.open(BytesIO(image_response.content))
        else:
            return Image.new('RGB', (500, 750), color='gray')

    except Exception as e:
        print(f"❌ Error fetching poster for movie_id {movie_id}: {e}")
        return Image.new('RGB', (500, 750), color='gray')

# ----------------------------
# 🎯 Recommendation Logic
# ----------------------------
def recommend(movie):
    if movie not in movies['title'].values:
        return [], []

    index = movies[movies['title'] == movie].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])

    recommended_movie_names = []
    movie_ids = []

    for i in distances[1:6]:
        recommended_movie_names.append(movies.iloc[i[0]].title)
        movie_ids.append(movies.iloc[i[0]].movie_id)

    with ThreadPoolExecutor() as executor:
        recommended_movie_posters = list(executor.map(fetch_poster, movie_ids))

    return recommended_movie_names, recommended_movie_posters

# ----------------------------
# 🌐 Streamlit Web App
# ----------------------------
st.header('🎬 Movie Recommender System')

movie_list = movies['title'].values
selected_movie = st.selectbox(
    "Type or select a movie from the dropdown",
    movie_list
)

if st.button('Show Recommendation'):
    recommended_movie_names, recommended_movie_posters = recommend(selected_movie)

    if recommended_movie_names:
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
    else:
        st.error("No recommendations found. Please try another movie.")
