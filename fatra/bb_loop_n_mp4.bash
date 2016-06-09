rm -f ~/bestboy/test.mp4


GRABBER_DEVICE=$(v4l2-ctl --list-devices \
                | grep -A1 "VisionRGB-E1S" \
                | tail -1 \
                | sed -r "s|\s*||")
WEBCAM_DEVICE=$(v4l2-ctl --list-devices \
                | grep -A1 "HD Pro Webcam C920" \
                | tail -1 \
                | sed -r "s|\s*||")

RESOLUTION=$(v4l2-ctl --all -d ${GRABBER_DEVICE} | grep -w "Width/Height" | sed "s|.*: ||")
DST=/home/briner/bestboy/test.mp4

if [[ -z ${WEBCAM_DEVICE} ]]; then
    echo "No webcam device found."
    echo "Exit !"
    exit 1
fi

if [[ -z ${GRABBER_DEVICE} ]]; then
    echo "No grabber device found."
    echo "Exit !"
    exit 1
fi

if [[ ${RESOLUTION} != "1024/768" ]]; then
  echo "Resolution must be 1024x768 not ${RESOLUTION}"
  echo "Exit !"
  exit 1
fi

gst-launch-1.0 -e \
  videomixer name=mix sink_0::xpos=0   sink_0::ypos=0   sink_0::zorder=2 \
                      sink_1::xpos=320 sink_1::ypos=0   sink_1::zorder=1 \
  ! "video/x-raw, width=(int)1344, height=(int)768,format=(string)I420, framerate=(fraction)30/1" \
  ! tee name=to_dev_loop \
  ! x264enc \
  ! queue \
  ! mux. \
  uvch264src device=${WEBCAM_DEVICE} \
     ! "video/x-raw, width=(int)320, height=(int)240,format=(string)I420, framerate=(fraction)30/1" \
     ! mix.sink_0 \
   v4l2src device=${GRABBER_DEVICE} \
     ! "video/x-raw, width=(int)1024, height=(int)768,format=(string)I420, framerate=(fraction)30/1" \
     ! videoconvert \
     ! "video/x-raw, width=(int)1024, height=(int)768, format=(string)I420, framerate=(fraction)30/1" \
     ! mix.sink_1 \
   pulsesrc ! audioconvert \
      ! audio/x-raw, rate=44100, channels=2 \
      ! lamemp3enc \
      ! queue \
      ! mp4mux name=mux \
   mux. ! filesink location="$DST" \
   to_dev_loop. ! queue ! v4l2sink device=/dev/video10

exit

gst-launch-1.0 -e videomixer name=mix sink_0::xpos=0   sink_0::ypos=0   sink_0::zorder=2 \
                                      sink_1::xpos=320 sink_1::ypos=0   sink_1::zorder=1 \
    ! videoconvert \
    ! "video/x-raw, format=I420, framerate=(fraction)30/1" \
    ! tee name=to_dev_loop \
    ! queue \
    ! x264enc \
    ! mux. \
    v4l2src device=${WEBCAM_DEVICE} \
        ! videoconvert \
        ! "video/x-raw, width=(int)320, height=(int)240, format=(string)YUY2, framerate=(fraction)30/1" \
        ! mix.sink_0 \
    v4l2src device=${GRABBER_DEVICE} \
        ! videoconvert \
        ! "video/x-raw, width=(int)800, height=(int)600, format=(string)YUY2, framerate=(fraction)30/1" \
        ! mix.sink_1 \
    pulsesrc \
        ! audioconvert \
        ! audio/x-raw, rate=44100, channels=2 \
        ! voaacenc \
        ! queue \
        ! mp4mux name=mux \
    mux. ! filesink location="${DST}" \
    to_dev_loop. ! queue ! v4l2sink device=/dev/video3
