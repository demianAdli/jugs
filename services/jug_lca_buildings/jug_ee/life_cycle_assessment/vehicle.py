"""
JUGS project
jug_lca_buildings package
vehicle module
Project developer: Alireza Adli alireza.adli4@gmail.com
Theoritical Support for LCA emissions: Mohammad Reza Seyedabadi
"""


class Vehicle:
  def __init__(self, vehicle_id, name, fuel_consumption_rate,
               fuel_consumption_unit, carbon_emission_factor,
               carbon_emission_unit):
    self._vehicle_id = vehicle_id
    self._name = name
    self._fuel_consumption_rate = fuel_consumption_rate
    self._fuel_consumption_unit = fuel_consumption_unit
    self._carbon_emission_factor = carbon_emission_factor
    self._carbon_emission_unit = carbon_emission_unit

  @property
  def id(self):
    return self._vehicle_id

  @property
  def name(self):
    return self._name

  @property
  def fuel_consumption_rate(self):
    return self._fuel_consumption_rate

  @property
  def fuel_consumption_unit(self):
    return self._fuel_consumption_unit

  @property
  def carbon_emission_factor(self):
    return self._carbon_emission_factor

  @property
  def carbon_emission_unit(self):
    return self._carbon_emission_unit

  def total_vehicle_emission(self):
    return self._fuel_consumption_rate * self._carbon_emission_factor
