#!/usr/bin/python3

from os import path

import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst, Gtk

# Needed for window.get_xid(), xvimagesink.set_window_handle(), respectively:
from gi.repository import GdkX11, GstVideo


GObject.threads_init()
Gst.init(None)
filename = path.join(path.dirname(path.abspath(__file__)), 'MVI_5751.MOV')
uri = 'file://' + filename


class Player(object):
    def __init__(self):
        self.window = Gtk.Window()
        self.window.connect('destroy', self.quit)
        self.window.set_default_size(800, 450)

        self.drawingarea = Gtk.DrawingArea()
        self.window.add(self.drawingarea)

        # Create GStreamer pipeline
        self.pipeline = Gst.Pipeline()

        # Create bus to get events from GStreamer pipeline
        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect('message::eos', self.on_eos)
        self.bus.connect('message::error', self.on_error)

        # This is needed to make the video output in our DrawingArea:
        self.bus.enable_sync_message_emission()
        self.bus.connect('sync-message::element', self.on_sync_message)

        #
        # WEBCAM elements
        self.webcam = Gst.ElementFactory.make('v4l2src', "webcam")
        self.webcam.set_property("device", "/dev/video0")
        #
        self.webcam_caps = Gst.Caps.from_string("video/x-raw, width=(int)320, height=(int)240, format=(string)I420, framerate=(fraction)30/1")
        self.webcam_filter = Gst.ElementFactory.make("capsfilter", "webcam_filter")
        self.webcam_filter.set_property("caps", self.webcam_caps)
        #
        self.webcam_encoder=Gst.ElementFactory.make('x264enc', "webcam_encoder")
        self.webcam_encoder.set_property("speed_preset", "fast")
        #
        # GRABBER elements
        self.grabber = Gst.ElementFactory.make('v4l2src', "grabber")
        self.grabber.set_property("device", "/dev/video1")
        #
        self.grabber_caps_1 = Gst.Caps.from_string("video/x-raw, width=(int)1280, height=(int)1024, format=(string)YUY2, framerate=(fraction)30/1")
        self.grabber_filter_1 = Gst.ElementFactory.make("capsfilter", "grabber_filter_1")
        self.grabber_filter_1.set_property("caps", self.grabber_caps_1)
        #
        self.grabber_convert=Gst.ElementFactory.make('videoconvert', "grabber_convert")
        #
        self.grabber_caps_2 = Gst.Caps.from_string("video/x-raw, width=(int)1280, height=(int)1024, format=(string)I420, framerate=(fraction)30/1")
        self.grabber_filter_2 = Gst.ElementFactory.make("capsfilter", "grabber_filter_2")
        self.grabber_filter_2.set_property("caps", self.grabber_caps_2)
        
        self.grabber_encoder=Gst.ElementFactory.make('x264enc', "grabber_encoder")
        self.grabber_encoder.set_property("speed_preset", "fast")
        
        self.container=Gst.ElementFactory.make("mp4mux", "container")
        
        self.filesink = Gst.ElementFactory.make('filesink', "file_output")
        self.filesink.props.location="/home/briner/test.mp4"
        
        self.webcam_screen = Gst.ElementFactory.make('autovideosink', "webcam_screen")

        
        #
        # Add elements to the pipeline
        #self.pipeline.add(self.webcam)
        #self.pipeline.add(self.webcam_filter)
        #self.pipeline.add(self.webcam_encoder)
        #self.pipeline.add(self.container)
        #
        self.pipeline.add(self.grabber)
        self.pipeline.add(self.grabber_filter_1)
        self.pipeline.add(self.convert)
        self.pipeline.add(self.grabber_filter_2)
        self.pipeline.add(self.grabber_encoder)
        self.pipeline.add(self.container)
        self.pipeline.add(self.filesink)
#        self.pipeline.add(self.webcam_screen)
        
        # link them
        #self.webcam.link(self.webcam_filter)
        #self.webcam_filter.link(self.webcam_encoder)
        #self.webcam_encoder.link(self.container)
        #self.container.link(self.filesink)
        self.grabber.link(self.grabber_filter_1)
        self.grabber_filter_1.link(self.grabber_convert)
        self.grabber_convert.link(self.grabber_filter2)
        self.grabber_filter2.link(self.grabber_encoder)
        self.grabber_encoder.link(self.container)
        self.container.link(self.filesink)        


    def run(self):
        self.window.show_all()
        # You need to get the XID after window.show_all().  You shouldn't get it
        # in the on_sync_message() handler because threading issues will cause
        # segfaults there.
        self.xid = self.drawingarea.get_property('window').get_xid()
        self.pipeline.set_state(Gst.State.PLAYING)
        Gtk.main()
        
    def quit(self, window):
        self.pipeline.send_event(Gst.Event.new_eos())

    def on_sync_message(self, bus, msg):
        if msg.get_structure().get_name() == 'prepare-window-handle':
            print('prepare-window-handle')
            msg.src.set_window_handle(self.xid)

    def on_eos(self, bus, msg):
        print('on_eos(): seeking to start of video')
        self.pipeline.seek_simple(
            Gst.Format.TIME,        
            Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
            0
        )
        Gtk.main_quit()

    def on_error(self, bus, msg):
        print('on_error():', msg.parse_error())


p = Player()
p.run()
