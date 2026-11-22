[![make.fun · news-image-20261122](https://make.fun/badge/news-image-20261122.svg)](https://make.fun/bounty/news-image-20261122?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)
[![rank](https://make.fun/badge/news-image-20261122/romdhoncom/news-image-20261122/rank.svg)](https://make.fun/bounty/news-image-20261122/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)
[![reward](https://make.fun/badge/news-image-20261122/romdhoncom/news-image-20261122/reward.svg)](https://make.fun/bounty/news-image-20261122?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)

# Sunday 22 November 2026 in one image

A dense newspaper front page summing up Sunday 22 November 2026 in a
single 1024x1024 picture: 43 verified stories. Lead stories are the COP31
climate talks collapsing in Antalya with no deal, Mexico capturing cartel
boss 'El Chapo Isidro', Iran striking Bahrain and tankers near Hormuz, a
Russian missile killing two in Kryvyi Rih, and US markets falling into
correction on an AI sell-off. A world map pins 12 of the stories, and a
"More from Sunday" column carries the other 38, from the World Court's
Myanmar genocide ruling to college football chaos.

`main.py` is pure Python standard library: its own raster canvas, its own
5x7 bitmap font, and its own PNG encoder. No PIL, no network, no
randomness, no clock -- two runs write byte-identical files.

Run it with:

```
MAKEFUN_OUTPUT_DIR=/tmp/out python3 main.py
```

and it writes `/tmp/out/entry.png` (1024x1024, under 1 MiB).
