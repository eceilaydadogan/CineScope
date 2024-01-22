import requests
from tkinter import Tk, Label, Frame, Canvas, Scrollbar, Entry, Button, messagebox, Toplevel, Text
from PIL import Image, ImageTk
import io
import pandas as pd


api_key = "6f7bf8466c96ec528bd87e5c321c7dc0"

endpoints = {
    'Sizin Icin Dunya Sinemasindan Sectiklerimiz': "https://api.themoviedb.org/3/movie/{}/similar",
    'Popüler Filmler': "https://api.themoviedb.org/3/movie/popular",
    'En Yüksek Puanlı Filmler': "https://api.themoviedb.org/3/movie/top_rated",
    'Vizyona Girecek Filmler': "https://api.themoviedb.org/3/movie/upcoming"
}

film_dic = {}
watch_later_list = []


def get_poster_image(url):
    response = requests.get(url)
    if response.status_code == 200:
        image_data = Image.open(io.BytesIO(response.content))
        image_data.thumbnail((100, 150), Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(image_data)
    else:
        print(f"Poster yüklenemedi: {response.status_code}")
        return None

#Film araması yapmak için TMDB API
def search_movie(movie_name):
    search_url = "https://api.themoviedb.org/3/search/movie"
    params = {'api_key': api_key, 'query': movie_name}
    response = requests.get(search_url, params=params)
    movies = response.json()['results']
    if movies:
        # İlk eşleşen filmin ID'si ve türleri alınır
        movie_id = movies[0]['id']
        movie_genres = get_movie_genres(movie_id)
        return pd.DataFrame(movies), movie_genres
    else:
        return pd.DataFrame(movies), []

#Bir film id'si verildiğinde o filmin türlerini döndüren fonksiyon
def get_movie_genres(movie_id):
    movie_url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    params = {'api_key': api_key}
    response = requests.get(movie_url, params=params)
    if response.status_code == 200:
        movie_info = response.json()
        return [genre['name'] for genre in movie_info['genres']]
    else:
        return []

#Belirli bir film adına göre benzer filmleri getiren fonksiyon
def get_similar_movies(movie_id, search_movie_genres):
    similar_url = f"https://api.themoviedb.org/3/movie/{movie_id}/similar"
    params = {'api_key': api_key}
    response = requests.get(similar_url, params=params)
    if response.status_code == 200:
        similar_movies = response.json()['results']
        filtered_movies = []

        for movie in similar_movies:
            movie_genres = get_movie_genres(movie['id'])
            if len(set(search_movie_genres) & set(movie_genres)) >= 2:
                filtered_movies.append(movie)

        if len(filtered_movies) < 12:
            for movie in similar_movies:
                if movie not in filtered_movies:
                    movie_genres = get_movie_genres(movie['id'])
                    if any(genre in search_movie_genres for genre in movie_genres):
                        filtered_movies.append(movie)
                        if len(filtered_movies) == 12:
                            break

        return pd.DataFrame(filtered_movies[:12])
    else:
        return pd.DataFrame([])


#Belirli bir endpoint'ten filmleri getiren fonksiyon
def get_movies_by_endpoint(endpoint):
    params = {'api_key': api_key}
    response = requests.get(endpoint, params=params)
    movies = response.json()['results'][:20]
    return pd.DataFrame(movies)

def get_movie_info(movie_id):
    movie_url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    params = {'api_key': api_key}
    response = requests.get(movie_url, params=params)
    if response.status_code == 200:
        movie_info = response.json()
        youtube_key = get_youtube_trailer_key(movie_id)
        return {
            'title': movie_info['title'],
            'genre': ', '.join([genre['name'] for genre in movie_info['genres']]),
            'overview': movie_info['overview'],
            'youtube_key': youtube_key,
            'poster_path': movie_info['poster_path']  # Poster path bilgisini ekle
        }
    else:
        print(f"Film bilgileri alınamadı: {response.status_code}")
        return {}



def get_youtube_trailer_key(movie_id):
    youtube_url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos"
    params = {'api_key': api_key}
    response = requests.get(youtube_url, params=params)
    if response.status_code == 200:
        videos = response.json()['results']
        for video in videos:
            if video['type'] == 'Trailer' and video['site'] == 'YouTube':
                return video['key']
    return None

def add_to_watch_later(movie_id):
    global watch_later_list
    if movie_id not in watch_later_list:
        if len(watch_later_list) >= 12:
            watch_later_list.pop(0)
        watch_later_list.append(movie_id)
        messagebox.showinfo("Başarılı", "Film, izleme listenize eklendi.")

def show_watch_later():
    watch_later_window = Toplevel()
    watch_later_window.title("İzleme Listem")
    watch_later_window.geometry("1920x260")

    canvas = Canvas(watch_later_window, bg='black')
    scrollbar = Scrollbar(watch_later_window, orient="horizontal", command=canvas.xview)
    scrollable_frame = Frame(canvas)

    canvas.configure(xscrollcommand=scrollbar.set)
    canvas.pack(side="bottom", fill="both", expand=True)
    scrollbar.pack(side="bottom", fill="x")
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    #Her film için bir frame oluştur ve onları yatay olarak sıralar
    for movie_id in watch_later_list:
        movie_info = get_movie_info(movie_id)
        if movie_info:
            movie_frame = Frame(scrollable_frame, bg='black', bd=2)
            movie_frame.pack(side="left", fill="y", expand=True, padx=20, pady=20)

            #Poster resmini yükleyip gösterir
            poster_path = f"https://image.tmdb.org/t/p/w500{movie_info['poster_path']}"
            poster_image = get_poster_image(poster_path)
            if poster_image:
                poster_label = Label(movie_frame, image=poster_image, bg='black')
                poster_label.image = poster_image
                poster_label.pack(side="top", fill="x", expand=True)

            title_label = Label(movie_frame, text=movie_info['title'], wraplength=100, bg='black', fg='white')
            title_label.pack(side="top")

    scrollable_frame.update()
    canvas.config(scrollregion=canvas.bbox("all"))

def show_movie_details(movie_id):
    movie_info = get_movie_info(movie_id)
    details_window = Toplevel()
    details_window.title("Film Detayları")

    genre_label = Label(details_window, text=f"Film Türü: {movie_info['genre']}")
    genre_label.pack()

    overview_frame = Frame(details_window)
    overview_scrollbar = Scrollbar(overview_frame)
    overview_scrollbar.pack(side="right", fill="y")

    overview_text = Text(overview_frame, wrap="word", yscrollcommand=overview_scrollbar.set, height=10, width=50)
    overview_text.insert("end", movie_info['overview'])
    overview_text.pack(side="left", fill="both", expand=True)
    overview_scrollbar.config(command=overview_text.yview)

    overview_frame.pack()

    if movie_info['youtube_key']:
        youtube_link = f"https://www.youtube.com/watch?v={movie_info['youtube_key']}"
        link_label = Label(details_window, text="Ilgili Filmin Fragmanını izle", fg="blue", cursor="hand2")
        link_label.pack()
        link_label.bind("<Button-1>", lambda e, link=youtube_link: open_youtube_link(link))
    else:
        no_trailer_label = Label(details_window, text="Ilgili filmin fragmanı bulunamadı")
        no_trailer_label.pack()

    watch_later_button = Button(details_window, text="Daha Sonra İzle", command=lambda: add_to_watch_later(movie_id))
    watch_later_button.pack(side="bottom", pady=5)

    details_window.geometry("400x230")

def open_youtube_link(link):
    import webbrowser
    webbrowser.open(link)

# Filmlerin posterlerini ve isimlerini gösteren fonksiyon
def show_movies_with_posters(movies_df, category_frame):
    for index, movie in movies_df.iterrows():
        # Poster URL'sini oluştur
        poster_path = movie['poster_path']
        full_poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"

        # Poster resmini yükleyip gösterir
        poster_image = get_poster_image(full_poster_url)
        poster_label = Label(category_frame, image=poster_image)
        poster_label.image = poster_image
        poster_label.grid(row=0, column=index, padx=10, pady=10)

        poster_label.bind("<Button-1>", lambda e, movie_id=movie['id']: show_movie_details(movie_id))

        title_label = Label(category_frame, text=movie['title'], wraplength=100)
        title_label.grid(row=1, column=index, padx=10, pady=10)

# Öneri butonuna basıldığında çağrılacak fonksiyon
def show_recommendations():
    searched_movie = film_dic['film_adı'].get()
    movie_results, search_movie_genres = search_movie(searched_movie)
    if not movie_results.empty:
        movie_id = movie_results.iloc[0]['id']
        similar_movies = get_similar_movies(movie_id, search_movie_genres)
        show_movies_window = Toplevel()
        show_movies_window.title("Film Önerileri")

        recommendation_title = f"İşte izleyebileceğiniz {searched_movie} benzeri filmler"
        title_label = Label(show_movies_window, text=recommendation_title, font=("Helvetica", 16))
        title_label.pack()

        similar_frame = Frame(show_movies_window)
        similar_frame.pack(fill="both", expand=True)

        show_movies_with_posters(similar_movies, similar_frame)
    else:
        messagebox.showinfo("Hata", "Film bulunamadı.")


def create_welcome_screen(root, image_path, show_main_app):
    #Pencere boyutlarını ayarlar
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.geometry(f'{screen_width}x{screen_height}+0+0')

    #Fotoğrafı arka plan olarak ayarlar
    welcome_image = Image.open(image_path)
    welcome_image = welcome_image.resize((screen_width, screen_height), Image.Resampling.LANCZOS)
    welcome_photo = ImageTk.PhotoImage(welcome_image)

    #Label widget'ına fotoğrafı yerleştir ve root'a referans olarak saklar
    welcome_label = Label(root, image=welcome_photo)
    welcome_label.image = welcome_photo
    welcome_label.place(x=0, y=0, relwidth=1, relheight=1)

    #Butonu konumlandirir
    enter_button = Button(welcome_label, text="Uygulamaya giriş yapmak için tıklayınız", command=lambda: [welcome_label.destroy(), show_main_app()], relief='raised', bd=4)
    enter_button.place(relx=0.65, rely=0.6, anchor='center')

# GUI arayüzü:
def create_interface(root):
    #Ana uygulama arayüzünü oluştur
    main_frame = Frame(root)

    #Filmi gireceği alanlar
    film_dic_frame = Frame(root)
    film_dic_frame.pack()

    Label(film_dic_frame, text="Film Adı:").grid(row=2, column=0)
    film_dic['film_adı'] = Entry(film_dic_frame)
    film_dic['film_adı'].grid(row=2, column=1)

    recommendations_button = Button(film_dic_frame, text="Öneri Al", command=show_recommendations)
    recommendations_button.grid(row=3, columnspan=2)

    watch_later_button = Button(film_dic_frame, text="İzleme Listem", command=show_watch_later)
    watch_later_button.grid(row=4, columnspan=2, pady=10)

    main_canvas = Canvas(root, bg="gray99")
    h_scrollbar = Scrollbar(root, orient="horizontal", command=main_canvas.xview)
    h_scrollbar.pack(side="bottom", fill="x")  # Pack horizontal scrollbar at the bottom
    v_scrollbar = Scrollbar(root, orient="vertical", command=main_canvas.yview)  # Dikey scrollbar ekle
    v_scrollbar.pack(side="right", fill="y")  # Pack vertical scrollbar on the right side
    main_canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)

    main_canvas.pack(side="left", fill="both", expand=True)  # Canvas fills remaining space

    scrollable_frame = Frame(main_canvas)

    #Tüm kategoriler için yatay düzeni kurar
    for category_name in endpoints.keys():

        category_frame = Frame(scrollable_frame)
        category_frame.pack(fill="x", expand=True)

        #Her kategori için bir başlık oluşturur ve konumalandirir
        category_label = Label(category_frame, text=category_name, font=("Helvetica", 16))
        category_label.pack()

        #Filmleri ve posterleri göstermek için iç içe bir frame daha oluşturur
        movies_frame = Frame(category_frame)
        movies_frame.pack(fill="both", expand=True)

        #Filmleri ve posterleri gösterir
        movies_df = get_movies_by_endpoint(endpoints[category_name].format('550'))
        show_movies_with_posters(movies_df, movies_frame)

    main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    main_canvas.pack(side="left", fill="both", expand=True)
    h_scrollbar.pack(side="bottom", fill="x")
    v_scrollbar.pack(side="right", fill="y")  # Dikey scrollbar'ı paketle

    #Scrollable frame'in genişliğini ayarlar
    scrollable_frame.bind("<Configure>", lambda e: main_canvas.config(scrollregion=main_canvas.bbox("all")))

    main_frame.pack(fill='both', expand=True)
    return main_frame

def main():
    root = Tk()
    root.title("Film Önerileri")

    # Ekranın tam boyutunu alir
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.geometry(f'{screen_width}x{screen_height}+0+0')

    welcome_image_path = 'karsilama.JPG'
    create_welcome_screen(root, welcome_image_path, lambda: create_interface(root))

    root.mainloop()

main()