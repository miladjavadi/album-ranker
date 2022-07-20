# -*- coding: utf-8 -*-
"""
Created on Mon Jul 18 23:37:35 2022

@author: Milad
"""

import csv
import random
import yaml
from os import name, system 
import math
import spotipy
import requests

ALBUM_LIST_CSV = "albums.csv"
PREFERENCES_YAML = "preferences.yml" #yaml

DEFAULT_INITIAL_RATING = 1200
DEFAULT_K = 30
DEFAULT_CALIBRATION_MATCHUPS = 15
DEFAULT_PAGE_SIZE = 30

class Album:
    def __init__(self, rank, title, artist, rating):
        self.rank = rank
        self.title = title
        self.artist = artist
        self.rating = rating
    
    def set_rating(self, new_rating):
        self.rating = round(new_rating)
        
    def set_rank(self, rank):
        self.rank = rank

def expected_score(rating_a, rating_b):
    e_score = 1 / (1 + (10**((rating_b - rating_a) / 400)))
    return e_score

def rate_1v1(w, l, k=DEFAULT_K):
    rating_w = w.rating
    rating_l = l.rating
    
    rating_w += k*(1-expected_score(rating_w, rating_l))
    rating_l += k*(-expected_score(rating_w, rating_l))
    
    return rating_w, rating_l

def rate_albums(album_list, k=DEFAULT_K):
    
    clear_screen()
    
    n_matchups = int(input("\nNumber of matchups: "))
        
    for i in range(n_matchups):
        clear_screen()
        
        print(f"\nMatchup {str(i+1)} of {n_matchups}\n")
        
        album_a, album_b = [random.sample(album_list, 2)[i] for i in [0, 1]]
        
        battle(album_a, album_b)

def battle(a, b, k=DEFAULT_K):
    while(True):
        
        print(f"Which of these two albums do you prefer?\n\
1) {a.artist} -- {a.title}\n\
2) {b.artist} -- {b.title}\n\
3) Draw")
    
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

def add_album(album_list, calibration_matchups=DEFAULT_CALIBRATION_MATCHUPS, initial_rating=DEFAULT_INITIAL_RATING, k=DEFAULT_K):
    clear_screen()
    
    title = input("\nAlbum title: ")
    artist = input("Artist: ")
    new_album = Album(1, title, artist, initial_rating)
    
    for i in range(min(calibration_matchups, len(album_list))):
        clear_screen()
        
        print(f"\nMatchup {str(i+1)} of {calibration_matchups}\n")
        battle(new_album, random.choice(album_list), k)
    
    print("\n")
    
    return new_album

def list_albums(album_list, page_size=DEFAULT_PAGE_SIZE, searchable=True, title="Leaderboards:"): 
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
            print(f"{album.rank}. {album.artist} -- {album.title} [{album.rating}]")
        
        print(f"\nPage {page} of {n_pages}\n\n\
1) Previous page\n\
2) Next page\n\n\
3) First page\n\
4) Last page \n")
        
        if searchable:
            print("5) Return to main menu\n\n\
6) Search by title\n\
7) Search by artist\n\
8) Search by rank")
        
        else:
            print("5) Return")
        
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
    album_list.sort(key=lambda x: x.rating, reverse=True)
    with open(ALBUM_LIST_CSV, 'w+', newline='', encoding="utf8") as f:
        csv_writer = csv.writer(f, delimiter=";")
        for album in album_list:
            csv_writer.writerow([album.rank, album.title, album.artist, album.rating])
            
        f.close()

def config():
    try:
        preferences = yaml.safe_load(open(PREFERENCES_YAML))
    except FileNotFoundError:
        preferences = {'initial_rating': DEFAULT_INITIAL_RATING, 'k': DEFAULT_K, 'calibration_matchups': DEFAULT_CALIBRATION_MATCHUPS, 'page_size': DEFAULT_PAGE_SIZE}
        with open(PREFERENCES_YAML, 'w') as f:
            yaml.dump(preferences, f)
    return preferences
    
def sort_and_rank(album_list):
    album_list.sort(key=lambda x: x.rating, reverse=True)
    for album in album_list:
        album.set_rank(album_list.index(album)+1)
    
    return album_list

def clear_screen():
    if name == 'nt':
        _ = system('cls')
  
    else:
        _ = system('clear')

def search_leaderboards(album_list, key, page_size=DEFAULT_PAGE_SIZE):
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
    
def init_spotify():
    token_url = "https://accounts.spotify.com/authorize"
    method =  "GET"
    
    client_id = "cc8ff7b4b79d4b8b9be44854bdb9fbb3"
    response_type = "token"
    redirect_uri = "http://localhost:8888/callback"
    
    token_url += "?response_type=" + response_type
    token_url += "&client_id=" + client_id
    token_url += "&redirect_uri=" + redirect_uri
    
    r = requests.get(token_url)
    
    print(r)
    
def main():
    updated = False
    
    album_list = load_album_list()
    
    preferences = config()
    
    init_spotify()
    
    input()
    
    while(True):
        clear_screen()
        
        print("\n")
        
        if updated is True:
            print("[!] You have unsaved changes to album data, select Save and exit (5) to save changes\n")
            
        print("1) Rate albums head-to-head\n\
2) Add new album\n\
3) Leaderboards\n\
4) Preferences\n\
5) Save and exit\n")
        
        
        choice = input()
    
        if choice == "1":
            rate_albums(album_list, preferences['k'])
            album_list = sort_and_rank(album_list)
            updated = True
            
        elif choice == "2":
            album_list.append(add_album(album_list, preferences['calibration_matchups'], preferences['initial_rating'], preferences['k']))
            album_list = sort_and_rank(album_list)
            updated = True
        
        elif choice == "3":
            list_albums(album_list, preferences['page_size'])
            
        elif choice == "4":
            preferences, album_list = edit_preferences(preferences, album_list)
            
        elif choice == "5":
            prepare_to_exit(album_list)
            break
        
main()
