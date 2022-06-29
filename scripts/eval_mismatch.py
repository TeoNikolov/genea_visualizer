import argparse
import ffmpeg
import pandas as pd
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('-csv', '--csv_file', help='Path to the "test_segments_evaluation.csv" file, which contains metadata for the mismatching process.', type=Path, required=True)
parser.add_argument('-vf', '--video_folder', help='Path to the folder containing the video stimuli to mismatch.', type=Path, required=True)
parser.add_argument('-af', '--audio_folder', help='Path to the folder containing the audio files which will replace the original audio of the video stimuli.', type=Path, required=True)
parser.add_argument('-of', '--output_folder', help='Path to the folder where mismatched video files will be saved to.', type=Path, required=True)
args = parser.parse_args()

metadata = pd.read_csv(args.csv_file)
for index, row in metadata.iterrows():
    # video IDs are offset by 1 in the spreadsheet currently (i.e. ID 18 -> video 017)
    mismatch_video_ID = int(row['Mismatched ID']) - 1
    video_ID = int(row['Sample number']) - 1
    audio_ID = int(row['File'].split('_')[-1].split('.wav')[0])

    video_filepath = args.video_folder / f"stimuli_noneaudiofilter_{mismatch_video_ID:0>3}_cut.mp4"
    audio_filepath = args.audio_folder / f"tst_2022_v1_{audio_ID:0>3}.wav"
    output_filepath = args.output_folder / f"stimuli_noneaudiofilter_{mismatch_video_ID:0>3}_cut_mismatched_{audio_ID:0>3}.mp4"
    
    # get audio stream segment
    audio_stream = ffmpeg.input(str(audio_filepath)).audio
    audio_stream = audio_stream.filter('atrim', start=row['Start'], end=row['End'])
    audio_stream = audio_stream.filter('asetpts', 'PTS-STARTPTS')
    # get video stream
    video_stream = ffmpeg.input(str(video_filepath)).video
    # merge audio and video streams, and save to disk
    output_stream = ffmpeg.output(video_stream, audio_stream, str(output_filepath), **{"y": None, "shortest": None})
    output_stream.run()