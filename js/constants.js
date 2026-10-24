/** A run is always this many prompts. Timeout and pass still count. */
export const RUN_LENGTH = 7;

/** The prompt is visible, but answers are not accepted yet. */
export const PREVIEW_MS = 2000;

/** Answering window after the preview. */
export const PLAY_MS = 25000;

/** One point lifts the craft by one kilometre. */
export const KM_PER_POINT = 1;

/** Bar and zone scale. Seven apex answers land at the top. */
export const MAX_KM = RUN_LENGTH * 100 * KM_PER_POINT;
