
from dash.data_models import Farmer


class Logic():
    def __init__(self):
        """
        Constructor
        """
        farmers = Farmer.query.all()
        for f in farmers:
            print(f.id, f.name)

    def getFarmersList():
        farmers = Farmer.query.all()
        for f in farmers:
            print(f.id, f.name)
