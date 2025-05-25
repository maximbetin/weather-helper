"""
Defines the Location class and the dictionary of known locations.
"""


class Location:
  def __init__(self, key, name, lat, lon):
    self.key = key
    self.name = name
    self.lat = lat
    self.lon = lon


# Define locations in Asturias
LOCATIONS = {
    "gijon": Location("gijon", "Gijón", 43.5322, -5.6611),
    "oviedo": Location("oviedo", "Oviedo", 43.3619, -5.8494),
    "llanes": Location("llanes", "Llanes", 43.4200, -4.7550),
    "aviles": Location("aviles", "Avilés", 43.5547, -5.9248),
    "somiedo": Location("somiedo", "Somiedo", 43.0981, -6.2550),
    "teverga": Location("teverga", "Teverga", 43.1578, -6.0867),
    "taramundi": Location("taramundi", "Taramundi", 43.3583, -7.1083),
    "ribadesella": Location("ribadesella", "Ribadesella", 43.4675, -5.0553),
    "tapia": Location("tapia", "Tapia de Casariego", 43.5700, -6.9436),
    "cangas_de_onis": Location("cangas_de_onis", "Cangas de Onís", 43.3507, -5.1356),
    "lagos_covadonga": Location("lagos_covadonga", "Lagos de Covadonga", 43.2728, -4.9906),
}
