# woooosh! — Research Report

## 1. Overview

**woooosh!** is a minimalist, single-page Progressive Web App (PWA) for personal task management. It runs entirely in the browser with no backend — all state lives in `localStorage`. The app's philosophy is captured in its tagline: *"Capture Ideas, Actionize, Start, and if you can't — Schedule!"*

The repo contains only four files:

| File | Purpose |
|------|---------|
| `index.html` | The entire app — markup, CSS, and JS bundled in one file |
| `sw.js` | Service Worker for offline/PWA support |
| `manifest.json` | PWA manifest (icons, start URL, colors, display mode) |
| `images/` | Icon assets (192 × 192 and 512 × 512 PNG) |

---

## 2. Data Model

Tasks are stored as a JSON array in `localStorage` under the key `wooooshTasks`.

Each task object has the following shape:

```json
{
  "id": 1716000000000,
  "text": "Write the research doc",
  "status": "idea",
  "created": "2024-05-18T10:00:00.000Z",
  "scheduledFor": null,
  "isEditing": false,
  "isScheduling": false
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | `number` | Unix timestamp (ms) used as unique ID, set via `Date.now()` |
| `text` | `string` | Task description |
| `status` | `string` | Current workflow state (see below) |
| `created` | `ISO string` | Creation timestamp, used for ordering |
| `scheduledFor` | `ISO string \| null` | Scheduled datetime for `status === 'scheduled'` |
| `isEditing` | `boolean` | UI-only flag — not persisted meaningfully |
| `isScheduling` | `boolean` | UI-only flag — not persisted meaningfully |

> **Note:** `isEditing` and `isScheduling` are runtime-only UI flags. `loadTasks()` resets both to `false` on every page load, so they survive in localStorage as written but are always cleared on reload — a safe-but-intentional behavior.

---

## 3. Workflow & Status Machine

The app enforces a linear but flexible workflow:

```
idea ──► action ──► inProgress ──► completed
                 │                    ▲
                 └──► scheduled ──────┘
                 └──► (also from inProgress → scheduled)
```

### Status Transitions

| From | Available Transitions | Triggered By |
|------|----------------------|--------------|
| `idea` | → `action` | "Actionize" button |
| `action` | → `inProgress` | "Start Now" button |
| `action` | → `scheduled` | "Schedule" → datetime picker → "Set" |
| `inProgress` | → `completed` | "Complete" button |
| `inProgress` | → `scheduled` | "Schedule" button (reschedule) |
| `scheduled` | → `inProgress` | "Start Now" button |
| `scheduled` | → `completed` | "Complete" button |
| `scheduled` | → `scheduled` (new time) | "Reschedule" button |
| `completed` | → `action` | "Re-open" button |

Any status can be edited (text) or deleted at any time (except while the scheduling picker is open — the Delete button is hidden to prevent accidental deletion).

---

## 4. Architecture

### Rendering

The app uses a **full DOM re-render** strategy: every call to `renderTasks()` wipes `taskList.innerHTML` and rebuilds all task elements from scratch. This is simple but means:
- All event listeners are inline `onclick`/`onblur` attributes (no `addEventListener`)
- There is no virtual DOM or diffing
- Re-render is synchronous and fast enough for the expected task count

### Persistence

```js
function saveTasks()  → JSON.stringify(tasks) → localStorage
function loadTasks()  → JSON.parse(localStorage) → tasks[]
```

Called on every change via `saveAndRender()` which calls `saveTasks()` then `renderTasks()`.

### PWA / Service Worker

The service worker (`sw.js`) uses a **cache-first** strategy:
1. **Install**: pre-caches `./`, `./index.html`, `./manifest.json`, and the two icon PNGs.
2. **Activate**: deletes all caches whose names differ from `CACHE_NAME` (handles cache versioning).
3. **Fetch**: serves from cache if available; falls back to network and caches the response.

The SW is only registered when running on HTTPS or localhost (standard PWA requirement).

### Filter System

Tasks can be filtered by status. The current filter is stored in `currentFilter` (default: `'all'`). `setFilter(filter)` updates the active button class and calls `renderTasks()` which applies the filter on the in-memory `tasks` array.

Sorting: completed tasks are sorted to the bottom; all others are sorted newest-first by `created` date.

---

## 5. Bugs Found

### Bug #1 — Missing curly braces in `toggleEdit` (Critical)

**Location:** `toggleEdit()` function

**Code (broken):**
```js
function toggleEdit(id) {
    tasks.forEach(t => { if (t.id !== id) t.isEditing = false; t.isScheduling = false; });
```

**What it does:** Due to the missing `{}` around the `if` body, `t.isScheduling = false` is **outside** the `if` block and runs for **every task** — including the task currently being toggled. Intended behavior is that only *other* tasks have their editing/scheduling state cleared.

**Impact:** Whenever a user opens edit mode on any task, all tasks (including any currently open scheduling interfaces) have their `isScheduling` state forcibly cleared. This causes the scheduling datetime picker to vanish unexpectedly — a task being scheduled "disappears" its scheduler when any edit is opened elsewhere.

**Fix:**
```js
tasks.forEach(t => { if (t.id !== id) { t.isEditing = false; t.isScheduling = false; } });
```

---

### Bug #2 — Missing curly braces in `openScheduleInterface` (Critical)

**Location:** `openScheduleInterface()` function

**Code (broken):**
```js
function openScheduleInterface(id) {
    tasks.forEach(t => { if (t.id !== id) t.isScheduling = false; t.isEditing = false; });
```

**What it does:** `t.isEditing = false` runs for **every task** — not just the others. Intended behavior is that opening the scheduler on one task closes any editing/scheduling on other tasks.

**Impact:** If a user is in editing mode and clicks "Schedule" (which is visible even when `isEditing` is true), the edit mode is forcibly cancelled for *all* tasks. The user cannot combine edit-then-schedule without the edit being abruptly discarded.

**Fix:**
```js
tasks.forEach(t => { if (t.id !== id) { t.isScheduling = false; t.isEditing = false; } });
```

---

### Bug #3 — Escape key does not cancel editing (Medium)

**Location:** The `<input type="text">` rendered inside `renderTasks()` for editing tasks.

**Code (broken):**
```html
onkeypress="if(event.key === 'Enter') { this.blur(); return false; }
            else if (event.key === 'Escape') { toggleEdit(${task.id}); return false; }"
```

**Two sub-problems:**
1. `onkeypress` does **not** fire for non-printable keys including `Escape` in modern browsers. The Escape handler is therefore dead code.
2. Even if `onkeydown` were used, pressing Escape would lose focus on the input, triggering `onblur` → `updateTaskText()` *before* the escape handler can cancel the edit. The text would be saved despite the user's intent to cancel.

**Impact:** Pressing Escape while editing a task text silently does nothing (the edit remains open), making Escape feel broken and forcing users to click "Save" or press Enter even when they want to discard changes.

**Fix:**
- Use `onkeydown` instead of `onkeypress`
- Set a module-level `_editCancelled` flag on Escape, then `blur()`
- Check the flag in `onblur`: if set, call `cancelEdit()` (closes without saving) instead of `updateTaskText()` (saves)

---

### Bug #4 — `onblur` + DOM re-render can trigger unintended actions (Medium)

**Location:** `updateTaskText()` called from `onblur`, followed by `saveAndRender()`

**Root cause:** In browsers, `blur` fires on `mousedown` (when the user presses the mouse button on another element). The full click event (mousedown + mouseup + click) fires *after* blur. `saveAndRender()` inside `updateTaskText()` synchronously replaces the entire `taskList` DOM.

**Scenario where tasks "run when they should be cancelled":**
1. Task A is in `action` state, user opened edit mode (`isEditing = true`).
2. User clicks "Start Now" button — `mousedown` fires, then `blur` fires on the text input.
3. `updateTaskText()` runs: sets `isEditing = false`, calls `saveAndRender()` — DOM is entirely replaced.
4. `mouseup`/`click` fires at the same screen coordinates.
5. After re-render, a *different* button may now be at that location (e.g., "Delete" appeared because the editing state changed the button layout), and that button's click handler fires unexpectedly.

**Impact:** Tasks can inadvertently change status (e.g., "Start Now" fires when user intended to click "Save") or be deleted when user intended a different action.

**Fix:** Use a module-level `_editCancelled` flag approach (as in Bug #3) plus ensure the `onblur`-triggered re-render risk is mitigated. A simpler approach: since `isEditing` state change from `true→false` does not significantly shift button positions in the current layout ("Edit"↔"Save" swap is the first button; all other buttons remain in position), the practical impact is low. The Escape key fix (Bug #3) addresses the most user-visible aspect of this bug.

---

## 6. User Workflow Deep-Dive

### Add Task
1. User types in the top input field.
2. Clicks "Add" (or presses Enter — *not* natively handled, see Bug #3 area).
3. New task created with status `idea`, prepended to the list.

### Actionize
- Only available on `idea` tasks.
- Clicking "Actionize" changes status to `action`.
- The task conceptually transitions from "I have an idea" to "I'm committed to doing this."

### Start Now vs. Schedule
- Available on `action` tasks.
- "Start Now" → `inProgress` immediately.
- "Schedule" → opens inline datetime picker → confirm saves `scheduledFor` and sets status `scheduled`.

### Reschedule
- Available on `scheduled` tasks alongside "Start Now" and "Complete."

### Complete
- Available on `inProgress` and `scheduled` tasks.
- Sets status to `completed`; `scheduledFor` is cleared.
- Completed tasks are visually struck through and sorted to the bottom.

### Re-open
- Available on `completed` tasks.
- Returns task to `action` status (skips `idea` — the task is already understood).

### Edit
- Available on all tasks except when scheduling is open.
- Inline text editing with save on `onblur` or Enter.
- Escape key *appears* to be supported but is broken (Bug #3).

### Delete / Delete All
- Both require browser `confirm()` dialogs for safety.
- "Delete All" is guarded by an `alert()` if the list is empty.

---

## 7. Filter Mechanics

The filter buttons target `task.status` directly:

```js
const filteredTasks = tasks.filter(task => {
    if (currentFilter === 'all') return true;
    return task.status === currentFilter;
});
```

Filter button IDs follow the pattern `filter` + capitalised status name:
- `filterAll`, `filterIdea`, `filterAction`, `filterInProgress`, `filterScheduled`, `filterCompleted`

The active state is managed via CSS class `.active` on the corresponding button.

---

## 8. PWA Notes

- **Manifest:** `start_url: "/"` with standalone display mode. Both icon sizes carry `"purpose": "any maskable"`.
- **SW Cache Version:** `woooosh-cache-v6` — must be incremented on every deployment that changes cached assets.
- **Registration Guard:** SW is only registered on HTTPS or localhost, preventing registration errors during local `file://` development.
- **No background sync / push notifications** — the app is purely interactive; there is no server-side component.

---

## 9. Summary of All Changes Recommended

| Priority | Change | Reason |
|----------|--------|--------|
| 🔴 Critical | Fix `toggleEdit` curly braces | Scheduling picker unexpectedly disappears |
| 🔴 Critical | Fix `openScheduleInterface` curly braces | Editing mode unexpectedly cancelled |
| 🟠 High | Fix Escape key in edit mode | Dead code; users can't cancel an edit |
| 🟠 High | Fix `onblur` + re-render race | Unintended task status changes |
| 🟡 Medium | Add `reminder` status + button | Feature requirement |
| 🟡 Medium | Replace `alert()` with toast notifications | Modern UX |
| 🟢 Low | Add task slide-in animation | Visual polish |
| 🟢 Low | Add confetti on task completion | Spark joy |
| 🟢 Low | Add count badges on filter buttons | Better at-a-glance info |
| 🟢 Low | Add emoji to status pills | Visual character |
| 🟢 Low | Enter key to add task | Keyboard usability |
| 🟢 Low | Better mobile responsive layout | Touch-friendliness |
