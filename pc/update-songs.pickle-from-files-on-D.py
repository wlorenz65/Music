# Either rename (artist, title) or modify (size, time)
# but not both at the same time. Otherwise you will get
# DEL+NEW which resets song likes and plays.

import types, os, re, hashlib, pickle

class Song(types.SimpleNamespace):
  track = None
  chartpos = None

  def path(self):
    track = f"{self.track:02d} " if self.track else ""
    chartpos = f"- {self.chartpos:03d} - " if self.chartpos else ""
    return f"{self.dir}/{track}{self.year} {chartpos}{self.artist} - {self.title}.mp3"

  def init_from_path(self, p):
    self.dir, p = os.path.split(p[:-4])
    if re.match(r"\d{2} ", p):
      self.track = int(p[:2])
      p = p[3:]
    if re.match(r"(19|20)\d\d ", p):
      self.year = int(p[:4])
      p = p[5:]
    if re.match(r"- \d{3} - ", p):
      self.chartpos = int(p[2:5])
      p = p[8:]
    sep = p.index(" - ")
    self.artist = p[:sep]
    self.title = p[sep+3:]

  def read_md5sum(self):
    with open(self.path(), "rb") as file:
      self.md5sum = hashlib.md5(file.read()).hexdigest()

musicdir = "/media/wlorenz65/D/Music/"
if not os.path.exists(musicdir):
  exit(musicdir, "not present")

songfile = os.path.abspath("songs.pickle")
with open(songfile, "rb") as f:
  old = pickle.load(f)
print(len(old), "entries read from", songfile)

os.chdir(musicdir)
unchanged = []
new = []
progress = 0
for root, dirnames, filenames in os.walk("."):
  for fn in filenames:
    progress += 1
    print(f"\r\033[36m{progress:5d}\033[m", end="")
    path = os.path.join(root[2:], fn)
    stat = os.stat(path)
    for o, s in enumerate(old):
      if s.path() == path and s.size == stat.st_size and s.time == stat.st_mtime_ns // 1_000_000_000:
        unchanged.append(s)
        del old[o]
        break
    else:
      if path.endswith(".mp3"):
        s = Song()
        s.init_from_path(path)
        s.size = stat.st_size
        s.time = stat.st_mtime_ns // 1_000_000_000
        new.append(s)
      else:
        print("what shall we do with", path)

renamed = []
for n in reversed(range(len(new))):
  for o in range(len(old)):
    if old[o].size == new[n].size and old[o].time == new[n].time:
      print(f"\n\033[33mREN {old[o].path()}\n -> {new[n].path()}\033[0m")
      for k in old[o].__dict__:
        if k not in ("dir", "track", "year", "chartpos", "artist", "title"):
          new[n].__dict__[k] = old[o].__dict__[k]
      renamed.append(new[n])
      del old[o], new[n]
      break

modified = []
for n in reversed(range(len(new))):
  for o in range(len(old)):
    if old[o].artist == new[n].artist and old[o].title == new[n].title:
      new[n].read_md5sum()
      print(f"\n\033[91mMOD {old[o].path()}\n{old[o]}\n{new[n]}\033[0m")
      if old[o].track: del old[o].track
      if old[o].chartpos: del old[o].chartpos
      old[o].__dict__.update(new[n].__dict__)
      modified.append(old[o])
      del old[o], new[n]
      break

for s in old:
  print(f"\n\033[34mDEL {s}\033[0m")

for s in new:
  s.read_md5sum()
  print(f"\n\033[32mNEW {s}\033[0m")

print()
print(len(unchanged), "unchanged")
print(len(renamed), "renamed")
print(len(modified), "modified")
print(len(old), "deleted")
print(len(new), "new")

if input(f"\nWrite {songfile} back to disk (y/N)? ").endswith("y"):
  songs = unchanged + renamed + modified + new
  songs.sort(key=lambda s: s.path())
  with open(songfile, "wb") as f:
    pickle.dump(songs, f)
  print("Written.")
else:
  print("Not written.")
