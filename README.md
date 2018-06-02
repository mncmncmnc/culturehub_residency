# Terminal Setup Instructions for OS X

1. Install Homebrew.

```/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"```

2. Install pyenv, pyenv-virtualenv, and portaudio.

```brew install pyenv pyenv-virtualenv portaudio```

3. Run the following commands to add init code for `pyenv` and `pyenv-virtualenv` to your ~/.bash_profile.

```
touch ~/.bash_profile

echo 'eval "$(pyenv virtualenv-init -)"' | cat - ~/.bash_profile > temp && mv temp ~/.bash_profile

echo 'eval "$(pyenv init -)"' | cat - ~/.bash_profile > temp && mv temp ~/.bash_profile

source ~/.bash_profile
```

4. Set your global Python version to 3.6.5.

```
pyenv install 3.6.5
pyenv global 3.6.5
```

5. Create a virtualenv called `speech-to-text`. The name matters, because currently it's hardcoded into the Max/MSP patch.

```pyenv virtualenv speech-to-text```

6. Activate the virtualenv and install the Python dependencies.

```
pyenv activate speech-to-text
cd speech-to-text
pip install -r requirements.txt
```

You should now be able to run the speech transcription Python script. You can test it out by running the following command from the `speech-to-text` directory.

```python listen.py 0```
