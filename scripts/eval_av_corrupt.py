import argparse
import ffmpeg
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('-i', '--input', help='Path to the original MP4 file to be processed.', type=Path, required=True)
parser.add_argument('-o', '--output', help='Path where the new MP4 file will be saved to.', type=Path, required=True)
# text
parser.add_argument('-t', '--text', help='A text string to overlay on top of the MP4 video.', type=str)
parser.add_argument('-tr', '--text_range', help='If --text is used, the time range to overlay the text for. Specify the range in the format "<start>:<end>" in seconds, or using the "start" / "end" labels.', type=str, default="start:end")
# audio
parser.add_argument('-a', '--audio', help='A .WAV audio file that will replace (a part of) the original MP4 audio.', type=Path)
parser.add_argument('-ar', '--audio_range', help='If --audio is used, the time range to replace the original MP4 audio. Specify the range in the format "<start>:<end>" in seconds, or using the "start" / "end" labels.', type=str, default="start:end")
parser.add_argument('-at', '--audio_trim', help='If --audio is used, the time range to trim the supplied audio clip. Specify the range in the format "<start>:<end>" in seconds, or using the "start" / "end" labels.', type=str, default="start:end")
args = parser.parse_args()

# load video
s = ffmpeg.input(str(args.input))
v_stream = s.video
a_stream = s.audio
duration = float(ffmpeg.probe(str(args.input))['streams'][0]['duration'])

# AUDIO STREAM
if args.audio:
    # calculate range values
    ar = args.audio_range.split(':')
    atr = args.audio_trim.split(':')
    AUDIO_START         = 0 if ar[0] == 'start' else float(ar[0])
    AUDIO_TRIM_START    = 0 if atr[0] == 'start' else float(atr[0])
    AUDIO_END           = duration if ar[1] == 'end' else float(ar[1])
    AUDIO_TRIM_END      = ffmpeg.probe(str(args.audio))['streams'][0]['duration'] if atr[1] == 'end' else float(atr[1])

    # the audio before the replacement
    a_l = a_stream.filter('atrim', start=0, end=AUDIO_START)
    a_l = a_l.filter('asetpts', 'PTS-STARTPTS')

    # the audio during replacement
    a_m = ffmpeg.input(str(args.audio))
    a_m = a_m.filter('atrim', start=AUDIO_TRIM_START, end=AUDIO_TRIM_END)
    a_m = a_m.filter('asetpts', 'PTS-STARTPTS')
    # trim or pad with silence if candidate audio is longer/shorter than replacement range
    a_m = a_m.filter('atrim', start=0, end=AUDIO_END-AUDIO_START)
    a_m = a_m.filter('asetpts', 'PTS-STARTPTS')
    a_m = a_m.filter('apad', whole_dur=AUDIO_END-AUDIO_START)

    # the audio after replacement
    a_r = a_stream.filter('atrim', start=AUDIO_END, end=duration)
    a_r = a_r.filter('asetpts', 'PTS-STARTPTS')

    # concatenate the 3 audio streams into one
    a_stream = ffmpeg.concat(a_l, a_m, a_r, **{"n":3,"v":0,"a":1})

# VIDEO STREAM (TEXT)
if args.text:
    # calculate range values
    sr = args.text_range.split(':')
    TEXT_START = 0 if sr[0] == 'start' else float(sr[0])
    TEXT_END = duration if sr[1] == 'end' else float(sr[1])

    # print(TEXT_STR)
    # exit()
    # TEXT_STR_SUB = f"1\n00:00:00,000 --> 10:00:00,000\n{args.text}"
    # tmp_subs = tempfile.NamedTemporaryFile(suffix='.srt', delete=False, dir=os.path.join(os.path.dirname(os.path.realpath(__file__)), "temp"))
    # tmp_subs.write(TEXT_STR_SUB.encode('utf-8'))
    # tmp_subs.flush()
    # print(tmp_subs.name)   
    # stream = stream.filter("subtitles", "./temp/")
    # exit()

    v_stream = v_stream.drawtext(
        text        =args.text,
        # textfile    =args.text,
        x           ="(w-text_w)/2",
        y           ="(h-text_h)/2",
        fontsize    =64,
        fontfile    ="Arial:style=Bold",
        fontcolor   ="black",
        enable      =f'between(t,{TEXT_START},{TEXT_END})'
    )

# output the processed video
s = ffmpeg.output(v_stream, a_stream, str(args.output), **{"y": None})
s = s.run()