# Sounds

Put your own audio files (voice notes, recordings, mp3s) in this folder, then tell the game
which sentence each one belongs to by editing [`../sounds.json`](../sounds.json):

```json
{
  "37": "apple-in-bowl.mp3",
  "1": "good-evening.m4a"
}
```

- The **number** is the sentence number from [`phrases.json`](../phrases.json).
- The **file name** must match a file in this folder exactly (capital letters count).
- When the wheel lands on that sentence, its sound plays. Sentences without an entry stay silent.
- Landing on a new sentence stops the previous sound.
- A speaker button on the wheel lets people mute everything (their choice is remembered).

Tips:

- Use **`.mp3`** or **`.m4a`** (what an iPhone's Voice Memos app makes). They work in every browser.
  Avoid WhatsApp-style `.opus` / `.ogg` voice notes: Safari on older iPhones will not play them.
- Keep clips short, ideally under 10 seconds and under about 300 KB. They download on demand,
  but the page is for everyone, including people on mobile data.
- Everything in this repository is **public**, so anyone can find and download these files.
- After you push a change, the page can take up to ~10 minutes to show a new `sounds.json`
  (browsers cache it briefly). If you replace a file but keep its name, give the new one a
  different name, otherwise people may hear the old version for a while.
