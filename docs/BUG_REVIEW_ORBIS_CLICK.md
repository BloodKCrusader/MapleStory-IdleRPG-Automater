# Bug Review: Orbis Selection Clicks Ludibrium

## Summary

When the user selects **Orbis** and the bot runs, the tap is performed on the **Ludibrium** card instead of the Orbis card. The mouse/cursor in the user's screenshot is on Ludibrium when Orbis was intended.

---

## How Quest Selection Works (Current Flow)

1. **Entry**: `main.py` → GUI or CLI sets `quest-choice` (e.g. `"orbis"`). Bot gets it as `self.quest_choice` in `MapleStoryIdleBot`.

2. **Main loop** (`games/maple_story_idle.py`):
   - `_tick()` runs every ~0.2s: capture screen, run priority checks, then either `_handle_queue()` (if in queue) or `_detect_and_act()` (if not in PQ and not in queue).

3. **Quest selection** happens inside `_detect_and_act()` (around lines 666–673):
   - `quest = self.quest_choice`  # e.g. `"orbis"`.
   - `if self.matcher.find(screen, quest):`  # Loads `orbis.png`, runs template matching.
   - If truthy: log "Selecting orbis...", then `_check_and_click(screen, quest)`.
   - `_check_and_click` calls `matcher.find(screen, "orbis")` again and, if found, `input.tap_center(match)`.

4. **Template matcher** (`core/template_matcher.py`):
   - `find(screen, template_name)` loads the template (e.g. `orbis.png`), runs `cv2.matchTemplate(screen, template, TM_CCOEFF_NORMED)` on the **entire** screenshot.
   - `cv2.minMaxLoc(result)` returns the **single** location with the **highest** correlation value.
   - If that value ≥ threshold (0.85), it returns a `MatchResult` at that location `(max_loc[0], max_loc[1])` (top-left of template). The bot then taps the **center** of that rectangle (`center_x`, `center_y`).

5. **Input** (`core/input_handler.py`):
   - `tap_center(match_result)` calls `tap(match_result.center_x, match_result.center_y)`.
   - `tap()` adds a small random offset (humanize), clamps to 0..959, 0..539, and sends `adb shell input tap x y`.

6. **Screen and coordinates**:
   - Screenshot comes from ADB `screencap` (no resizing in the code). Expected resolution is 960×540 (BlueStacks setting).
   - Tap is sent in the same coordinate system (device/emulator). So screenshot and tap are aligned **if** the device is 960×540.

---

## Where the Bug Is

**Location**: The wrong click is a consequence of **where** the template match is accepted and clicked, not a coordinate or ADB bug.

**Root cause**:  
`matcher.find(screen, "orbis")` returns the **global best** match on the **whole** screen. There is **no** check that this match lies on the **Orbis** card (the third card). So:

- If `orbis.png` matches **better** on a region that overlaps the **Ludibrium** card (e.g. similar colors, card frame, or a small template that fits multiple cards), `find()` returns that location.
- The code then taps the center of that match → the tap goes to **Ludibrium**.

So the bug is: **we trust the best template match regardless of screen region.** For a four-card layout (Sleepywood | Ludibrium | Orbis | Locked), we should only treat a match as “Orbis” if it lies in the **third** card’s region (e.g. right half of the screen for 960 px width). Accepting a match in the second card (Ludibrium) causes the observed bug.

**Relevant code**:

- **`core/template_matcher.py`** (lines 170–183): returns one global best match, no region constraint.
- **`games/maple_story_idle.py`** (lines 666–673): uses that match for quest selection without checking that the match is in the correct card region for `"orbis"`.

So the **fix** belongs in the **game bot** (quest selection logic): when `quest_choice == "orbis"`, only accept a match whose center is in the Orbis card region; otherwise treat as “no match” and optionally fall back to a fixed position for Orbis.

---

## Why Template Matching Can Pick the Wrong Card

- `cv2.matchTemplate` slides the template over the whole image and returns one correlation value per position. `minMaxLoc` picks the **single** position with the highest value.
- Cards share UI (frame, layout, font). A template that includes a lot of “generic” pixels can have high correlation on more than one card.
- If the Orbis template is small or similar in color to Ludibrium, the maximum can be on Ludibrium.
- So “best match” does **not** guarantee “correct card” unless we restrict by region.

---

## Other Components (Checked, Not the Bug)

- **Screen capture**: No resize; screenshot is used as-is. Coordinates from the matcher correspond to the same frame as the tap.
- **ADB tap**: `input tap x y` uses the same coordinate system as the device screen. No scaling in code.
- **Input humanize**: Small random offset (±5 px) and clamp to 960×540. Cannot move a correct Orbis tap onto Ludibrium; it can only slightly shift a tap that is already wrong.
- **POSITIONS**: Used elsewhere (e.g. cancel queue, center tap). Quest selection currently does **not** use `POSITIONS` for the initial click; it uses only the template match. So wrong tap is from match position, not from a wrong constant.
- **Recovery** (`_try_recovery`): Uses `(self.quest_choice, "click")` and the same `matcher.find` + `tap_center`. So it has the same risk: if the best match for `orbis` is on Ludibrium, recovery would also click Ludibrium. Fixing the main quest selection (region check + optional position fallback) keeps behavior consistent; recovery could use the same “Orbis region” rule if we add it.

---

## Recommended Fix (Without Replacing Template Selection)

1. **Region check for Orbis**  
   In the quest selection block, when `quest == "orbis"`:
   - Call `match = self.matcher.find(screen, quest)`.
   - If `match` is not None, require `match.center_x >= ORBIS_MIN_X` (e.g. 600 for 960 px, so the match is in the right half / third card). If `match.center_x < 600`, set `match = None` (reject this match).
   - If after this we have a valid `match`, log "Selecting orbis..." and `tap_center(match)`.
   - If we do **not** have a valid match and `quest in self.POSITIONS`, optionally **fallback**: log "Selecting orbis (position)..." and `self.input.tap(*self.POSITIONS["orbis"])`.

2. **Leave other quests unchanged**  
   Do **not** change the logic for Sleepywood/Ludibrium: keep “if find(quest) then click” as is, so the app keeps working for them.

3. **Optional**  
   Use the same Orbis region rule (and position fallback) in `_try_recovery` when `self.quest_choice == "orbis"` so recovery doesn’t click Ludibrium either.

This keeps template-based selection when the match is in the correct region and prevents clicking Ludibrium when the best match is on the wrong card.
