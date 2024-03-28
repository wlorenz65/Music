import types, os, pickle, curses, re, androidhelper, struct, shutil, ftplib, random

droid = androidhelper.Android()

def prompt(title, message, ok, cancel=None):
  droid.dialogCreateAlert(title, message)
  droid.dialogSetPositiveButtonText(ok)
  if cancel:
    droid.dialogSetNegativeButtonText(cancel)
  droid.dialogShow()
  try: return droid.dialogGetResponse().result['which'] == "positive"
  except: return cancel

class Song(types.SimpleNamespace):
  track = 0
  chartpos = 0
  stars = -1
  lru = False
  todo = ""

  def path(self):
    track = f"{self.track:02d} " if self.track else ""
    chartpos = f"- {self.chartpos:03d} - " if self.chartpos else ""
    return f"{self.dir}/{track}{self.year} {chartpos}{self.artist} - {self.title}.mp3"

class Entry(types.SimpleNamespace):
  selected = False

class List(types.SimpleNamespace):
  query = ""
  selected = 0
  blockstart = None
  top = 0
  cursor = 0

  def __init__(self):
    self.entries = []

def dir_without_artist(s):
  a = s.artist
  if a.startswith("The "): a = a[4:]
  if s.dir.startswith(a):
    return re.sub(rf".{{{len(a)}}} (\d+ )?- ", "", s.dir)
  return s.dir

trans = str.maketrans("﹤﹥ː⧸⧹⼁？﹡", r'<>:/\|?*')
def draw():
  h = (height - 1) // 2
  l.cursor = max(0, min(l.cursor, len(l.entries) - 1))
  l.top = max(l.cursor - (h - 1), min(l.top, l.cursor))
  selected = f"({l.selected} selected) " if l.selected else ""
  blockstart = f"(blockstart at {l.blockstart}) " if l.blockstart != None else ""
  stdscr.addstr(0, 0, f"[{active}] {l.cursor}/{len(l.entries)} results {selected}{blockstart}for {repr(l.query):{width}}"[:width], curses.A_REVERSE)
  stdscr.refresh()
  for y in range(h):
    i = l.top + y
    if i >= len(l.entries):
      if y * 2 + 1 < height:
        stdscr.move(y * 2 + 1, 0)
        stdscr.clrtobot()
        stdscr.refresh()
      break
    e = l.entries[i]
    s = e.song
    if s.stars == -1:
      stdscr.addstr(y * 2 + 1, 1, " -1 ?", curses.color_pair(0x08))
    elif s.stars == 0:
      stdscr.addstr(y * 2 + 1, 1, "  0  ", curses.color_pair(0x08))
    else:
      stdscr.addstr(y * 2 + 1, 1, "*" * s.stars, curses.color_pair((None,4,6,2,3,9)[s.stars]) | curses.A_BOLD)
      stdscr.addstr(y * 2 + 1, 1 + s.stars, "*" * (5 - s.stars), curses.color_pair(0x08))
    attr = curses.color_pair(11 if e.selected else 7)
    stdscr.addstr(y * 2 + 1, 7, f"{s.title[:width-8]:{width-8}}".translate(trans), attr | curses.A_BOLD)
    m = f" {s.year} {s.artist} | {dir_without_artist(s)}".translate(trans)
    if s.chartpos: m += f" | {s.chartpos:03}"
    if s.track: m += f" | {s.track:02}"
    stdscr.addstr(y * 2 + 2, 1, f"{m[:width-2]:{width-2}}", attr)
    if s.todo:
      m = "Todo: " + s.todo + " "
      w = len(m) // 2
      stdscr.addstr(y * 2 + 1, width - w - 4, " | " + m[:w], attr)
      stdscr.addstr(y * 2 + 2, width - w - 4, " | " + m[w:w*2], attr)
    attr = curses.A_REVERSE if i == l.cursor else 0
    for x in 0, width - 1:
      stdscr.addch(y * 2 + 1, x, " ", attr)
      try: stdscr.addch(y * 2 + 2, x, " ", attr)
      except: pass
    stdscr.refresh()

def Up():
  l.cursor -= 1

def Down():
  l.cursor += 1

def PageUp():
  l.cursor -= height // 2 - 1

def PageDown():
  l.cursor += height // 2 - 1

def Home():
  l.cursor = 0

def End():
  l.cursor = 2e9

def Like():
  s.stars = min(s.stars + 1, 5)

def Unlike():
  s.stars = max(0, s.stars - 1)

def Info():
  m = ""
  fields = ["dir", "track", "year", "chartpos", "artist", "title", "size", "time", "md5sum", "stars"]
  for f in fields:
    if f in s.__dict__:
      m += f"{f} = {repr(s.__dict__[f])}\n"
  for k, v in s.__dict__.items():
    if k not in fields:
      m += f"{k} = {repr(v)}\n"
  prompt("Info", m, "Close")

def Todo():
  m = droid.dialogGetInput("Todo", "On archive disk:", s.todo).result
  if m:
    s.todo = m
  elif m == "" and s.todo:
    del s.todo

def ClearTodo():
  if not s.todo: return
  del s.todo
  l.cursor += 1

def Clear():
  global l
  l = lists[active] = List()

def Search():
  global l
  q = l.query
  error = ""
  while 1:
    q = droid.dialogGetInput("Search", "Search in s.path() with _=space or eval with fields=(s.dir, s.track, s.year, s.chartpos, s.artist, s.title, s.stars, s.todo)" + error, q).result
    if q == None: return
    l1 = List()
    if q:
      f = re.search(r"\bs\.(\w{3,})", q)
      if f:
        try:
          for s in songs:
            if eval(q):
              l1.entries.append(Entry(song=s))
          l1.entries.sort(key=lambda e: getattr(e.song, f.group(1)))
        except Exception as e:
          error = f"\n\n{e}"
          continue
      else:
        words = q.lower().split()
        for s in songs:
          p = s.path().lower().replace(" ", "_")
          for w in words:
            if w not in p: break
          else:
            l1.entries.append(Entry(song=s))
    break
  l1.query = q
  l = lists[active] = l1
  stdscr.clear() #curses bugfix

def Backspace():
  if l.cursor > 0: l.cursor -= 1
  l.selected -= l.entries[l.cursor].selected
  del l.entries[l.cursor]

def Delete():
  for i in reversed(range(len(l.entries))):
    if l.entries[i].selected:
      del l.entries[i]
      if i < l.cursor:
        l.cursor -= 1
  l.selected = 0

def id3tag(s):
  def frame(bid, str):
    bstr = b'\1' + str.encode("utf-16")
    return bid + struct.pack(">I", len(bstr)) + b'\0\0' + bstr
  frames = frame(b'TPE1', s.artist) + frame(b'TIT2', s.title)
  album = f"{s.year}"
  sep = s.dir.find(" - ")
  if sep != -1:
    album += " - " + s.dir[sep + 3:]
  elif s.chartpos:
    album += f" - {s.chartpos:03d}"
  frames += frame(b'TALB', album)
  size = len(frames)
  return b'ID3\3\0\0\0\0' + bytes([size >> 7 & 0x7F, size & 0x7F]) + frames

def Get():
  os.chdir("/storage/emulated/0/Music/")
  total, used, free = shutil.disk_usage(".")
  needed = sum(e.song.size for e in l.entries if e.selected)
  d = f"[{active}]"
  if not os.path.isdir(d): os.mkdir(d)
  os.chdir(d)
  tracknum = -1
  for f in os.listdir():
    if re.match(r"\d{3} .*\.mp3", f):
      tracknum = max(tracknum, int(f[:3]))
  if not prompt("Get from NAS", f"    {free/1e9:.1f} GB free before\n– {needed/1e9:.1f} GB needed for {l.selected} files\n= {(free-needed)/1e9:.1f} GB free afterwards\n\nStarting at tracknum {tracknum+1:03d}", "Ok", "Cancel"): return
  try:
    ftp = ftplib.FTP("192.168.178.1")
    ftp.login(user=..., passwd=...)
    ftp.sendcmd("OPTS UTF8 ON")
    ftp.encoding = "utf-8"
    ftp.cwd("D/Music")
    for i, e in enumerate(l.entries):
      if e.selected:
        l.cursor = i
        draw()
        s = e.song
        tracknum += 1
        name = f"{tracknum:03d} {s.year} {s.artist} - {s.title}.mp3"
        with open(name, "wb") as f:
          f.write(id3tag(s))
          ftp.retrbinary(f"RETR {s.path()}", f.write)
          #ftp.storbinary( 'STOR '+fileName, file)
        del e.selected
        l.selected -= 1
    ftp.quit()
  except Exception as e:
    prompt("Error", str(e), "Ok")

def select(a, b):
  if not l.entries: raise ValueError #debug
  if b < a: a,b = b,a
  b += 1
  s = sum(e.selected for e in l.entries[a:b]) <= (b - a) // 2
  for e in l.entries[a:b]:
    l.selected += s - e.selected
    e.selected = s
    if s and active != 0 and len(lists[0].entries) < 1000:
      lists[0].entries.append(Entry(song=e.song))

def Enter():
  select(l.cursor, l.cursor)
  l.cursor += 1

def Block():
  if l.blockstart == None:
    l.blockstart = l.cursor
  else:
    select(l.blockstart, l.cursor)
    l.blockstart = None

def SelectAll():
  select(0, len(l.entries) - 1)

def SelectDir():
  a = b = l.cursor
  while a > 0 and l.entries[a - 1].song.dir == s.dir:
    a -= 1
  while b < len(l.entries) - 1 and l.entries[b + 1].song.dir == s.dir:
    b += 1
  select(a, b)

def Random():
  os.chdir("/storage/emulated/0/Music/")
  total, used, free = shutil.disk_usage(".")
  leave = droid.dialogGetInput("Random", f"{free/1e9:.1f} GB available\nHow many GB leave free?" , ".6").result
  if leave == None: return
  leave = float(leave) * 1e9
  next = [9e99]
  weights = [None]
  lists = [None]
  for stars in range(1, 6):
    num_songs = 0
    lists.append([])
    for s in songs:
      if s.stars == stars:
        num_songs += 1
        if not s.lru:
          lists[stars].append(s)
    weights.append(1 / num_songs / (None, 1, 1, 2, 3, 7)[stars])
    next.append(weights[stars] / 2)
  plays = []
  while free > leave and len(plays) < 1000:
    stars = next.index(min(next))
    next[stars] += weights[stars]
    if not lists[stars]:
      for s in songs:
        if s.stars == stars:
          lists[stars].append(s)
          del s.lru
    s = random.choice(lists[stars])
    lists[stars].remove(s)
    plays.append(s)
    s.lru = True
    free -= s.size
  l.entries = [Entry(song=s) for s in plays]
  l.query = "random()"

def UpdateLRUs():
  if not prompt("Update", f"Update lru play counters for {l.selected} selected entries?", "Ok", "Cancel"): return
  for e in l.entries:
    if e.selected:
      s = e.song
      s.lru = True

def ClearBlockstart():
  l.blockstart = None

bindings = {
   curses.KEY_UP: Up,
   curses.KEY_DOWN: Down,
   curses.KEY_LEFT: PageUp,
   curses.KEY_RIGHT: PageDown,
   "h": Home,
   "e": End,
  "+": Like,
  "-": Unlike,
  "i": Info,
  "t": Todo,
  "T": ClearTodo,
  10: Enter,
  "b": Block,
  1: SelectAll,
  "d": SelectDir,
  curses.KEY_BACKSPACE: Backspace,
  "D": Delete,
  "g": Get,
  "u": UpdateLRUs,
}

def main(_stdscr):
  global stdscr, height, width, lists, active, l, e, s
  stdscr = _stdscr
  height, width = stdscr.getmaxyx()
  curses.curs_set(False)
  stdscr.keypad(True)
  for i in range(1, 256):
    curses.init_pair(i, i & 0x0F, i >> 4)
  l = lists[active]
  draw()
  while 1:
    e = s = None
    k = stdscr.getch()
    if k == 27: break
    elif chr(k) == "s": Search()
    elif chr(k) == "r": Random()
    elif chr(k) == "C": Clear()
    elif chr(k) == "B": ClearBlockstart()
    elif k >= 48 and k < 58:
      active = k - 48
      l = lists[active]
    elif l.entries:
      e = l.entries[l.cursor]
      s = e.song
      if k in bindings: bindings[k]()
      elif chr(k) in bindings: bindings[chr(k)]()
    try: draw()
    except: pass
    if 0: #debug
      if l.selected != sum([e.selected for e in l.entries]): raise ValueError

songfile = os.path.abspath("songs.pickle")
with open(songfile, "rb") as f:
  songs = pickle.load(f)

listfile = os.path.abspath("lists.pickle")
try:
  with open(listfile, "rb") as f:
    lists, active = pickle.load(f)
except FileNotFoundError:
  lists = [List() for _ in range(10)]
  active = 1

# restore song references
if 0: #debug
  lists[0].entries.append(Entry(song=Song(md5sum=None)))
on = 0
ol = set()
index = {s.md5sum:s for s in songs}
for li, l in enumerate(lists):
  for i, e in enumerate(l.entries):
    if e.song.md5sum in index:
      l.entries[i].song = index[e.song.md5sum]
    else:
      on += 1
      ol.add(li)
del index
if on:
  prompt("Orphans", f"{on} songs in lists {ol} are no longer in {songfile}", "Ok")

t = os.environ["TERM"] = "xterm-16color"
i = os.environ["TERMINFO"] = "/storage/emulated/0/qpython/terminfo"
ti = f"{i}/{t[0]}/{t}"
if not os.path.exists(ti):
  raise FileNotFoundError(f"{ti} is missing, copy this file from a Linux installation, usually found in /usr/share/terminfo")
curses.wrapper(main)

with open(listfile, "wb") as f:
  pickle.dump((lists, active), f)

with open(songfile, "wb") as f:
  pickle.dump(songs, f)
