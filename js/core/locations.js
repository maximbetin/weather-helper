function loc(key, name, lat, lon) {
  return { key, name, lat, lon };
}

// Asturias only, on purpose: this app answers "where should I go today?" for
// places within a day trip, so other regions were dropped rather than kept as
// unused browsing options.
export const LOCATIONS = {
  arriondas: loc("arriondas", "Arriondas", 43.3892, -5.1908),
  gijon: loc("gijon", "Gijón", 43.5322, -5.661),
  oviedo: loc("oviedo", "Oviedo", 43.3623, -5.8485),
  llanes: loc("llanes", "Llanes", 43.4211, -4.7562),
  aviles: loc("aviles", "Avilés", 43.5567, -5.9256),
  luarca: loc("luarca", "Luarca", 43.542, -6.5359),
  luanco: loc("luanco", "Luanco", 43.6137, -5.7929),
  salinas: loc("salinas", "Salinas", 43.5753, -5.9585),
  cudillero: loc("cudillero", "Cudillero", 43.5629, -6.1453),
  ribadesella: loc("ribadesella", "Ribadesella", 43.4631, -5.0567),
  cangas_de_onis: loc("cangas_de_onis", "Cangas de Onís", 43.3514, -5.1292),
  villaviciosa: loc("villaviciosa", "Villaviciosa", 43.4814, -5.4356),
  lastres: loc("lastres", "Lastres", 43.5135, -5.2696),
};
