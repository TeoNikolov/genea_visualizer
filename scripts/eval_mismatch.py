import argparse
import ffmpeg
import pandas as pd
from pathlib import Path

# either command line or batched
def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-csv', '--csv_file', help='Path to the "test_segments_evaluation.csv" file, which contains metadata for the mismatching process.', type=Path, required=True)
    parser.add_argument('-vf', '--video_folder', help='Path to the folder containing the video stimuli to mismatch.', type=Path, required=True)
    parser.add_argument('-af', '--audio_folder', help='Path to the folder containing the audio files which will replace the original audio of the video stimuli.', type=Path, required=True)
    parser.add_argument('-of', '--output_folder', help='Path to the folder where mismatched video files will be saved to.', type=Path, required=True)
    return parser.parse_args()

    # parser.add_argument('-v', '--video',        help='Path to MP4 for which the video stream will be used.',    type=Path, required=True)
    # parser.add_argument('-a', '--audio',        help='Path to MP4 for which the audio stream will be used.',    type=Path, required=True)
    # parser.add_argument('-o', '--output',       help='Path to which the output MP4 will be saved',              type=Path, required=True)
    # parser.add_argument('-vr', '--video_range', help='The time range for which the video stream is extracted. Specify the range in the format "<start>:<end>" in seconds, or using the "start" / "end" labels.', type=str, default="start:end")
    # parser.add_argument('-ar', '--audio_range', help='The time range for which the audio stream is extracted. Specify the range in the format "<start>:<end>" in seconds, or using the "start" / "end" labels.', type=str, default="start:end")
    # return parser.parse_args()

def load_csv(filepath : Path) -> pd.DataFrame:
    return pd.read_csv(filepath)
    # validate format?

args = get_args()
metadata = load_csv(args.csv_file)

for index, row in metadata.iterrows():
    original_ID = row['File'].split('_')[-1].split('.wav')[0]
    mismatch_ID = row['Mismatched File'].split('_')[-1].split('.wav')[0]
    video_filepath = args.video_folder / f"stimuli_withaudiofilter_{original_ID}_cut.mp4"
    audio_filepath = args.audio_folder / row['Mismatched File']
    output_filepath = args.output_folder / f"stimuli_withaudiofilter_{original_ID}_cut_mismatched_{mismatch_ID}.mp4"

    # mismatch_start = datetime.strptime(row['Start'], "%M:%S.%f")
    # mismatch_end = datetime.strptime(row['End'], "%M:%S.%f")
    # get audio stream segment
    audio_stream = ffmpeg.input(str(audio_filepath)).audio
    audio_stream = audio_stream.filter('atrim', start=row['Start'], end=row['End'])
    audio_stream = audio_stream.filter('asetpts', 'PTS-STARTPTS')
    # get video stream
    video_stream = ffmpeg.input(str(video_filepath)).video
    # merge audio and video streams, and save to disk
    output_stream = ffmpeg.output(video_stream, audio_stream, str(output_filepath), **{"y": None, "shortest": None})
    output_stream.run()