import re
import os

line_pattern = re.compile('(\w+)--(\w+(?:,?\s\w+)*)\tColour=(\w+)\tVotesForThisColour=(\w+)\tTotalVotesCast=(\w+)')

file_contents = ''
with open(os.path.dirname(os.path.realpath(__file__)) + '/NRC-color-lexicon-senselevel-v0.92.txt') as f:
    file_contents = f.read()

lines = file_contents.split('\n')

word_color_associations = {}

for line in lines:
    if not line:
        continue

    match = line_pattern.match(line)

    if not match:
        print(line)
        continue

    word = match.group(1)
    senses = match.group(2).split(', ')
    color = match.group(3)
    votes_for_color = match.group(4)
    total_votes = match.group(5)

    word_color_associations[word] = {
        'senses': senses,
        'color': color if color != 'None' else None,
        'votes_for_color': votes_for_color,
        'total_votes': total_votes
    }
