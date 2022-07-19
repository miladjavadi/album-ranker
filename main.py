# -*- coding: utf-8 -*-
"""
Created on Mon Jul 18 23:37:35 2022

@author: Milad
"""

import csv
import random

DEFAULT_RATING = 1200
ALBUM_LIST_CSV = "albums.csv"
K = 30
INITIAL_MATCHUPS = 10

class Album:
    def __init__(self, title, artist, rating):
        self.title = title
        self.artist = artist
        self.rating = rating
    
    def set_rating(self, new_rating):
        self.rating = round(new_rating)

def add_entry(title, artist):
    with open(ALBUM_LIST_CSV, 'a', newline='') as f:
        csv_writer = csv.writer(f, delimiter=",")
        csv_writer.writerow([title, artist, DEFAULT_RATING])

def expected_score(rating_a, rating_b):
    e_score = 1 / (1 + (10**((rating_b - rating_a) / 400)))
    return e_score

def rate_1v1(w, l):
    rating_w = w.rating
    rating_l = l.rating
    
    rating_w += K*(1-expected_score(rating_w, rating_l))
    rating_l += K*(-expected_score(rating_w, rating_l))
    
    return rating_w, rating_l

def rate_albums(album_list):
    
    n_matchups = int(input("Number of matchups: "))
        
    for i in range(n_matchups):
        print(f"\nMatchup {str(i+1)} of {n_matchups}\n")
        
        album_a, album_b = [random.sample(album_list, 2)[i] for i in [0, 1]]
        
        battle(album_a, album_b)

def battle(a, b):
    while(True):
        print(f"Which of these two albums do you prefer?\n\
1) {a.artist} -- {a.title}\n\
2) {b.artist} -- {b.title}\n\
3) Draw")
    
        choice = input()

        if choice == "1":
            new_rating_a, new_rating_b = rate_1v1(a, b)
            a.set_rating(new_rating_a)
            b.set_rating(new_rating_b)
            break
    
        elif choice == "2":
            new_rating_b, new_rating_a = rate_1v1(b, a)
            a.set_rating(new_rating_a)
            b.set_rating(new_rating_b)
            break
        
        elif choice == "3":
            break

def load_album_list():
    album_list = []
    with open(ALBUM_LIST_CSV, newline='') as f:
        csv_reader = csv.reader(f, delimiter=";")
        for row in csv_reader:
            list_entry = []
            for col in row:
                list_entry.append(col)
            
            album_list.append(Album(list_entry[0], list_entry[1], int(list_entry[2])))
    
    return album_list

def add_album(album_list):
    title = input("Album title (no semicolon): ")
    artist = input("Artist (no semicolon): ")
    new_album = Album(title, artist, DEFAULT_RATING)
    
    for i in range(INITIAL_MATCHUPS):
        print(f"\nMatchup {str(i+1)} of {INITIAL_MATCHUPS}\n")
        battle(new_album, random.choice(album_list))
    
    print("\n")
    
    return new_album

def list_albums(album_list):
    
    album_list.sort(key=lambda x: x.rating, reverse=True)
    
    print(f"\n\nAll rated albums ({len(album_list)}):\n")
    
    album_rank = 0
    
    for album in album_list:
        album_rank += 1
        print(f"{album_rank}. {album.artist} -- {album.title} [{album.rating}]")
    
    print("\n")
    
    
def preferences():
    print("\n")
    
def prepare_to_exit(album_list):
    album_list.sort(key=lambda x: x.rating, reverse=True)
    with open(ALBUM_LIST_CSV, 'w+', newline='') as f:
        csv_writer = csv.writer(f, delimiter=";")
        for album in album_list:
            csv_writer.writerow([album.title, album.artist, album.rating])
    
def main():
    updated = False
    
    album_list = load_album_list()
    
    while(True):
        print("\n")
        
        if updated is True:
            print("[!] You have unsaved changes to album data, select Save and exit (5) to save changes\n")
            
        print("1) Rate albums head-to-head\n\
2) Add new album\n\
3) List all rated albums\n\
4) Preferences\n\
5) Save and exit")
        
        choice = input()
    
        if choice == "1":
            rate_albums(album_list)
            updated = True
            
        elif choice == "2":
            album_list.append(add_album(album_list))
            updated = True
        
        elif choice == "3":
            list_albums(album_list)
            
        elif choice == "4":
            preferences()
            
        elif choice == "5":
            prepare_to_exit(album_list)
            break
        
main()