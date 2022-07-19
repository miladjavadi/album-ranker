# -*- coding: utf-8 -*-
"""
Created on Mon Jul 18 23:37:35 2022

@author: Milad
"""

import csv
import random
import yaml

ALBUM_LIST_CSV = "albums.csv"
PREFERENCES_YAML = "preferences.yml"

DEFAULT_INITIAL_RATING = 1200
DEFAULT_K = 30
DEFAULT_CALIBRATION_MATCHUPS = 15
DEFAULT_PAGE_SIZE = 30

class Album:
    def __init__(self, title, artist, rating):
        self.title = title
        self.artist = artist
        self.rating = rating
    
    def set_rating(self, new_rating):
        self.rating = round(new_rating)

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
    
    n_matchups = int(input("Number of matchups: "))
        
    for i in range(n_matchups):
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

def load_album_list():
    album_list = []
    
    try:
        with open(ALBUM_LIST_CSV, newline='', encoding="utf8") as f:
            csv_reader = csv.reader(f, delimiter=";")
            for row in csv_reader:
                list_entry = []
                for col in row:
                    list_entry.append(col)
                
                album_list.append(Album(list_entry[0], list_entry[1], int(list_entry[2])))
            
            f.close()
    
    except FileNotFoundError:
        f = open(ALBUM_LIST_CSV, 'w')
        f.close()
    
    return album_list

def add_album(album_list, calibration_matchups=DEFAULT_CALIBRATION_MATCHUPS, initial_rating=DEFAULT_INITIAL_RATING, k=DEFAULT_K):
    title = input("Album title: ")
    artist = input("Artist: ")
    new_album = Album(title, artist, initial_rating)
    
    for i in range(min(calibration_matchups, len(album_list))):
        print(f"\nMatchup {str(i+1)} of {calibration_matchups}\n")
        battle(new_album, random.choice(album_list), k)
    
    print("\n")
    
    return new_album

def list_albums(album_list, page_size=DEFAULT_PAGE_SIZE):
    
    album_list.sort(key=lambda x: x.rating, reverse=True)
    
    sub_list = album_list[0:page_size]
    
    album_rank = 0
    
    print(f"\n\nAll rated albums ({len(album_list)}):\n")
    
    for album in album_list:
        album_rank += 1
        print(f"{album_rank}. {album.artist} -- {album.title} [{album.rating}]")
    
    print("\n")
    
def edit_preferences(preferences, album_list):
    
    while(True):
        print(f"\n1) Set initial rating ({preferences['initial_rating']})\n\
2) Set K-factor ({preferences['k']})\n\
3) Set no. calibration matchups ({preferences['calibration_matchups']})\n\
4) Reset all ratings to initial rating\n\
5) Delete all entries from file\n\
6) Reset default preferences\n\
7) Save and return to main menu\n")
    
        choice = input()
        
        print("\n")
        
        if choice == "1":
            preferences['initial_rating'] = int(input(f"Current initial rating: {preferences['initial_rating']}\n\nNew initial rating: "))
            
        elif choice == "2":
            preferences['k'] = int(input(f"Current K-factor: {preferences['k']}\n\nNew K-factor: "))
        
        elif choice == "3":
            preferences['calibration_matchups'] = int(input(f"Current no. calibration matchups: {preferences['calibration_matchups']}\n\nNew no. calibration matchups: "))
        
        elif choice == "4":
            print(f"Are you sure you want to reset all ratings to initial rating ({preferences['initial_rating']})?\n\
1) Yes\n\
<anything else>) No\n")
            
            choice = input()
            
            if choice == "1":
                for album in album_list:
                    album.set_rating(preferences['initial_rating'])
            
        elif choice == "5":
            print("Are you sure you want to delete all entries from file?\n\
1) Yes\n\
<anything else>) No\n")
            
            choice = input()
            
            if choice == "1":
                album_list = []
        
        elif choice == "6":
            print("Are you sure you want to reset default preferences?\n\
1) Yes\n\
<anything else>) No\n")
            
            choice = input()
            
            if choice == "1":
                preferences = {'initial_rating': DEFAULT_INITIAL_RATING, 'k': DEFAULT_K, 'calibration_matchups': DEFAULT_CALIBRATION_MATCHUPS}
                
        elif choice == "7":
            with open(PREFERENCES_YAML, 'w+') as f:
                yaml.dump(preferences, f)
            return preferences, album_list
    
def prepare_to_exit(album_list):
    album_list.sort(key=lambda x: x.rating, reverse=True)
    with open(ALBUM_LIST_CSV, 'w+', newline='', encoding="utf8") as f:
        csv_writer = csv.writer(f, delimiter=";")
        for album in album_list:
            csv_writer.writerow([album.title, album.artist, album.rating])
            
        f.close()

def config():
    try:
        preferences = yaml.safe_load(open(PREFERENCES_YAML))
    except FileNotFoundError:
        preferences = {'initial_rating': DEFAULT_INITIAL_RATING, 'k': DEFAULT_K, 'calibration_matchups': DEFAULT_CALIBRATION_MATCHUPS}
        with open(PREFERENCES_YAML, 'w') as f:
            yaml.dump(preferences, f)
    return preferences
    

def main():
    updated = False
    
    album_list = load_album_list()
    
    preferences = config()
    
    while(True):
        print("\n")
        
        if updated is True:
            print("[!] You have unsaved changes to album data, select Save and exit (5) to save changes\n")
            
        print("1) Rate albums head-to-head\n\
2) Add new album\n\
3) List all rated albums\n\
4) Preferences\n\
5) Save and exit\n")
        
        choice = input()
    
        if choice == "1":
            rate_albums(album_list, preferences['k'])
            updated = True
            
        elif choice == "2":
            album_list.append(add_album(album_list, preferences['calibration_matchups'], preferences['initial_rating'], preferences['k']))
            updated = True
        
        elif choice == "3":
            list_albums(album_list)
            
        elif choice == "4":
            preferences, album_list = edit_preferences(preferences, album_list)
            
        elif choice == "5":
            prepare_to_exit(album_list)
            break
        
main()
