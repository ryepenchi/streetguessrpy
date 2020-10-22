# StreetGuessr
Guessing-Game for the streets of Vienna using **pygame**.
This was my first project after learning a bit of python
The original streetgraph and district shape data was downloaded from [data.wien.gv.at](https://www.data.gv.at/katalog/dataset/1039ed7e-97fb-435f-b6cc-f6a105ba5e09) in JSON format and pickled manually.
The images are from [basemap.at] or created using the OpenData.

####Features
- Experience a User Interface Nightmare
- Resolution is fixed to 1280x960

**How to use**:
1. cycle through zoom-levels with right-click
    or choose a base image layer in the top right
    Confirm with left-click
2. You are zoomed into your chosen area
    Confirm with left-lick
    Return with right-click
3. Count-down of 10s starts
    Left-click to draw polyline
    Right-click to confirm
4. See how far you were off
    after your guesses offset combine to 5k its Game over!
