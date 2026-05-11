from import_export import resources
from import_export.fields import Field
from import_export.widgets import ForeignKeyWidget
from .models import *
from datetime import datetime

class ButtonResource(resources.ModelResource):
	# def __init__(self, **kwargs):
	# 	self.user = kwargs.get("user")
		
	def before_save_instance(self, instance, using_transactions, dry_run):
		instance.createDate = datetime.now()

	class Meta:
		model = Button
		import_id_fields = ('iccid',)
		fields = ('iccid', 'imei', 'serial','createDate', 'hwname', 'user')


class ActusResourse(resources.ModelResource):
	vincode = Field(attribute='carVincode', column_name='Вин-код')
	iccid = Field(attribute='button', column_name='ICCID', 
                  widget=ForeignKeyWidget(Button, field='iccid'))
	

	hwname = Field(attribute='button', column_name='Наименование оборудование', 
                   widget=ForeignKeyWidget(Button, field='hwname'))

	class Meta:
		model = Actus
		fields = ('vincode','carMarka','iccid','createDate', 'carColor', 'carYear', 'hwname', 'isRegistred')
		export_order = ('iccid', 'vincode', 'isRegistred','carMarka','carColor', 'carYear', 'hwname')

class ActusReportResourse(resources.ModelResource):
	vincode = Field(attribute='carVincode', column_name='Вин-код')
	iccid = Field(attribute='button', column_name='ICCID', 
                  widget=ForeignKeyWidget(Button, field='iccid'))
	

	hwname = Field(attribute='button', column_name='Наименование оборудование', 
                   widget=ForeignKeyWidget(Button, field='hwname'))

	class Meta:
		model = Actus
		name = "Экспорт для отчета"
		fields = ('vincode','carMarka','iccid','frln', 'personUid', 'createDate', 'carColor', 'carYear', 'hwname', 'isRegistred')
		export_order = ('iccid', 'vincode', 'frln', 'personUid', 'isRegistred','carMarka','carColor', 'carYear', 'hwname')
