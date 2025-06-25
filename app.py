import pickle
import streamlit as st
import requests
import time
from io import BytesIO
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
import os
import gdown

# ----------------------------
# ✅ Download .pkl files if not present
# ----------------------------
if not os.path.exists("movie_list.pkl"):
    print("⬇️ Downloading movie_list.pkl...")
    gdown.download("https://drive.google.com/uc?id=1njRyATrUwtdm-2e5EUuKG9n-BEQwVbvq", "movie_list.pkl", quiet=False)

if not os.path.exists("similarity.pkl"):
    print("⬇️ Downloading similarity.pkl...")
    gdown.download("https://drive.google.com/uc?id=1LVMYIfgMwS3QH8FYre7lSDqTgbgoLNvb", "similarity.pkl", quiet=False)

# ----------------------------
# ✅ Load pickle files safely
# ----------------------------
print("movie_list.pkl exists:", os.path.exists("movie_list.pkl"))
print("similarity.pkl exists:", os.path.exists("similarity.pkl"))

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
            image = Image.open(BytesIO(image_response.content))
            return image
        else:
            print(f"⚠️ No poster path for movie_id {movie_id}")
            return Image.new('RGB', (500, 750), color='gray')

    except Exception as e:
        print(f"❌ Error fetching poster for movie_id {movie_id}:", e)
        return Image.new('RGB', (500, 750), color='gray')


# ----------------------------
# 🎯 Recommendation Logic
# ----------------------------
def recommend(movie):
    print(f"🔍 Recommending for: {movie}")

    if movie not in movies['title'].values:
        print("❌ Movie not found in movie list!")
        return [], []

    index = movies[movies['title'] == movie].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])

    recommended_movie_names = []
    movie_ids = []

    for i in distances[1:6]:
        recommended_movie_names.append(movies.iloc[i[0]].title)
        movie_ids.append(movies.iloc[i[0]].movie_id)

    print(f"✅ Recommended: {recommended_movie_names}")

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
