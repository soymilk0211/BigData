#!/usr/bin/env bash
# rec.sh <scene>  record one terminal scene on DISPLAY :47
s=$1; export DISPLAY=:47; cd /workspace/bigdata-week11/rec
ffmpeg -loglevel error -y -f x11grab -video_size 1920x1080 -framerate 30 -draw_mouse 0 -i :47 -c:v libx264 -preset veryfast -crf 18 -pix_fmt yuv420p raw/$s.mp4 &
FF=$!
( for i in $(seq 1 50); do sleep 0.2; xdotool search --class xfce4-terminal >/dev/null 2>&1 && { xdotool search --class xfce4-terminal | while read w; do xdotool windowmove $w 0 0 windowsize $w 1920 900; done; break; }; done ) &
xfce4-terminal --disable-server --hide-menubar --hide-toolbar --hide-scrollbar --font "DejaVu Sans Mono 18" --title demo --geometry 134x31 -x bash -c "bash /workspace/bigdata-week11/rec/$s.sh; sleep 2.5" 2>/dev/null
kill -INT $FF; wait $FF 2>/dev/null
ffprobe -v error -show_entries format=duration -of csv=p=0 raw/$s.mp4
