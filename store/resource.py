from import_export import resources
#from import_export.fields import Field
#from import_export.widgets import ForeignKeyWidget
from .models import *

class StoreResource(resources.ModelResource):
	# def __init__(self, **kwargs):
	# 	self.user = kwargs.get("user")
		
	# def before_save_instance(self, instance, using_transactions, dry_run):
	# 	instance.createDate = datetime.now()

	class Meta:
		model = Store
		import_id_fields = ('id',)
		fields = ('id', 'typ', 'amount', 'name', 'brand', 'model', 'serial', 'creator','location', 'qrcode')