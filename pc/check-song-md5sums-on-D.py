import types, hashlib, os, pickle, time

starttime = time.time()
minutes = 37
print("estimated runtime", minutes, "minutes, finished at", time.strftime("%H:%M", time.localtime(starttime + minutes * 60)))

class Song(types.SimpleNamespace):
  track = None
  chartpos = None

  def path(self):
    track = f"{self.track:02d} " if self.track else ""
    chartpos = f"- {self.chartpos:03d} - " if self.chartpos else ""
    return f"{self.dir}/{track}{self.year} {chartpos}{self.artist} - {self.title}.mp3"

  def read_md5sum(self):
    with open(self.path(), "rb") as file:
      self.md5sum = hashlib.md5(file.read()).hexdigest()

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
