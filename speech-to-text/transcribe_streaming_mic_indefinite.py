#!/usr/bin/env python

# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Google Cloud Speech API sample application using the streaming API.

NOTE: This module requires the additional dependency `pyaudio`. To install
using pip:

    pip install pyaudio

Example usage:
    python transcribe_streaming_mic.py
"""

# [START import_libraries]
from __future__ import division

import argparse
import re
import sys
import grpc

from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types

from microphone_stream import ResumableMicrophoneStream, SimulatedMicrophoneStream
# [END import_libraries]

def duration_to_secs(duration):
    return duration.seconds + (duration.nanos / float(1e9))

def _record_keeper(responses, stream):
    """Calls the stream's on_transcribe callback for each final response.

    Args:
        responses - a generator of responses. The responses must already be
            filtered for ones with results and alternatives.
        stream - a ResumableMicrophoneStream.
    """
    for r in responses:
        result = r.results[0]
        if result.is_final:
            top_alternative = result.alternatives[0]
            # Keep track of what transcripts we've received, so we can resume
            # intelligently when we hit the deadline
            stream.on_transcribe(duration_to_secs(
                    top_alternative.words[-1].end_time))
        yield r

def listen_print_loop(responses, stream):
    """Iterates through server responses and prints them.

    Same as in transcribe_streaming_mic, but keeps track of when a sent
    audio_chunk has been transcribed.
    """
    with_results = (r for r in responses if (r.results and r.results[0].alternatives))
    _listen_print_loop(_record_keeper(with_results, stream))

def _listen_print_loop(responses):
    """Iterates through server responses and prints them.

    The responses passed is a generator that will block until a response
    is provided by the server.

    Each response may contain multiple results, and each result may contain
    multiple alternatives; for details, see https://goo.gl/tjCPAU.  Here we
    print only the transcription for the top alternative of the top result.

    In this case, responses are provided for interim results as well. If the
    response is an interim one, print a line feed at the end of it, to allow
    the next result to overwrite it, until the response is a final one. For the
    final one, print a newline to preserve the finalized transcription.
    """
    num_chars_printed = 0
    for response in responses:
        if not response.results:
            continue

        # The `results` list is consecutive. For streaming, we only care about
        # the first result being considered, since once it's `is_final`, it
        # moves on to considering the next utterance.
        result = response.results[0]
        if not result.alternatives:
            continue

        # Display the transcription of the top alternative.
        top_alternative = result.alternatives[0]
        transcript = top_alternative.transcript

        # Display interim results, but with a carriage return at the end of the
        # line, so subsequent lines will overwrite them.
        #
        # If the previous result was longer than this one, we need to print
        # some extra spaces to overwrite the previous result
        overwrite_chars = ' ' * (num_chars_printed - len(transcript))

        if not result.is_final:
            sys.stdout.write(transcript + overwrite_chars + '\r')
            sys.stdout.flush()

            num_chars_printed = len(transcript)

        else:
            print(transcript + overwrite_chars)

            # Exit recognition if any of the transcribed phrases could be
            # one of our keywords.
            if re.search(r'\b(exit|quit)\b', transcript, re.I):
                print('Exiting..')
                break

            num_chars_printed = 0

def main(sample_rate, audio_src):
    # See http://g.co/cloud/speech/docs/languages
    # for a list of supported languages.
    language_code = 'en-US'  # a BCP-47 language tag

    client = speech.SpeechClient()
    config = types.RecognitionConfig(
        encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=sample_rate,
        language_code=language_code,
        max_alternatives=1,
        enable_word_time_offsets=True)
    streaming_config = types.StreamingRecognitionConfig(
        config=config,
        interim_results=True)

    if audio_src:
        mic_manager = SimulatedMicrophoneStream(
                audio_src, sample_rate, int(sample_rate / 10))
    else:
        mic_manager = ResumableMicrophoneStream(
                sample_rate, int(sample_rate / 10))

    with mic_manager as stream:
        resume = False
        while True:
            audio_generator = stream.generator(resume=resume)
            requests = (types.StreamingRecognizeRequest(audio_content=content)
                        for content in audio_generator)

            responses = client.streaming_recognize(streaming_config, requests)

            try:
                # Now, put the transcription responses to use.
                listen_print_loop(responses, stream)
                break
            except grpc.RpcError as e:
                if e.code() not in (grpc.StatusCode.INVALID_ARGUMENT,
                                    grpc.StatusCode.OUT_OF_RANGE):
                    raise
                details = e.details()
                if e.code() == grpc.StatusCode.INVALID_ARGUMENT:
                    if 'deadline too short' not in details:
                        raise
                else:
                    if 'maximum allowed stream duration' not in details:
                        raise

                print('Resuming..')
                resume = True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--rate', default=16000, help='Sample rate.', type=int)
    parser.add_argument('--audio_src', help='File to simulate streaming of.')
    args = parser.parse_args()
    main(args.rate, args.audio_src)