import { ForecastViewModel } from "./view_model.js";
import { ACTIVITY_PROFILE_LABELS } from "./core/scoring.js";
import { LOCATION_GROUPS } from "./core/locations.js";
import { formatDate, getRatingColor, getRatingBackground } from "./core/presentation.js";
import { installBackButtonHandler } from "../native-bridge.js";
import { getNotificationTime, getNotificationsEnabled, applyNotificationSettings, initNotifications } from "./notifications.js";

const $ = (id) => document.getElementById(id);

function create(tag, props = {}, children = []) {
  const el = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (key === "className") el.className = value;
    else if (key === "textContent") el.textContent = value;
    else if (key === "dataset") Object.assign(el.dataset, value);
    else if (key === "ariaLabel") el.setAttribute("aria-label", value);
    else if (key.startsWith("on") && typeof value === "function") el.addEventListener(key.slice(2).toLowerCase(), value);
    else if (value !== undefined && value !== null) el.setAttribute(key, value);
  }
  for (const child of children) {
    if (child === null || child === undefined) continue;
    el.appendChild(typeof child === "string" ? document.createTextNode(child) : child);
  }
  return el;
}

const vm = new ForecastViewModel();

const groupSelect = $("group-select");
const profileSelect = $("profile-select");
const dateSelect = $("date-select");
const refreshButton = $("refresh-button");
const loadProgress = $("load-progress");
const statusText = $("status-text");
const rankingList = $("ranking-list");
const showAllButton = $("show-all-button");
const detailsPanel = $("details-panel");
const selectedSummary = $("selected-summary");
const hourlyList = $("hourly-list");
const settingsButton = $("settings-button");
const settingsCloseButton = $("settings-close-button");
const settingsPanel = $("settings-panel");
const notifyEnabled = $("notify-enabled");
const notifyTime = $("notify-time");
const notifyStatus = $("notify-status");
const notifySaveButton = $("notify-save-button");

function populateStaticOptions() {
  groupSelect.replaceChildren(...Object.keys(LOCATION_GROUPS).map((name) => create("option", { value: name, textContent: name })));
  groupSelect.value = vm.groupName;

  profileSelect.replaceChildren(
    ...Object.entries(ACTIVITY_PROFILE_LABELS).map(([key, label]) => create("option", { value: key, textContent: label })),
  );
  profileSelect.value = vm.activityProfile;
}

function updateDateOptions() {
  const dates = vm.availableDates();
  dateSelect.replaceChildren(...dates.map((d) => create("option", { value: d, textContent: formatDate(d) })));
  dateSelect.disabled = dates.length === 0;
  if (vm.selectedDate) dateSelect.value = vm.selectedDate;
}

function rankCard(item) {
  const isSelected = item.locationKey === vm.selectedLocationKey;
  return create(
    "button",
    {
      className: isSelected ? "rank-card selected" : "rank-card",
      type: "button",
      "aria-pressed": String(isSelected),
      onclick: () => selectLocation(item.locationKey),
    },
    [
      create("span", { className: "rank-badge", textContent: String(item.rank) }),
      create("div", { className: "rank-main" }, [
        create("div", { className: "rank-name", textContent: item.locationName }),
        create("div", { className: "rank-window", textContent: item.bestWindow || "No consistent window today" }),
      ]),
      create("div", { className: "rank-score" }, [
        create("span", { className: "score-value", textContent: item.normalizedScore ?? "N/A", style: `color:${getRatingColor(item.rating)}` }),
        create("span", { className: "rating-label", textContent: item.rating, style: `color:${getRatingColor(item.rating)}` }),
      ]),
    ],
  );
}

let showAllResults = false;
const RANKING_PREVIEW_COUNT = 5;

function renderRanking() {
  const total = Object.keys(vm.forecasts).length || 1;
  const items = vm.rankedLocations(showAllResults ? total : RANKING_PREVIEW_COUNT);

  if (items.length === 0) {
    rankingList.replaceChildren(create("p", { className: "empty-state", textContent: "No ranked locations for this date." }));
  } else {
    rankingList.replaceChildren(...items.map((item) => rankCard(item)));
  }

  showAllButton.hidden = total <= RANKING_PREVIEW_COUNT;
  showAllButton.textContent = showAllResults ? `Show top ${RANKING_PREVIEW_COUNT} only` : `Show all ${total} locations`;
}

function hourlyRow(hour) {
  return create("div", { className: "hourly-row", style: `border-left-color:${getRatingColor(hour.rating)}` }, [
    create("span", { className: "hourly-time", textContent: hour.time }),
    create("div", { className: "hourly-metrics" }, [
      create("span", { textContent: `Temp ${hour.temperature}` }),
      create("span", { textContent: `Wind ${hour.wind}` }),
      create("span", { textContent: `Clouds ${hour.clouds}` }),
      create("span", { textContent: `Rain ${hour.precipitation}` }),
      create("span", { textContent: `Humidity ${hour.humidity}` }),
    ]),
    create("span", { className: "hourly-score", textContent: hour.normalizedScore, style: `color:${getRatingColor(hour.rating)}` }),
  ]);
}

function renderDetails() {
  const location = vm.selectedLocation();
  if (!location) {
    detailsPanel.hidden = true;
    selectedSummary.replaceChildren();
    hourlyList.replaceChildren();
    return;
  }

  detailsPanel.hidden = false;
  detailsPanel.style.backgroundColor = getRatingBackground(location.rating);
  detailsPanel.style.borderColor = getRatingColor(location.rating);

  selectedSummary.replaceChildren(
    ...[
      create("div", { className: "score-big", textContent: location.normalizedScore ?? "N/A", style: `color:${getRatingColor(location.rating)}` }),
      create("div", { className: "rating-label", textContent: `${location.rating} · ${location.locationName}` }),
      location.bestWindow ? create("div", { className: "best-window", textContent: `Best window: ${location.bestWindow}` }) : null,
      create("div", { className: "best-window-details", textContent: location.bestWindowDetails }),
    ].filter((node) => node !== null),
  );

  const hours = vm.hourlyForecast(location.locationKey);
  hourlyList.replaceChildren(...(hours.length > 0 ? hours.map(hourlyRow) : [create("p", { className: "empty-state", textContent: "No hourly data." })]));
}

function renderDashboard() {
  renderRanking();
  renderDetails();
}

function selectLocation(locationKey) {
  vm.selectLocation(locationKey);
  renderDetails();
  renderRanking();
  detailsPanel.scrollIntoView({ behavior: "smooth", block: "start" });
}

function setStatus(text) {
  statusText.textContent = text;
}

async function refreshForecast() {
  refreshButton.disabled = true;
  groupSelect.disabled = true;
  loadProgress.hidden = false;
  setStatus("Loading forecast…");
  try {
    const { forecasts, errors } = await vm.load();
    const loadedCount = Object.keys(forecasts).length;
    const errorCount = Object.keys(errors).length;
    setStatus(errorCount > 0 ? `Loaded ${loadedCount} location(s), ${errorCount} failed.` : `Loaded ${loadedCount} location(s).`);
  } catch {
    setStatus("Could not load this forecast. Please try again.");
  } finally {
    refreshButton.disabled = false;
    groupSelect.disabled = false;
    loadProgress.hidden = true;
    showAllResults = false;
    updateDateOptions();
    renderDashboard();
  }
}

async function openSettings() {
  notifyEnabled.checked = await getNotificationsEnabled();
  notifyTime.value = await getNotificationTime();
  notifyStatus.textContent = "";
  settingsPanel.hidden = false;
}

function closeSettings() {
  settingsPanel.hidden = true;
}

async function saveSettings() {
  notifySaveButton.disabled = true;
  notifyStatus.textContent = "Saving…";
  try {
    const result = await applyNotificationSettings({ enabled: notifyEnabled.checked, time: notifyTime.value });
    if (result === "denied") {
      notifyStatus.textContent = "Notification permission denied. Enable it in Android settings.";
    } else if (result === "disabled") {
      notifyStatus.textContent = "Daily reminder turned off.";
    } else {
      // Android only guarantees exact delivery when "Alarms & reminders" is granted,
      // so promise an approximate time rather than the exact minute.
      notifyStatus.textContent = `Daily reminder set for around ${notifyTime.value}. Android may delay it slightly.`;
    }
  } catch (error) {
    const detail = error?.message ? ` (${error.message})` : "";
    notifyStatus.textContent = `Could not save settings. Please try again.${detail}`;
  } finally {
    notifySaveButton.disabled = false;
  }
}

function initialiseUi() {
  populateStaticOptions();

  groupSelect.addEventListener("change", () => {
    vm.selectGroup(groupSelect.value);
    refreshForecast();
  });

  profileSelect.addEventListener("change", () => {
    vm.selectActivityProfile(profileSelect.value);
    renderDashboard();
  });

  dateSelect.addEventListener("change", () => {
    vm.selectDate(dateSelect.value);
    renderDashboard();
  });

  refreshButton.addEventListener("click", () => refreshForecast());

  showAllButton.addEventListener("click", () => {
    showAllResults = !showAllResults;
    renderRanking();
  });

  settingsButton.addEventListener("click", () => openSettings());
  settingsCloseButton.addEventListener("click", () => closeSettings());
  notifySaveButton.addEventListener("click", () => saveSettings());

  installBackButtonHandler();
  initNotifications();
  refreshForecast();
}

initialiseUi();
