==========================================
TEMPLATES FOR MAPLESTORY IDLE BOT
==========================================

CURRENT TEMPLATES:
  [x] app_button.png    - App icon to open game
  [x] main_menu.png     - Main lobby indicator
  [x] pq_button.png     - Party Quest button
  [x] sleepywood.png    - Sleepywood quest option
  [x] start_queue.png   - Start queue button
  [x] in_queue.png      - Waiting in queue indicator
  [x] stop_queue.png    - Cancel queue button
  [x] confirm.png       - OK/Confirm button

OPTIONAL (for better detection):
  [ ] ludibrium.png     - Ludibrium quest option
  [ ] orbis.png         - Orbis quest option
  [ ] in_pq.png         - Inside PQ battle indicator
  [ ] pq_complete.png   - Victory/completion screen
  [ ] victory.png       - Alternative victory indicator

==========================================
BOT FLOW
==========================================

1. LOOKING_FOR_GAME
   - Looks for: main_menu, pq_button, or app_button
   - If app_button found: clicks to open game

2. IN_MAIN_MENU
   - Looks for: pq_button
   - Clicks it to open PQ selection

3. SELECTING_QUEST
   - Looks for: sleepywood, ludibrium, or orbis
   - Clicks to select quest

4. CLICKING_START
   - Looks for: start_queue
   - Clicks to enter queue

5. IN_QUEUE
   - Looks for: in_queue (to confirm we're queued)
   - Waits for match or timeout
   - If timeout: goes to CANCELING_QUEUE

6. CANCELING_QUEUE
   - Looks for: stop_queue
   - Clicks to cancel and retry

7. IN_PQ
   - Looks for: in_pq, confirm buttons
   - Waits for completion

8. PQ_COMPLETED
   - Clicks confirm to dismiss results
   - Returns to IN_MAIN_MENU

==========================================
