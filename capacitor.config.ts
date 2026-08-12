import type { CapacitorConfig } from "@capacitor/cli";

const config: CapacitorConfig = {
  appId: "com.maximbk.weatherhelper",
  appName: "Weather Helper",
  webDir: "dist",
  bundledWebRuntime: false,
  plugins: {
    CapacitorHttp: {
      enabled: true,
    },
    // Runs roughly once a day (measured from whenever the app is backgrounded, not a
    // fixed wall-clock time, and subject to OS battery-optimization heuristics) plus
    // whenever notifications.js dispatches "updateNotificationSettings" on a settings
    // change. Each run computes fresh recommendation text and arms a precise
    // CapacitorNotifications alarm (id 1001) for the next occurrence of the user's
    // chosen wall-clock time — this task owns both the content and the exact firing
    // time; no other scheduler is involved.
    BackgroundRunner: {
      label: "com.maximbk.weatherhelper.dailyforecast",
      src: "js/background-task.js",
      event: "dailyForecastCheck",
      repeat: true,
      interval: 1440,
      autoStart: true,
    },
  },
};

export default config;
