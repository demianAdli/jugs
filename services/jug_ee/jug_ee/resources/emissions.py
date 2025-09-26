from flask import request, jsonify
from flask.views import MethodView
from flask_smorest import Blueprint, abort

from jug_ee.schemas.schemas import LCAInputDataSchema

from jug_ee.lca_carbon_workflow import LCACarbonWorkflow

blp = Blueprint('Emissions', 
                __name__, 
                description='Exporting embodied and end-of-life ' \
                'emissions data for buildings')



@blp.route("/emissions")
class Emissions(MethodView):
    @blp.arguments(LCAInputDataSchema)
    def post(self, request_city):
        try:
            emissions_data = LCACarbonWorkflow(request_city,
                                               'nrcan_archetypes.json', 
                                               'nrcan_constructions_cap_3.json'
                                               ).export_emissions()
            return jsonify(emissions_data), 201
        except Exception as e:
            abort(500, message=str(e))
