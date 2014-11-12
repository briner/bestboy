#!/usr/bin/python3

import gi
from gi.repository import GdkX11, GstVideo, GObject, Gst, Gtk

Gst.parse_launch('v4l2src device=${WEBCAM_DEVICE} \
        ! "video/x-raw, width=(int)320, height=(int)240, format=(string)I420, framerate=(fraction)30/1" \
        ! x264enc speed-preset=fast \
        ! mux. \
    v4l2src device=${GRABBER_DEVICE} \
        ! "video/x-raw, width=(int)1280, height=(int)1024, format=(string)YUY2, framerate=(fraction)30/1" \
        ! videoconvert \
        ! "video/x-raw, width=(int)1280, height=(int)1024, format=(string)I420, framerate=(fraction)30/1" \
        ! x264enc speed-preset=fast \
        ! mux. \
    pulsesrc \
        ! audioconvert \
        ! audio/x-raw, rate=44100, channels=2 \
        ! voaacenc \
        ! queue \
        ! mp4mux name=mux \
    mux. ! filesink location="genuine.mp4"')
