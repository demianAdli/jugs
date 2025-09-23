"""
JUGS project
jug_ee project
jugs_ee package
envelope_emission module
Project developer: Alireza Adli alireza.adli4@gmail.com
Theoritical Support: Mohammad Reza Seyedabadi 
"""


class EnvelopeEmission:
  def __init__(self,
               envelope_material_emission,
               envelope_thickness,
               envelope_surface,
               density):
    self._envelope_material_emission = envelope_material_emission
    self._envelope_thickness = envelope_thickness
    self._envelope_surface = envelope_surface
    self._density = density

  @property
  def envelope_material_emission(self):
    return self._envelope_material_emission

  @property
  def envelope_thickness(self):
    return self._envelope_thickness

  @property
  def envelope_surface(self):
    return self._envelope_surface

  @property
  def density(self):
    return self._density

  def calculate_envelope_emission(self):
    return self._envelope_material_emission * \
           self._envelope_thickness * \
           self._envelope_surface * \
           self._density
