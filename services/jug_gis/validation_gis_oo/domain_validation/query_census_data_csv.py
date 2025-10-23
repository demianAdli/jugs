class QueryCensusDataCSV:
  def __init__(self, census_data):
    self.census_data = census_data

  def census_code_units_num(self, census_code_field_title,
                            cencus_code_units_num_field_title,
                            census_code):
    return self.census_data.loc[
      self.census_data[
        census_code_field_title].eq(census_code),
      cencus_code_units_num_field_title].iloc[0]
