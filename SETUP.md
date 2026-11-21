# Profile cards

Install the renderer dependency and generate the animated cards from the checked-in contribution snapshot.

```sh
python -m pip install fonttools==4.68.0
python render_cards.py
```

For a screenshot, render still images into a separate folder and open them in your browser. Use an HTML page with `<img>` tags to preview the same rendering mode GitHub uses.

```powershell
$env:STATIC = '1'
python render_cards.py --output preview/cards
Remove-Item Env:STATIC
```

On macOS or Linux, run `STATIC=1 python render_cards.py --output preview/cards`.

The **Update Profile Stats** action runs daily at 03:17 UTC and can also be run manually. It fetches the public GitHub contribution calendar, saves the latest 365 days to `data/contributions.json`, regenerates `cards/`, and commits changes using GitHub's built-in workflow token. If GitHub's public calendar markup changes, the refresh fails before publishing and the previous cards stay on the profile.

To refresh the snapshot locally, run `python render_cards.py --refresh Rudranilkesh`. The analytics use the dates, totals, and activity levels visible on the public calendar. The chart includes partial months at the ends of the 365-day range. The portrait comes from `assets/portrait.jpg`. Pass a different JPEG with `--portrait`, or point the flag at a missing file to use initials.
