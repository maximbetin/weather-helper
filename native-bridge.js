export const isNativeAndroid = () => Boolean(globalThis.Capacitor?.isNativePlatform?.());

const plugins = () => {
  const capacitor = globalThis.Capacitor;
  if (!capacitor) return {};
  return {
    App: capacitor.registerPlugin?.("App") || capacitor.Plugins?.App,
    Preferences: capacitor.registerPlugin?.("Preferences") || capacitor.Plugins?.Preferences,
    BackgroundRunner: capacitor.registerPlugin?.("BackgroundRunner") || capacitor.Plugins?.BackgroundRunner,
  };
};

export function getPlugin(name) {
  return plugins()[name];
}

export function installBackButtonHandler() {
  if (!isNativeAndroid()) return;
  plugins().App?.addListener?.("backButton", ({ canGoBack }) => {
    if (canGoBack && globalThis.history.length > 1) {
      globalThis.history.back();
    } else {
      plugins().App?.exitApp?.();
    }
  });
}
