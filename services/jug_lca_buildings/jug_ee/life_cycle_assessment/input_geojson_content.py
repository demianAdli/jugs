"""
JUGS project
jug_ee project
jug_ee package
input_geojson_content module
Returns a temporary path to input the GeometryFactory
Project developer: Alireza Adli alireza.adli4@gmail.com
"""
import tempfile
import json


class InputGeoJsonContent:
  def __init__(self, content):
    self.content = content

  @property
  def content(self):
    return self._content

  @content.setter
  def content(self, content):
    if isinstance(content, str):
      self._content = content
    else:
      temp_file = \
        tempfile.NamedTemporaryFile(
          delete=False, suffix='.geojson', mode='w', encoding='utf8')
      try:
        json.dump(content, temp_file)
        temp_file.flush()
        self._content = temp_file.name
      finally:
        temp_file.close()
