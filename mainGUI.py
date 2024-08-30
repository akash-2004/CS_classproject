import datetime as dt
import threading
import webbrowser
from functools import partial
from tkinter import *
from dotenv import load_dotenv

import requests
import spotipy
from bs4 import BeautifulSoup
from spotipy.oauth2 import SpotifyOAuth
from tkcalendar import Calendar
import os




width_win = 480
height_win = 600

week_ago = dt.date.today() - dt.timedelta(days=7)  # As billboards can only be shown for a minimum of one week back
day = week_ago.day
month = week_ago.month
year = week_ago.year


# -----------------------------------------------Date brain-----------------------------------------------#
def get_date():
    date = cal.get_date().split("/")
    selected_year = f"{cal.get_displayed_month()[1]}"
    selected_month = f"{date[0]}"
    if len(date[1]) != 2:
        selected_day = f"0{date[1]}"
    else:
        selected_day = f"{date[1]}"

    if len(date[0]) != 2:
        selected_month = f"0{date[0]}"
    else:
        selected_month = f"{date[0]}"

    selected_date = f"{selected_year}-{selected_month}-{selected_day}"
    return selected_date


# -----------------------------------------------Playlist creation-----------------------------------------------#
def create_playlist(songs_list: list, travelled_back_to_date: str, listbox_item):
    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            scope="playlist-modify-private",
            redirect_uri="http://example.com",
            client_id=os.getenv('CLIENT_ID'),
            client_secret=os.getenv('CLIENT_SECRET'),
            show_dialog=True,
            cache_path=os.getenv('token')
        )
    )
    user_id = sp.current_user()["id"]
    print(user_id)

    # Searching Spotify for songs by title
    song_uris = []
    travelled_back_to_year = travelled_back_to_date.split("-")[0]
    num = 0
    listbox_item.delete(0, END)
    listbox_item.insert(0, "Obviously this will take some time...")
    listbox_item.insert(1, "Now, give us an A+ in the meantime")
    for song in songs_list:
        result = sp.search(q=f"{song} {travelled_back_to_year}", type="track")
        num += 1
        try:
            uri = result["tracks"]["items"][0]["uri"]
            song_uris.append(uri)
            listbox_item.insert(num + 1, f"success ({num}/{len(songs_list)})")
        except IndexError:
            listbox_item.insert(num + 1, f"{song} doesn't exist in Spotify. Skipped.")

    # Creating a new private playlist in Spotify
    playlist = sp.user_playlist_create(
        user=user_id, name=f"{travelled_back_to_date} Billboard 100", public=False)

    playlist_link = playlist['external_urls']['spotify']

    # Adding songs found into the new playlist
    sp.playlist_add_items(playlist_id=playlist["id"], items=song_uris)
    webbrowser.open(playlist_link)


def start_create_playlist_in_bg(songs_list: list, travelled_back_to_date: str, listbox_item):
    threading.Thread(target=create_playlist, args=(songs_list, travelled_back_to_date, listbox_item)).start()


# --------------------------------------------Second Window UI Setup--------------------------------------------#

def display_songs_list(songs_list: list, travelled_back_to_date: str):
    win = Tk()
    win.config(padx=50, pady=10)
    win.title(f"Billboard Hot 100 from {travelled_back_to_date}")
    can = Canvas(win, width=280, height=360)

    # listbox
    listb = Listbox(can, bd=3, width=50, height=20)
    for i in range(len(songs_list)):
        listb.insert(i, songs_list[i])
    listb.pack(side=LEFT, fill=BOTH)

    # scrollbar
    scrollbar = Scrollbar(can)
    scrollbar.pack(side=RIGHT, fill=BOTH)
    listb.config(yscrollcommand=scrollbar.set)
    scrollbar.config(command=listb.yview)

    can.grid(row=0, column=0, rowspan=2)
    # button for creating a playlist
    create_playlist_function_with_argument = partial(start_create_playlist_in_bg, songs_list, travelled_back_to_date,
                                                     listb)
    create_playlist_button = Button(win, text="Create a Spotify Playlist",
                                    command=create_playlist_function_with_argument)
    create_playlist_button.grid(row=2, column=0, columnspan=2)

    win.resizable(False, False)
    win.mainloop()


# --------------------------------------Web Scraping for top songs of that time--------------------------------------#
def get_songs():
    date_to_travel_back_to = get_date()
    if date_to_travel_back_to != "":
        response = requests.get(
            f"https://www.billboard.com/charts/hot-100/{date_to_travel_back_to}").text
        soup = BeautifulSoup(response, "html.parser")
        data = soup.find_all(name="h3",
                             class_="c-title a-no-trucate a-font-primary-bold-s u-letter-spacing-0021 "
                                    "lrv-u-font-size-18@tablet lrv-u-font-size-16 u-line-height-125 "
                                    "u-line-height-normal@mobile-max a-truncate-ellipsis u-max-width-330 "
                                    "u-max-width-230@tablet-only",
                             id="title-of-a-story")
        first_song = soup.find(name="h3",
                               class_="c-title a-no-trucate a-font-primary-bold-s u-letter-spacing-0021 "
                                      "u-font-size-23@tablet lrv-u-font-size-16 u-line-height-125 "
                                      "u-line-height-normal@mobile-max a-truncate-ellipsis u-max-width-245 "
                                      "u-max-width-230@tablet-only u-letter-spacing-0028@tablet",
                               id="title-of-a-story").text.strip()
        songs = [first_song]
        for item in data:
            songs.append(item.text.strip())
        display_songs_list(songs, travelled_back_to_date=date_to_travel_back_to)
    else:
        print("empty")


# -----------------------------------------------UI Setup-----------------------------------------------#
load_dotenv()
window = Tk()
window.title("Old is Billboard")
window.geometry("480x600")

window.config(padx=10, pady=50)

# background image
image_dj = PhotoImage(file="image.png")

# canvas = Canvas(width=width_win, height=height_win)
# canvas.grid(row=0, column=0, rowspan=2, columnspan=2)
# canvas.create_image(0, 0, image=image_dj, anchor=NW)

# Date picker
cal = Calendar(window, selectmode="day", year=year, month=month, day=day)
cal.grid(row=1, column=0, sticky="n", pady=20, padx=5, columnspan=2)

button1 = Button(window, text="Get Songs", command=get_songs).grid(row=2, column=0, pady=20, padx=5, sticky="n",
                                                                   columnspan=2)

# Text
main_text = Label(window, text="Which date would you like to travel back to (Atleast one week back)?",
                  font="Arial 10 bold", bg="white")
main_text.grid(row=0, column=0, sticky="n", columnspan=2, pady=(0, 20), padx=5)

window.resizable(False, False)
window.mainloop()
