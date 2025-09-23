"""
JUGS project
jug_ee project
jugs_ee package
opening_emission module
Returns the summarize of all surfaces openings' emissions
The returned value will be used to calculate the building component emission.
Project developer: Alireza Adli alireza.adli4@gmail.com
Theoritical Support: Mohammad Reza Seyedabadi 
"""


class OpeningEmission:
  def __init__(self, opening_material_emission, opening_surface):
    self._opening_material_emission = opening_material_emission
    self._opening_surface = opening_surface

  @property
  def opening_material_emission(self):
    return self._opening_material_emission

  @property
  def opening_surface(self):
    return self._opening_surface

  def calculate_opening_emission(self):
    return self._opening_material_emission * self._opening_surface
