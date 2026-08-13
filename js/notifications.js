import { getPlugin } from "../native-bridge.js";
import { DEFAULT_NOTIFICATION_TIME, parseTimeOfDay as parseTime } from "./core/timezone.js";

export { DEFAULT_NOTIFICATION_TIME, parseTime };

const PREF_TIME_KEY = "notificationTime";
const PREF_ENABLED_KEY = "notificationsEnabled";
const RUNNER_LABEL = "com.maximbk.weatherhelper.dailyforecast";
const UPDATE_SETTINGS_EVENT = "updateNotificationSettings";

export async function getNotificationTime() {
  const Preferences = getPlugin("Preferences");
  if (!Preferences) return DEFAULT_NOTIFICATION_TIME;
  const { value } = await Preferences.get({ key: PREF_TIME_KEY });
  return parseTime(value) ? value : DEFAULT_NOTIFICATION_TIME;
}

export async function getNotificationsEnabled() {
  const Preferences = getPlugin("Preferences");
  if (!Preferences) return false;
  const { value } = await Preferences.get({ key: PREF_ENABLED_KEY });
  return value === "true";
}

export async function saveNotificationSettings({ enabled, time }) {
  const parsed = parseTime(time);
  if (!parsed) throw new Error(`Invalid time: ${time}`);
  const Preferences = getPlugin("Preferences");
  if (Preferences) {
    await Preferences.set({ key: PREF_TIME_KEY, value: time });
    await Preferences.set({ key: PREF_ENABLED_KEY, value: String(enabled) });
  }
}

export async function requestNotificationPermission() {
  const BackgroundRunner = getPlugin("BackgroundRunner");
  if (!BackgroundRunner) return "granted";
  const status = await BackgroundRunner.checkPermissions();
  if (status.notifications === "granted") return "granted";
  const requested = await BackgroundRunner.requestPermissions({ apis: ["notifications"] });
  return requested.notifications;
}

export async function pushNotificationSettingsToRunner(enabled, time) {
  const BackgroundRunner = getPlugin("BackgroundRunner");
  if (!BackgroundRunner) return;
  await BackgroundRunner.dispatchEvent({
    label: RUNNER_LABEL,
    event: UPDATE_SETTINGS_EVENT,
    details: { enabled, time },
  });
}

export async function applyNotificationSettings({ enabled, time }) {
  await saveNotificationSettings({ enabled, time });
  if (!enabled) {
    await pushNotificationSettingsToRunner(false, time);
    return "disabled";
  }
  const permission = await requestNotificationPermission();
  if (permission !== "granted") return "denied";
  await pushNotificationSettingsToRunner(true, time);
  return "granted";
}

export async function initNotifications() {
  const enabled = await getNotificationsEnabled();
  if (!enabled) return;
  const time = await getNotificationTime();
  const permission = await requestNotificationPermission();
  if (permission === "granted") await pushNotificationSettingsToRunner(true, time);
}
