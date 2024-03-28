# Music

License is CC0. Runs on QPython 3L on my Android tablet while VLC is playing in the background. Provides star ratings for each song with a single keypress [+] / [–]. In random mode, five-star songs get played 7× as often as two-star songs.

There is a todo field for each song which is available with the key [t], so that when the song is playing and I notice a bug, I can just quickly type in a few words to mark that song and fix it later on the master archive by pressing [s] for search and entering _s.todo_ as the query string. This means that bugs noticed while not at home won't be forgotten and there will never be a consistency problem in my music collection, because all changes will be made to the master archive. There are also no problems with wrong ID3Tags as Music.py will create them on the fly from file paths while copying a new bunch of songs for VLC from the master archive in random mode.

![Screenshot of Music.py running on my Android tablet](Screenshot.jpg)
