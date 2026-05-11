from django.db import models
from django.contrib.auth.models import User
from subuser.models import SubUser

class Actus(models.Model):
	number 			= models.IntegerField(verbose_name="Номер акта", blank=True)
	cost 			= models.CharField(verbose_name="Цена", default="")
	button			= models.ForeignKey('Button', on_delete=models.CASCADE, verbose_name="Кнопка",unique=True, null=True)
	carMarka 		= models.CharField(verbose_name="Марка и модель машины", max_length=200)
	carVincode 		= models.CharField(verbose_name="VINCODE", max_length=50, unique=True)
	carYear			= models.CharField(verbose_name="Год выпуска", max_length=5)
	carColor		= models.CharField(verbose_name="Цвет ТС", max_length=30, default="")
	frln 			= models.CharField(verbose_name="ФИО", max_length=255)
	personUid 		= models.CharField(verbose_name="ИИН", max_length=50)
	personNumber 	= models.CharField(verbose_name="Номер УД", max_length=50, null=True, blank=True)
	personPublic 	= models.DateField(verbose_name="Дата выдачи",blank=True,null=True)
	address 		= models.TextField(verbose_name="Адресс")
	personPhone 	= models.CharField(verbose_name="Номер телефон", max_length=20, default="+7")
	createDate 		= models.DateTimeField(verbose_name="Дата создание акта", auto_now_add=True)
	creator			= models.ForeignKey(SubUser, on_delete=models.CASCADE, verbose_name="Создатель", null=True)

	act 			= models.FileField(upload_to="act/", verbose_name="Акт", null=True)
	contract 		= models.FileField(upload_to="act/", verbose_name="Договор", null=True)

	app1			= models.FileField(upload_to="apps/", verbose_name="Приложения 1", null=True)
	app2			= models.FileField(upload_to="apps/", verbose_name="Приложения 2", null=True, blank=True)
	app3			= models.FileField(upload_to="apps/", verbose_name="Приложения 3", null=True, blank=True)

	isClose 		= models.BooleanField(default=False, verbose_name="Закончен")
	isRegistred		= models.CharField(default="-", verbose_name="Регистрация")
	isCalled		= models.CharField(default="-", verbose_name="Прозвон")

	def __str__(self):
		return f"{self.number}) {self.carVincode} - {self.frln}"

	class Meta:
		verbose_name = "АКТ"
		verbose_name_plural = "АКТЫ"

class ActusPending(Actus):
    class Meta:
        proxy = True


class Button(models.Model):
	iccid 	= models.CharField(unique=True, verbose_name="ICCID", max_length=50)
	imei  	= models.CharField(unique=True, null=True, blank=True, verbose_name="IMEI", max_length=50)
	serial 	= models.CharField(unique=True, null=True, blank=True, verbose_name="S/N", max_length=50)
	hwname 	= models.CharField(verbose_name="Имя оборудование", max_length=100)
	user 	= models.ForeignKey(SubUser, on_delete=models.CASCADE, verbose_name="Присвоин", null=True)
	createDate = models.DateField(verbose_name="Дата создание кнопки", auto_now_add=True, null=True)


	def __str__(self):
		return f"{self.iccid}, {self.imei}, {self.serial}, {self.hwname}"

	class Meta:
		verbose_name = "Кнопка"
		verbose_name_plural = "Кнопки"


