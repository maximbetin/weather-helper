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
    // fixed wall-clock time, and subject to OS battery-optimization heuristics) to
    // refresh notification id 1001 with real recommendation text. The LocalNotifications
    // alarm scheduled by notifications.js is what fires at the user's chosen wall-clock
    // time; this task's job is only to keep that notification's content fresh.
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
