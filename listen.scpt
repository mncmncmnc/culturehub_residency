on run argv
  do shell script "source ~/.bash_profile; pyenv activate speech-to-text; ./speech-to-text/listen.py -d " & item 1 of argv
end run
