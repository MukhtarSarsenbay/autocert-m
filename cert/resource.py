from import_export import resources, fields
from .models import Certificates


class CertResourse(resources.ModelResource):
# 	vincode = Field(attribute='carVincode', column_name='Вин-код')
# 	iccid = Field(attribute='button', column_name='ICCID', 
#                   widget=ForeignKeyWidget(Button, field='iccid'))
	

# 	hwname = Field(attribute='button', column_name='Наименование оборудование', 
#                    widget=ForeignKeyWidget(Button, field='hwname'))

	marka_full = fields.Field(column_name='Продукция')
	full_name = fields.Field(column_name='Заявитель')
	description = fields.Field(column_name='Примечание')

	class Meta:
		model = Certificates
		fields = ('certCreateDate', 'marka_full', 'carVin', 'full_name', 'sbkts', 'sbkts', 'description')
		export_order = ('certCreateDate', 'marka_full', 'carVin', 'full_name', 'sbkts', 'sbkts', 'description')
		#fields = ('vincode','carMarka','iccid','createDate', 'carColor', 'carYear', 'hwname', 'isRegistred')
		#export_order = ('iccid', 'vincode', 'isRegistred','carMarka','carColor', 'carYear', 'hwname')

	def dehydrate_marka_full(self, obj):
		return f"{obj.carMarka} {obj.carModel}"

	def dehydrate_full_name(self, obj):
		return f"{obj.lastName} {obj.firstName} {obj.middleName}"

	def dehydrate_description(self, obj):
		return ""
