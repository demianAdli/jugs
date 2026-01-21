class QueryCensusDataCSV:
  def __init__(self,
               census_data,
               census_code_field_title,
               cencus_code_units_num_field_title):

    self.lookup = (
      census_data
        .set_index(census_code_field_title, drop=True)
      [cencus_code_units_num_field_title]
    )

  def census_code_units_num(self, census_code):
    return self.lookup.get(census_code)
