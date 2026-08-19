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
    // Wakes roughly hourly (subject to OS battery-optimization heuristics), plus
    // whenever notifications.js dispatches "updateNotificationSettings". Most wake-ups
    // do nothing: the task only fetches forecasts inside a window around the user's
    // chosen reminder time, then arms a single CapacitorNotifications alarm (id 1001)
    // for today, and records the date so it runs at most once per day. The hourly
    // cadence exists so the forecast used is recent, not so it polls the API hourly.
    BackgroundRunner: {
      label: "com.maximbk.weatherhelper.dailyforecast",
      src: "js/background-task.js",
      event: "dailyForecastCheck",
      repeat: true,
      interval: 60,
      autoStart: true,
    },
  },
};

export default config;
