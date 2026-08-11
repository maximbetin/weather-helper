import { getPlugin } from "../native-bridge.js";

const DAILY_NOTIFICATION_ID = 1001;
export const DEFAULT_NOTIFICATION_TIME = "08:00";

const PREF_TIME_KEY = "notificationTime";
const PREF_ENABLED_KEY = "notificationsEnabled";

export function parseTime(value) {
  const match = /^([0-1]\d|2[0-3]):([0-5]\d)$/.exec(value ?? "");
  if (!match) return null;
  return { hour: Number(match[1]), minute: Number(match[2]) };
}

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

export function buildDailyScheduleOptions(time) {
  const parsed = parseTime(time);
  if (!parsed) throw new Error(`Invalid time: ${time}`);
  const at = new Date();
  at.setHours(parsed.hour, parsed.minute, 0, 0);
  return {
    notifications: [
      {
        id: DAILY_NOTIFICATION_ID,
        title: "Weather Helper",
        body: "Checking today's best outdoor window…",
        schedule: { at, repeats: true, every: "day", allowWhileIdle: true },
      },
    ],
  };
}

export async function requestNotificationPermission() {
  const LocalNotifications = getPlugin("LocalNotifications");
  if (!LocalNotifications) return "granted";
  const status = await LocalNotifications.checkPermissions();
  if (status.display === "granted") return "granted";
  const requested = await LocalNotifications.requestPermissions();
  return requested.display;
}

export async function scheduleDailyNotification(time) {
  const LocalNotifications = getPlugin("LocalNotifications");
  if (!LocalNotifications) return;
  await LocalNotifications.cancel({ notifications: [{ id: DAILY_NOTIFICATION_ID }] });
  await LocalNotifications.schedule(buildDailyScheduleOptions(time));
}

export async function cancelDailyNotification() {
  const LocalNotifications = getPlugin("LocalNotifications");
  if (!LocalNotifications) return;
  await LocalNotifications.cancel({ notifications: [{ id: DAILY_NOTIFICATION_ID }] });
}

export async function applyNotificationSettings({ enabled, time }) {
  await saveNotificationSettings({ enabled, time });
  if (!enabled) {
    await cancelDailyNotification();
    return "disabled";
  }
  const permission = await requestNotificationPermission();
  if (permission !== "granted") return "denied";
  await scheduleDailyNotification(time);
  return "granted";
}

export async function initNotifications() {
  const enabled = await getNotificationsEnabled();
  if (!enabled) return;
  const time = await getNotificationTime();
  const permission = await requestNotificationPermission();
  if (permission === "granted") await scheduleDailyNotification(time);
}
