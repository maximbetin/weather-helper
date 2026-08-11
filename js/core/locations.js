function loc(key, name, lat, lon) {
  return { key, name, lat, lon };
}

export const ASTURIAS_LOCATIONS = {
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

export const SPAIN_OTHER_LOCATIONS = {
  alicante: loc("alicante", "Alicante", 38.3452, -0.483),
  madrid: loc("madrid", "Madrid", 40.4165, -3.7026),
  barcelona: loc("barcelona", "Barcelona", 41.3888, 2.159),
  valencia: loc("valencia", "Valencia", 39.4699, -0.3763),
  sevilla: loc("sevilla", "Sevilla", 37.3891, -5.9845),
  granada: loc("granada", "Granada", 37.1882, -3.6067),
  malaga: loc("malaga", "Málaga", 36.7213, -4.4214),
  cordoba: loc("cordoba", "Córdoba", 37.8882, -4.7794),
  zaragoza: loc("zaragoza", "Zaragoza", 41.6488, -0.8891),
  murcia: loc("murcia", "Murcia", 37.9922, -1.1307),
  valladolid: loc("valladolid", "Valladolid", 41.6523, -4.7245),
  bilbao: loc("bilbao", "Bilbao", 43.263, -2.935),
  palma: loc("palma", "Palma", 39.5696, 2.6502),
  tenerife: loc("tenerife", "Tenerife", 28.4636, -16.2518),
  las_palmas: loc("las_palmas", "Las Palmas", 28.1235, -15.4363),
  almeria: loc("almeria", "Almería", 36.83, -2.43),
  salobrena: loc("salobrena", "Salobreña", 36.7432, -3.5866),
  almunecar: loc("almunecar", "Almuñécar", 36.7339, -3.6907),
  motril: loc("motril", "Motril", 36.746, -3.5204),
};

export const WORLDWIDE_OTHER_LOCATIONS = {
  london: loc("london", "London", 51.5074, -0.1278),
  paris: loc("paris", "Paris", 48.8566, 2.3522),
  new_york: loc("new_york", "New York", 40.7128, -74.006),
  tokyo: loc("tokyo", "Tokyo", 35.6762, 139.6503),
  berlin: loc("berlin", "Berlin", 52.52, 13.405),
  rome: loc("rome", "Rome", 41.9028, 12.4964),
  amsterdam: loc("amsterdam", "Amsterdam", 52.3676, 4.9041),
  prague: loc("prague", "Prague", 50.088, 14.4208),
  lisbon: loc("lisbon", "Lisbon", 38.7223, -9.1393),
  houston: loc("houston", "Houston", 29.7604, -95.3698),
  rio_de_janeiro: loc("rio_de_janeiro", "Rio de Janeiro", -22.9068, -43.1729),
  buenos_aires: loc("buenos_aires", "Buenos Aires", -34.6037, -58.3816),
};

export const SPAIN_LOCATIONS = { ...SPAIN_OTHER_LOCATIONS };
export const WORLDWIDE_LOCATIONS = { ...WORLDWIDE_OTHER_LOCATIONS, madrid: SPAIN_OTHER_LOCATIONS.madrid };

export const LOCATION_GROUPS = {
  Asturias: ASTURIAS_LOCATIONS,
  Spain: SPAIN_LOCATIONS,
  Worldwide: WORLDWIDE_LOCATIONS,
};

export const LOCATIONS = ASTURIAS_LOCATIONS;
