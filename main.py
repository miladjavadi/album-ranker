# -*- coding: utf-8 -*-
"""
Created on Mon Jul 18 23:37:35 2022

@author: Milad
"""

# from standard library
import csv
import random
from os import name, system
import math
import datetime
import json
from urllib.parse import urlencode, parse_qs
import sys
import string

# other packages
import requests
import yaml
from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtCore import *

# directories
ALBUM_LIST_CSV = "albums.csv"
PREFERENCES_YAML = "preferences.yml" #yaml
SPOTIFY_TOKEN_PATH = "spotify_token.json"

# spotify app client ID
CLIENT_ID = "cc8ff7b4b79d4b8b9be44854bdb9fbb3"

# some constants
DEFAULT_INITIAL_RATING = 1200 # sets default initial elo rating when adding albums
DEFAULT_K = 30 # sets default k-coefficient when adjusting rating
DEFAULT_CALIBRATION_MATCHUPS = 15 # sets default no. matchups for calibrating new album
DEFAULT_PAGE_SIZE = 30 # sets default no. entries per page in leaderboards
SEARCH_PAGE_SIZE = 7 # sets no. results per page when searching on spotify
MAX_SEARCH_RESULTS = 28 # sets max no. results when searching on spotify 

class Album:
    
    def __init__(self, rank, title, artist, rating):
        self.rank = rank
        self.title = title
        self.artist = artist
        self.rating = rating
    
    def set_rating(self, new_rating):
        self.rating = round(new_rating) # elo is rounded to nearest int
        
    def set_rank(self, rank):
        self.rank = rank
    
    def __str__(self):
        return f"{self.artist} -- {self.title}"
    
    def __bool__(self): # used for checking if a function returns an album instance
        return True 

class SpotifyLogin:
 
    # stores spotify token and user info
    
    def __init__(self):
        self.token=None
        self.expires=None # as POSIX timestamp
        self.account_name=None # spotify display name
    
    def as_dict(self):
        return {'access_token': self.token, 'expires': self.expires}

class ExpiredTokenError(Exception): # raise when token is invalid (i.e. expired)
    pass

class AuthError(Exception): # raise when spotify authorization is unsuccessful
    pass

def expected_score(rating_a, rating_b):
    
    # returns elo expected score (win prob. + draw prob./2)
    
    e_score = 1 / (1 + (10**((rating_b - rating_a) / 400)))
    return e_score

def rate_1v1(w, l, k=DEFAULT_K):
    
    # returns adjusted elo after matchup
    
    rating_w = w.rating # old rating of winner
    rating_l = l.rating # old rating of loser
    
    rating_w += k*(1-expected_score(rating_w, rating_l))
    rating_l += k*(-expected_score(rating_w, rating_l))
    
    return rating_w, rating_l

def rate_albums(album_list, k=DEFAULT_K):
    
    # performs a number of matchups between random albums
    
    clear_screen()
    
    n_matchups = int(input("\nNumber of matchups: "))
        
    for i in range(n_matchups):
        clear_screen()
        
        print(f"\nMatchup {str(i+1)} of {n_matchups}")
        
        album_a, album_b = [random.sample(album_list, 2)[i] for i in [0, 1]]
        
        battle(album_a, album_b)

def battle(a, b, k=DEFAULT_K):
    
    # performs a single matchup between two albums
    
    while(True):
        
        print(f"\nWhich of these two albums do you prefer?\n\
1) {a}\n\
2) {b}\n\
3) Draw\n")
    
        choice = input()

        if choice == "1":
            new_rating_a, new_rating_b = rate_1v1(a, b, k)
            a.set_rating(new_rating_a)
            b.set_rating(new_rating_b)
            break
    
        elif choice == "2":
            new_rating_b, new_rating_a = rate_1v1(b, a, k)
            a.set_rating(new_rating_a)
            b.set_rating(new_rating_b)
            break
        
        elif choice == "3":
            break
        
        clear_screen()

def load_album_list():
    
    # loads in list of albums from file as list of album objects
    
    album_list = []
    
    try:
        with open(ALBUM_LIST_CSV, newline='', encoding="utf8") as f:
            csv_reader = csv.reader(f, delimiter=";")
            for row in csv_reader:
                list_entry = []
                for col in row:
                    list_entry.append(col)
                
                album_list.append(Album(int(list_entry[0]), list_entry[1], list_entry[2], int(list_entry[3])))
            
            f.close()
    
    except (FileNotFoundError, IndexError):
        f = open(ALBUM_LIST_CSV, 'w')
        f.close()
    
    album_list = sort_and_rank(album_list)
    
    return album_list

def add_album(album_list, calibration_matchups=DEFAULT_CALIBRATION_MATCHUPS, initial_rating=DEFAULT_INITIAL_RATING, k=DEFAULT_K, spotify_client_is_ready=False, spotify_token=None):
    
    # finds a new album and adds to list
    
    clear_screen() 
    
    print("\n1) Search for album on Spotify\n\
2) Add album manually\n\
3) Return to main menu\n")
    
    choice = input()
    
    while(True):
        if choice == "1":
            if not spotify_client_is_ready:
                clear_screen()
                
                input("\nYou are not signed in with Spotify. Please sign in from main menu.")
                raise AuthError
                
            else:
                title, artist = search_album_spotify(spotify_token)
                break
        
        elif choice == "2":
            title, artist = manual_album_input()
            break
        
        elif choice == "3":
            return False
        
    new_album = Album(1, title, artist, initial_rating)
        
    for i in range(min(calibration_matchups, len(album_list))):
        clear_screen()
        
        print(f"\nMatchup {str(i+1)} of {calibration_matchups}")
        battle(new_album, random.choice(album_list), k)
    
    print("\n")
    
    album_list.append(new_album)
    
    return True

def search_album_spotify(access_token):
    
    # uses spotify search engine to find album based on user input query
    
    while(True):
        clear_screen()
        
        query = input("\nSearch for album on Spotify: ")
        
        header = {"Authorization": f"Bearer {access_token}"}
        endpoint = "https://api.spotify.com/v1/search"
        data = urlencode({"q": query, "type": "album", "limit": MAX_SEARCH_RESULTS})
        
        lookup_url = f"{endpoint}?{data}"
        
        r = requests.get(lookup_url, headers=header)
        
        r_dic = r.json()
        
        result_list = []
        
        if r.status_code in range(200, 299):
            for album in r_dic['albums']['items']:
                title = album['name']
                artist = join_multiple_artists([x['name'] for x in album['artists']])
                result_list.append(Album(1, title, artist, 0))
        
        selected_album = select_from_search_results(result_list, query)
        
        if selected_album:
            break
        
        else:
            pass
    
    return selected_album.title, selected_album.artist
    
def select_from_search_results(album_list, query):
    
    # displays spotify search results and returns selected album
    
    page_size = SEARCH_PAGE_SIZE
    
    page = 1
    n_pages = math.ceil(len(album_list)/page_size)
    
    while(True):
        clear_screen()
        
        if page < page_size: 
            sub_list = album_list[(page-1)*page_size:page*page_size]
        
        else:
            sub_list = album_list[(page-1)*page_size:]
            
        print(f"\nResults for '{query}':\n")
        
        for album in sub_list:
            print(f"{str(sub_list.index(album)+1)}) {album}\n")
        
        print(f"\nPage {page}/{n_pages}\n\n\
8) Previous page\n\
9) Next page\n\n\
0) Cancel\n")
    
        choice = input()
        
        if choice in [str(x) for x in range(1, 8)]:
            selected_album = sub_list[int(choice)-1]
            return selected_album
        
        elif choice == "8":
            page = max(1, page-1)
            
        elif choice == "9":
            page = min(n_pages, page+1)
        
        elif choice == "0":
            return False

def manual_album_input():
    
    # adds new album to list manually
    
    clear_screen()
    
    title = input("\nAlbum title: ")
    artist = input("Artist: ")
    
    return title, artist

def list_albums(album_list, page_size=DEFAULT_PAGE_SIZE, searchable=True, title="Leaderboards:"): 
    
    # displays leaderboards
    
    page = 1
    n_pages = math.ceil(len(album_list)/page_size)
    
    while(True):
        clear_screen()
        
        if page < page_size: 
            sub_list = album_list[(page-1)*page_size:page*page_size]
        
        else:
            sub_list = album_list[(page-1)*page_size:]
        
        print(f"\n{title}\n")
        
        for album in sub_list:
            print(f"{album.rank}. {album} [{album.rating}]")
        
        print(f"\nPage {page} of {n_pages}\n\n\
1) Previous page\n\
2) Next page\n\n\
3) First page\n\
4) Last page \n")
        
        if searchable:
            print("5) Return to main menu\n\n\
6) Search by title\n\
7) Search by artist\n\
8) Search by rank\n")
        
        else:
            print("5) Return\n")
        
        choice = input()
        
        if choice == "1":
            page = max(1, page-1)
        
        elif choice == "2":
            page = min(n_pages, page+1)
        
        elif choice == "3":
            page = 1
        
        elif choice == "4":
            page = n_pages
            
        elif choice == "5":
            return
        
        if searchable:
            if choice == "6":
                search_leaderboards(album_list, 'title', page_size)
            
            elif choice == "7":
                search_leaderboards(album_list, 'artist', page_size)
            
            elif choice == "8":
                search_leaderboards(album_list, 'rank', page_size)
    
def edit_preferences(preferences, album_list):
    
    # display settings menu where user can adjust different parameters
    
    while(True):
        clear_screen()
        
        print(f"\n1) Set initial rating ({preferences['initial_rating']})\n\
2) Set K-factor ({preferences['k']})\n\
3) Set no. calibration matchups ({preferences['calibration_matchups']})\n\
4) Set leaderboard page size ({preferences['page_size']})\n\
5) Reset all ratings to initial rating\n\
6) Delete all entries from file\n\
7) Reset default preferences\n\
8) Save and return to main menu\n")
    
        choice = input()
        
        clear_screen()
        
        if choice == "1":
            try:
                preferences['initial_rating'] = int(input(f"\nCurrent initial rating: {preferences['initial_rating']}\n\nNew initial rating: "))
            except ValueError:
                pass
            
        elif choice == "2":
            try:
                preferences['k'] = int(input(f"\nCurrent K-factor: {preferences['k']}\n\nNew K-factor: "))
            except ValueError:
                pass
        
        elif choice == "3":
            try:
                preferences['calibration_matchups'] = int(input(f"\nCurrent no. calibration matchups: {preferences['calibration_matchups']}\n\nNew no. calibration matchups: "))
            except ValueError:
                pass
        
        elif choice == "4":
            try:
                preferences['page_size'] = int(input(f"\nCurrent leaderboard page size: {preferences['page_size']}\n\nNew leaderboard page size: "))
            except ValueError:
                pass
        
        elif choice == "5": 
            print(f"\nAre you sure you want to reset all ratings to initial rating ({preferences['initial_rating']})?\n\
1) Yes\n\
<anything else>) No\n")
            
            choice = input()
            
            if choice == "1":
                for album in album_list:
                    album.set_rating(preferences['initial_rating'])
            
        elif choice == "5":
            print("\nAre you sure you want to delete all entries from file?\n\
1) Yes\n\
<anything else>) No\n")
            
            choice = input()
            
            if choice == "1":
                album_list = []
        
        elif choice == "7":
            print("\nAre you sure you want to reset default preferences?\n\
1) Yes\n\
<anything else>) No\n")
            
            choice = input()
            
            if choice == "1":
                preferences = {'initial_rating': DEFAULT_INITIAL_RATING, 'k': DEFAULT_K, 'calibration_matchups': DEFAULT_CALIBRATION_MATCHUPS, 'page_size': DEFAULT_PAGE_SIZE}
                
        elif choice == "8":
            with open(PREFERENCES_YAML, 'w+') as f:
                yaml.dump(preferences, f)
            return preferences, album_list
    
def prepare_to_exit(album_list):
    
    # saves album list to file and clears screen
    
    album_list.sort(key=lambda x: x.rating, reverse=True)
    with open(ALBUM_LIST_CSV, 'w+', newline='', encoding="utf8") as f:
        csv_writer = csv.writer(f, delimiter=";")
        for album in album_list:
            csv_writer.writerow([album.rank, album.title, album.artist, album.rating])
            
        f.close()
    
    clear_screen()

def config():
    
    # loads user preferences
    
    try:
        preferences = yaml.safe_load(open(PREFERENCES_YAML))
    except FileNotFoundError:
        preferences = {'initial_rating': DEFAULT_INITIAL_RATING, 'k': DEFAULT_K, 'calibration_matchups': DEFAULT_CALIBRATION_MATCHUPS, 'page_size': DEFAULT_PAGE_SIZE}
        with open(PREFERENCES_YAML, 'w') as f:
            yaml.dump(preferences, f)
    return preferences
    
def sort_and_rank(album_list):
    
    # sorts album list by elo rating
    
    album_list.sort(key=lambda x: x.rating, reverse=True)
    for album in album_list:
        album.set_rank(album_list.index(album)+1)
    
    return album_list

def clear_screen():
    
    # clears the terminal window
    
    # windows
    if name == 'nt':
        _ = system('cls')
    
    # unix
    else:
        _ = system('clear')

def search_leaderboards(album_list, key, page_size=DEFAULT_PAGE_SIZE):
    
    # filters the leaderboards by different parameters
    
    clear_screen()
    
    query = input(f"\nSearch for {key}: ")
    
    match_list = []
    
    if key == 'title':
        for album in album_list:
            if query.casefold() in album.title.casefold(): 
                match_list.append(album)
    
    elif key == 'artist':
        for album in album_list:
            if query.casefold() in album.artist.casefold(): 
                match_list.append(album)
    
    elif key == 'rank':
        for album in album_list:
            if int(query) == album.rank:
                match_list.append(album)
    
    list_albums(match_list, searchable=False, page_size=page_size, title=f"\nAlbums with {key} matching '{query}':")

def log_in_to_spotify(login):
    
    # prompts user to log into spotify
    
    now_dt = datetime.datetime.now()
    now = datetime.datetime.timestamp(now_dt)
    
    token_still_valid = auto_login(login)
        
    if not token_still_valid:
        try:
            app = QApplication(sys.argv)
            QApplication.setApplicationName('Sign in with Spotify')
            window = QMainWindow()
            
            window.browser = QWebEngineView()
            
            
            endpoint = "https://accounts.spotify.com/authorize"
            
            client_id = CLIENT_ID
            response_type = "token"
            redirect_URI = "http://localhost:8888/"
            scope = ""
            state = generate_random_string(16)
            
            request_data = urlencode({'response_type': response_type, 'client_id': client_id, 'scope': scope, 'redirect_uri': redirect_URI, 'state': state})
            
            lookup_url = f"{endpoint}?{request_data}"
            
            lookup_url = f"{endpoint}?{request_data}"        
            window.browser.setUrl(QUrl(lookup_url))
            
            window.setCentralWidget(window.browser)
            window.setGeometry(0, 0, 600, 800)
            
            window.browser.urlChanged.connect(lambda: update_url(window.browser.url(), login, now))
            window.browser.urlChanged.connect(lambda: window.close())
            
            window.show()
            
            app.exec()
            
            header = {"Authorization": f"Bearer {login.token}"}
            endpoint = "https://api.spotify.com/v1/me"
            
            r = requests.get(endpoint, headers=header)
            
            r_dic = r.json()
            
            if r.status_code in range(200, 299):
                login.name = r_dic['display_name']
                return True
            
            else:
                raise AuthError
            
        except AuthError:
            return False
    
    else:
        return True

def update_url(url, login, now):
    
    # slot for when url in browser is updated
    
    url_str = url.toString()
    if "http://localhost:8888/" in url_str:
        if "access_token=" in url_str:            
            queries = parse_qs(url_str.split("#")[1])
            
            print(queries)
            
            login.token = queries['access_token'][0]
            login.expires = now + int(queries['expires_in'][0])
            
            with open(SPOTIFY_TOKEN_PATH, 'w+') as f:
                json.dump(login.as_dict(), f)
            
        else:
            raise AuthError
    
def generate_random_string(length=16, alphabet="letters"):
    
    # generate a random string of given length using alphabet as character set
    
    if alphabet == "lowercase":
        letters = string.ascii_lowercase
    elif alphabet == "uppercase":
        letters = string.ascii_uppercase
    elif alphabet == "letters":
        letters = string.ascii_letters
    elif alphabet == "digits":
        letters = string.digits
    elif alphabet == "punctuation":
        random_string = string.punctuation
    elif alphabet == "whitespace":
        alphabet == string.whitespace
    elif alphabet == "printable":
        alphabet == string.printable
    else:
        raise ValueError(f"'{alphabet}' is not a valid character set")
        
    random_string = ''.join(random.choice(letters) for i in range(length))
    return random_string
    
def auto_login(login, now=datetime.datetime.timestamp(datetime.datetime.now())):
    
    # attempts to log in to spotify using previously granted token
    
    try:
        with open(SPOTIFY_TOKEN_PATH, 'r') as f:
            token_and_expiration = json.load(f)
            f.close()
        
        login.token = token_and_expiration['access_token']
        login.expires = token_and_expiration['expires']
        
        if login.expires < now:
            raise ExpiredTokenError
    
    except (ExpiredTokenError, FileNotFoundError, json.decoder.JSONDecodeError):
        return False
    
    try:
        header = {"Authorization": f"Bearer {login.token}"}
        endpoint = "https://api.spotify.com/v1/me"
        
        r = requests.get(endpoint, headers=header)
        
        r_dic = r.json()
        
        if r.status_code in range(200, 299):
            login.name = r_dic['display_name']
        
        elif r.status_code == 401:
            raise ExpiredTokenError
        
        else:
            raise AuthError
    
    except (AuthError, ExpiredTokenError):
        return False
    
    return True

def join_multiple_artists(artist_list):
    
    # strings together list of artist names 
    
    if len(artist_list) > 3:
        return "Various Artists"
    
    else:
        return ", ".join(artist_list)
        
# def show_recommendations(album_list, spotify_token, spotify_client_is_ready=True):
#     top_albums = album_list[:29]
    
#     top_elos = {}
    
#     for album in top_albums:
#         if album.artist not in top_elos:
#             top_elos[album.artist] = album.rating
#         else:
#             top_elos[album.artist] += album.rating

def main():
    updated = False
    
    album_list = load_album_list()
    
    preferences = config()
    
    spotify_login = SpotifyLogin()
    
    spotify_client_is_ready = auto_login(spotify_login)
    
    while(True):
        clear_screen()
        
        if updated is True:
            print("\n[!] You have unsaved changes to album data, select Save and exit (5) to save changes")
            
        print("\n1) Rate albums head-to-head\n\
2) Add new album\n\
3) Leaderboards\n\
4) Preferences\n\
5) Save and exit\n")
    
        if spotify_client_is_ready:
            print(f"Signed in as {spotify_login.name}. Welcome back!\n")
            
        else:
            print("6) Sign in with Spotify\n")
        
        choice = input()
    
        if choice == "1":
            rate_albums(album_list, preferences['k'])
            album_list = sort_and_rank(album_list)
            updated = True
            
        elif choice == "2":
            try:
                if add_album(album_list, preferences['calibration_matchups'], preferences['initial_rating'], preferences['k'], spotify_client_is_ready, spotify_login.token):
                    album_list = sort_and_rank(album_list)
                    updated = True
            except AuthError:
                pass
        
        elif choice == "3":
            list_albums(album_list, preferences['page_size'])
            
        elif choice == "4":
            preferences, album_list = edit_preferences(preferences, album_list)
        
        # elif choice == "5":
        #     show_recommendations(album_list, spotify_token, spotify_client_is_ready)
        
        elif choice == "5":
            prepare_to_exit(album_list)
            return
        
        elif choice == "6" and not spotify_client_is_ready:
            clear_screen()
            print("\nSigning in, please follow instructions in browser window...")
            spotify_client_is_ready = log_in_to_spotify(spotify_login)
        
main()
