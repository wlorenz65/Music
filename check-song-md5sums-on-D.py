import types, hashlib, os, pickle, time

starttime = time.time()
minutes = 37
print("estimated runtime", minutes, "minutes, finished at", time.strftime("%H:%M", time.localtime(starttime + minutes * 60)))

class Song(types.SimpleNamespace):
  track = None

  def path(s):
    track_ = f"{s.track:02d} " if s.track else ""
    return f"{s.dir}/{track_}{s.year} {s.artist} - {s.title}.mp3"

  def read_md5sum(s):
    with open(s.path(), "rb") as file:
      s.md5sum = hashlib.md5(file.read()).hexdigest()

musicdir = "/media/wlorenz65/D/Music/"
if not os.path.exists(musicdir):
  exit(musicdir, "not present")

songfile = os.path.abspath("songs.pickle")
with open(songfile, "rb") as f:
  songs = pickle.load(f)
print(len(songs), "entries read from", songfile)

os.chdir(musicdir)
for i, s in enumerate(songs):
  print(f"\r\033[36m{i+1:5d}\033[m", end="")
  if not hasattr(s, "md5sum"):
    print("\nNO MD5SUM", s)
  else:
    oldsum = s.md5sum
    s.read_md5sum()
    if s.md5sum != oldsum:
      print("\nMD5SUM CHANGED", s)
print()

print("measured runtime", round((time.time() - starttime) / 60), "minutes")
