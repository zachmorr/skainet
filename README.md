# Skainet

Skainet is a shell tool for interacting with the OpenAI API. It provides a convenient command-line interface for using various OpenAI models and services such as chat, audio transcription, and image generation.

## Installation
Pip installation requires Python 3.7 or later
```console
pip install skainet
```

## Chatting
The chat feature in Skainet allows you to have a conversation with ChatGPT, an AI language model developed by OpenAI. You can use the `skai chat` command to send a message
```console
skai chat "Where is Waldo?"
Unknown.
```

The chat tool also accepts piped input
```console
git diff --cached | skai chat "write a commit message for this diff" | git commit -F -
```

## Audio Transcription
```console
skai audio transcribe Tequila-TheChamps.mp3
♪ ♪ ♪ ♪ ♪ ♪ Tequila ♪ ♪ ♪ ♪ ♪ ♪ ♪ ♪ Tequila ♪ ♪ ♪ ♪ ♪ ♪ Tequila
```

## Audio Translation
```console
skai audio translate bruh.mp3
Bruh
```

## Image Generation
```console
skai image create "a photo of Gandalf playing ping pong"
```
![Nice shot!](assets/gandalf_small.png)

## Image Edits
```console
skai image edit img.png mask.png "an owl living in the middle of a cartoon tree"
```
![Original](test/files/img.png) ![Mask](test/files/mask.png) ![Not quite what I ment](assets/owltree_small.png)

## Image Variation
```console
skai image variation img.png
```
![Original](test/files/img.png) ![Variation](assets/variation.png)

