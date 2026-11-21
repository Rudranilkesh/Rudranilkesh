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

The **Update Profile Stats** action runs hourly at 17 minutes past the hour and can also be run manually. It saves the dates and total from GitHub's native public profile calendar to `data/contributions.json` and the seven-day public commit count to `data/commits.json`. It regenerates `cards/` and commits changes using GitHub's built-in workflow token. If an activity source fails or the calendar cells disagree with GitHub's displayed total, the previous cards stay on the profile.

To include anonymized private activity in the contribution cards, enable **Contribution settings → Private contributions** on your GitHub profile. The refresh uses only the calendar totals GitHub already makes visible to profile visitors.

Commit Sun uses [GitHub Commit Search](https://docs.github.com/en/search-github/searching-on-github/searching-commits). Its seven-day window ends on the latest date in the public contribution calendar. Search covers authored commits on public repositories' default branches. Between zero and ten commits, the sun's corona expands and brightens and its pulse speeds up. The card stays at maximum intensity above ten and continues to display the full count. Reduced motion and `STATIC=1` keep the sun still.

To refresh the snapshot locally, run `python render_cards.py --refresh Rudranilkesh`. The chart includes partial months at the ends of GitHub's date range. The portrait comes from `assets/portrait.jpg`. Pass a different JPEG with `--portrait`, or point the flag at a missing file to use initials.
