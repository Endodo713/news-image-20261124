# The World in One Day — 24 November 2026

[![make.fun · news-image-20261124](https://make.fun/badge/news-image-20261124.svg)](https://make.fun/bounty/news-image-20261124?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)
[![rank](https://make.fun/badge/news-image-20261124/Endodo713/news-image-20261124/rank.svg)](https://make.fun/bounty/news-image-20261124/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)
[![reward](https://make.fun/badge/news-image-20261124/Endodo713/news-image-20261124/reward.svg)](https://make.fun/bounty/news-image-20261124?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)

A program that draws Tuesday 24 November 2026's world news as one
newspaper front page (1024x1024 PNG) and writes it to `/output/entry.png`.

Pure Python standard library: no network, no fonts, no images on disk.
The picture is drawn from scratch — a hand-made 5x7 bitmap font, flat
pictograms (Riyadh tower, Nvidia chip, warning triangle, ship, bar chart,
satellite, globe) — and two runs write byte-identical files.

26 stories: the Houthi drone strike on Riyadh's tallest tower leads, with
Nvidia bringing back Jensen Huang, Russia warning Estonia of open war,
Ukraine sinking a Russian corvette off Libya, the 700,000 Russian war
dead, NATO vowing to defend space, plus markets and 20 more of the day.

Run it with `mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py`.
