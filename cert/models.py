from django.db import models
from django.contrib.auth.models import User
from subuser.models import SubUser
from actus.models import Actus


class Certificates(models.Model):
	TYPE_FUELS = (
		("b", "Бензин"),
		("g", "Газ"),
		("d", "Дизель"),
		("e", "Электро"),
	)

	TEST_LOCATIONS = (
		("kolik", "РК, г. Шымкент, Каратауский район, Квартал 216, уч. 312"),
	)

	TYPE_CATEGORY = (
		("M1", "M1 - легковые"),
		("M2", "M2 - пассажирские ТС (более восьми мест не превышает 5т)"),
		("M3", "M3 - пассажирские ТС (более восьми мест превышает 5т)"),
		("N1", "N1 - Грузовые тех. допус. макс. масса не более 3.5т"),
		("N2", "N2 - Грузовые тех. допус. макс. масса с выше 3.5т"),
		("N3", "N3 - Грузовые тех. допус. макс. масса более 12т"),
		("O1", "O1 - Прицепы, тех допус. макс. масса не более 0,75 т."),
		("O2", "O2 - Прицепы, тех допус. макс. масса свыше 0,75 т. но не более 3.5т"),
		("O3", "O3 - Прицепы, тех допус. макс. масса свыше 3,5 т. но не более 10т"),
		("O4", "O4 - Прицепы, тех допус. макс. масса более 10т"),
	)

	TYPE_VLD = (
		("FRONT", "Переднеприводная"),
		("REAR", "Заднеприводная"),
		("ALL", "Полноприводная"),
		
		("TRAILER", "Прицеп"),
		("TRAILER_T", "Прицеп Тентовонный"),
		("STRAILER", "Полуприцеп"),
		("STRAILER_T", "Полуприцеп Тентовонный"),
		("STRAILER_R", "Полуприцеп Рефрижератор"),
		("COE", "Кабина над двигателем"),
	)

	TYPE_ECO = (
		("E0", "Экологический класс 0"),
		("E1", "Экологический класс 1"),
		("E2", "Экологический класс 2"),
		("E3", "Экологический класс 3"),
		("E4", "Экологический класс 4"),
		("E5", "Экологический класс 5"),
		("E6", "Экологический класс 6"),
	)

	sbkts           = models.CharField(verbose_name="Номер", max_length=100)
	certCreateDate  = models.DateField(verbose_name="Дата сертификации")
	#logBookCreated  = models.DateField(verbose_name="Дата Журнала")

	# Car
	carMarka        = models.CharField(verbose_name="Марка", max_length=255)
	carModel        = models.CharField(verbose_name="Модель", max_length=255)
	carYear         = models.CharField(verbose_name="Год транспорта", max_length=255)
	carVin          = models.CharField(verbose_name="Вин-Код", max_length=255)
	carCategory     = models.CharField(verbose_name="Категория", max_length=255, choices=TYPE_CATEGORY, default="M1")
	carEco			= models.CharField(verbose_name="Эко класс", default="E5", max_length=255, choices=TYPE_ECO)
	carType         = models.CharField(verbose_name="Тип ТС", max_length=255, null=True)
	carGear			= models.CharField(verbose_name="Тип Передачи", max_length=255, default="")
	carManufacturer = models.TextField(verbose_name="Страна изготовителя")

	carWF 			= models.CharField(verbose_name="Колесная формула/ведущие колеса", max_length=255, default="")
	carVLD			= models.CharField(verbose_name="Схема компоновки транспортного средства", max_length=255, choices=TYPE_VLD)
	carEngLoc		= models.CharField(verbose_name="Расположение двигателя", max_length=255, default="")
	carBody			= models.CharField(verbose_name="Тип кузова/количество дверей", max_length=255, default="")
	carNSFR			= models.CharField(verbose_name="Количество мест спереди/сзади", max_length=255, default="")

	carWidth		= models.CharField(verbose_name="Ширина, мм", max_length=255,default="")
	carHeight		= models.CharField(verbose_name="Высота, мм", max_length=255,default="")
	carLength		= models.CharField(verbose_name="Длина, мм", max_length=255,default="")
	carBase 		= models.CharField(verbose_name="База, мм", max_length=255,default="")

	carWT 			= models.CharField(verbose_name="Колея (/) мм", max_length=255,default="")
	#carRWT 			= models.CharField(verbose_name="Колея задних колес, мм", max_length=255,default="")

	carEngine 		= models.CharField(verbose_name="Двигатель внутреннего сгорания (марка, тип)", max_length=255,default="")
	carEngineCount 	= models.CharField(verbose_name="количество и расположениецилиндров", max_length=255,default="")
	carEngineVolume = models.CharField(verbose_name="рабочий объем цилиндров, см3", max_length=255,default="")
	carEngineCR		= models.CharField(verbose_name="степень сжатия", max_length=255,default="")
	carEnginePower	= models.CharField(verbose_name="максимальная мощность, кВт", max_length=255,default="")
	carPowerType	= models.CharField(verbose_name="Система питания (тип)", max_length=255,default="")
	carIgnitionType = models.CharField(verbose_name="Система зажигания (тип)", max_length=255,default="", blank=True, null=True)
	#carFuel			= models.CharField(verbose_name="Топливо", max_length=255,default="")

	carEANS 		= models.CharField(verbose_name="Система выпуска и нейтрализации отработавших газов", max_length=255,default="")
	carTransmission = models.CharField(verbose_name="Трансмиссия", max_length=255, default="")
	carClutches 	= models.CharField(verbose_name="Сцепление (марка, тип)", max_length=255, default="", blank=True, null=True)
	carGearbox 		= models.CharField(verbose_name="Коробка передач (марка, тип)", max_length=255, default="")
	carSusFront 	= models.CharField(verbose_name="Подвеска передняя", max_length=255, default="")
	carSusRear		= models.CharField(verbose_name="Подвеска задняя", max_length=255, default="")

	# Подвеска для прицепа
	carSusTree	 	= models.CharField(verbose_name="Подвеска третий", max_length=255, default="-")
	carSusFour		= models.CharField(verbose_name="Подвеска четвертый", max_length=255, default="-")
	carSusFive		= models.CharField(verbose_name="Подвеска пятый", max_length=255, default="-")
	carSusSix		= models.CharField(verbose_name="Подвеска шестой", max_length=255, default="-")
	carSusSeven		= models.CharField(verbose_name="Подвеска седьмой", max_length=255, default="-")
	carSusEight		= models.CharField(verbose_name="Подвеска восьмой", max_length=255, default="-")

	carSC			= models.CharField(verbose_name="Рулевое управление (марка, тип)", max_length=255, default="")
	carBrakeWork	= models.CharField(verbose_name="Тормозная система рабочая", max_length=255, default="")
	carBrakeSpear 	= models.CharField(verbose_name="Тормозная система запасная", max_length=255, default="")
	carBrakeParking	= models.CharField(verbose_name="Тормозная система стояночная", max_length=255, default="")

	сarCabin 		= models.CharField(verbose_name="Кабина", max_length=255, default="")
	carDLS 			= models.CharField(verbose_name="Исполнение загрузочного пространства", max_length=255, default="")

	carMarkRefPlL 	= models.CharField(verbose_name="высота от опорной плоскости нижнего края государственного регистрационного знака", max_length=6, default="")
	carMarkRefPlH 	= models.CharField(verbose_name="высота от опорной плоскости верхнего края государственного регистрационного знака", max_length=6, default="")
	testMAUP		= models.CharField(verbose_name="Рег. знак обр углы вверх", max_length=6, default="")
	#testMADOWN		= models.CharField(verbose_name="Рег. знак обр углы вниз", max_length=6, default="")
	testMALEFT		= models.CharField(verbose_name="Рег. знак обр углы левый", max_length=6, default="")
	testMARIGHT		= models.CharField(verbose_name="Рег. знак обр углы правый", max_length=6, default="")

	# Person
	firstName       = models.CharField(verbose_name="Имя", max_length=255)
	lastName        = models.CharField(verbose_name="Фамилия", max_length=255)
	middleName      = models.CharField(verbose_name="Отчество", max_length=255, default="", blank=True)
	personId        = models.CharField(verbose_name="ИИН", max_length=255)
	personByW		= models.CharField(verbose_name="Кем выдан", max_length=255, default="")
	#personUid       = models.CharField(verbose_name="Номер паспорта", max_length=255, blank=True)
	#personIssueDate = models.DateField(verbose_name="Дата выдачи", max_length=255, blank=True)
	personAddress   = models.TextField(verbose_name="Фактический или Юридичиский адрес", blank=True)
	personPhone		= models.CharField(verbose_name="Номер телефона",  max_length=20, default="+7")
	personEmail		= models.CharField(verbose_name="Почта для входа в ЕКТРМ",  max_length=50, default="")
	personPassword	= models.CharField(verbose_name="Пароль для входа в ЕКТРМ",  max_length=50, default="")

	# Test
	testType 		= models.BooleanField(verbose_name="Эффект ноль 2", default=False)
	testFuelType	= models.CharField(verbose_name="Тип топливо", null=True, choices = TYPE_FUELS)
	testLocation    = models.CharField(verbose_name="Место проведение теста", max_length=255, choices=TEST_LOCATIONS, default="kolik")
	# TEMP
	testTemp        = models.CharField(verbose_name="Температура", max_length=255, null=True)
	testHum         = models.CharField(verbose_name="Влажность", max_length=255, null=True)
	testPress       = models.CharField(verbose_name="Атмосферное давления", max_length=255, null=True)

	# braking force
	testBWD         = models.CharField(verbose_name="Усилие на органе управления (педаль)", max_length=255, null=True, blank=True)
	testSPB			= models.CharField(verbose_name="Удельная тормозная сила рабочей тормозной системы (Коф)", max_length=255, null=True, blank=True)
	testCBDR        = models.CharField(verbose_name="Усилие на орган управления стояночный тормозной системы", default="")
	testCBDP        = models.CharField(verbose_name="Усилие на орган управления (ножного)", max_length=255, default="")
	#testNNCF		= models.CharField(verbose_name="Коэф. неравномер. передний оси", max_length=255, null=True, blank=True)
	#testNNCR		= models.CharField(verbose_name="Коэф. неравномер. задний оси", max_length=255, null=True, blank=True)

	# new model fields
	testUsilie    	= models.CharField(verbose_name="Усилие, прикладываемое к органу управления стояночной тормозной системы", max_length=255, null=True, blank=True)
	test_depth    	= models.CharField(verbose_name="Глубина протектора, мм", max_length=255, null=True, blank=True)
	#test_noise 		= models.CharField(verbose_name="Уровень шума, дБ", max_length=255, null=True, blank=True)
	#carBase 	= models.CharField(verbose_name="База, мм", max_length=255, default="")
	#testWheelBack = models.CharField(verbose_name="Колея задних колес, мм", max_length=255, default="")
	#testWheelFront = models.CharField(verbose_name="Колея передних колес, мм", max_length=255, default="")

	testFW			= models.CharField(verbose_name="Усилие на первый ось", max_length=255, null=True, blank=True)
	testSW			= models.CharField(verbose_name="Усилие на второй ось", max_length=255, null=True, blank=True)
	testTW			= models.CharField(verbose_name="Усилие на третий ось", max_length=255, default="")
	testFOW			= models.CharField(verbose_name="Усилие на четвертый ось", max_length=255, default="")
	testFIW			= models.CharField(verbose_name="Усилие на пятый ось", max_length=255, default="")

	# Car Mass
	testMass		= models.CharField(verbose_name="Масса транспорта", max_length=255, null=True)

	#testFAW			= models.CharField(verbose_name="Масса на передний ось", max_length=255, null=True, blank=True)
	#testRAW 		= models.CharField(verbose_name="Масса на задний ось", max_length=255, null=True, blank=True)

	testMaxMass		= models.CharField(verbose_name="Полная допустимая масса транспорта", max_length=255, null=True)

	# 
	testCoMin       = models.CharField(verbose_name="CO min", max_length=255, null=True, blank=True)
	testCoMax       = models.CharField(verbose_name="CO max", max_length=255, null=True, blank=True)

	testEF			= models.CharField(verbose_name="Дымность отработавших газов ТС с дизелями в режиме свободного ускорения, м-1:", max_length=255, null=True, blank=True)

	testEN          = models.CharField(verbose_name="Уровень шума выпуска газов дБ", max_length=255,null=True, blank=True)
	testALN			= models.CharField(verbose_name="Уровень регулировки ближнего света фар", max_length=255, null=True, blank=True)
	testLNR         = models.CharField(verbose_name="Ближний свет правый", max_length=255, null=True, blank=True)
	testLNL         = models.CharField(verbose_name="Ближний свет левый", max_length=255, null=True, blank=True)
	testMPLAR		= models.CharField(verbose_name="Левая сила света всех фар, кд.", max_length=255, null=True, blank=True)
	testMPLAL		= models.CharField(verbose_name="Правая сила света всех фар, кд.", max_length=255, null=True, blank=True)
	testMPLA 		= models.CharField(verbose_name="Максимальная сила света всех фар, кд.", max_length=255, null=True, blank=True)
	#testLD          = models.CharField(verbose_name="Дальний свет", max_length=255, null=True, blank=True)
	testFPM         = models.CharField(verbose_name="Частота проблесков в мин.", max_length=255, null=True, blank=True)
	testTSP         = models.CharField(verbose_name="Суммарный люфт в рул. упр.", max_length=255, null=True, blank=True)
	testLT          = models.CharField(verbose_name="Светопропускание, %", max_length=255, null=True, blank=True)

	testTH			= models.CharField(verbose_name="Высота протектора мм", max_length=255, null=True, blank=True)
	testTM			= models.CharField(verbose_name="Маркировка шины", max_length=255, null=True)

	testASR			= models.CharField(verbose_name="Показание борт сканера", max_length=255, null=True, blank=True)
	testBD			= models.CharField(verbose_name="Тормозной путь м", max_length=255, null=True, blank=True)
	testSD			= models.CharField(verbose_name="Установившееся замедление, м/с2", max_length=255, null=True, blank=True)
	testBSAT		= models.CharField(verbose_name="Время срабатывания тормозной системы, с", max_length=255, null=True, blank=True)

	testLTLG		= models.CharField(verbose_name="Светопропускание стекол левый", max_length = 4, default="")
	testLTWG		= models.CharField(verbose_name="Светопропускание стекол лобовой", max_length = 4, default="")
	testLTRG		= models.CharField(verbose_name="Светопропускание стекол правый", max_length = 4, default="")

	# User
	creator         = models.ForeignKey(SubUser, on_delete=models.CASCADE, verbose_name="Создатель", null=True)

	# Files
	decision        = models.FileField(upload_to="decisions/", verbose_name="Решение", null=True)
	application     = models.FileField(upload_to="applications/", verbose_name="Заявка", null=True)
	contract        = models.FileField(upload_to="contracts/", verbose_name="Договор", null=True)
	protocol        = models.FileField(upload_to="protocols/", verbose_name="Протокол", null=True)
	protocol_new 	= models.FileField(upload_to="protocols_new/", verbose_name="Протокол (новый)", null=True)
	expert			= models.FileField(upload_to="experts/", verbose_name="Тех спертификация", null=True)
	logbook			= models.FileField(upload_to="logbooks/", verbose_name="Журнал", null=True)
	conclusion      = models.FileField(upload_to="conclusions/",verbose_name="Заключение о соответствии",null=True)
	conclusionNumber = models.IntegerField(null=True, blank=True, verbose_name="Номер заключения")
	journal_c00395 = models.FileField(upload_to="journal_main/", verbose_name="Журнал Основной", null=True, blank=True)                                                                                                    
	protocol_c00395 = models.FileField(upload_to="protocol_main/", verbose_name="Протокол Основной", null=True, blank=True)

	# Signature
	signature		= models.ImageField(upload_to="signatures/", null=True, verbose_name="Подпись клиента")

	linkVideo		= models.URLField("Ссылка на видео", max_length=255, blank=True, null=True, unique=True)

	actus 			= models.OneToOneField(Actus, on_delete=models.CASCADE, verbose_name="Акт", null=True, blank=True)
	device 			= models.TextField(verbose_name="Дополнительное оборудование транспортного средства (прицеп)", default="-")

	app1			= models.ImageField(upload_to="apps/", null=True, verbose_name="Приложение 1")
	app2			= models.ImageField(upload_to="apps/", null=True, verbose_name="Приложение 2")
	app3			= models.ImageField(upload_to="apps/", null=True, blank=True, verbose_name="Приложение 3")
	app4			= models.ImageField(upload_to="apps/", null=True, blank=True, verbose_name="Приложение 4")
	app5			= models.ImageField(upload_to="apps/", null=True, blank=True, verbose_name="Приложение 5")
	app6			= models.ImageField(upload_to="apps/", null=True, blank=True, verbose_name="Приложение 6")
	app7			= models.ImageField(upload_to="apps/", null=True, blank=True, verbose_name="Приложение 7")
	app8			= models.ImageField(upload_to="apps/", null=True, blank=True, verbose_name="Приложение 8")
	app9			= models.ImageField(upload_to="apps/", null=True, blank=True, verbose_name="Приложение 9")
	app10			= models.ImageField(upload_to="apps/", null=True, blank=True, verbose_name="Приложение 10")

	# Utils
	isClose         = models.BooleanField(verbose_name="Статус", null=True)

class Meta:
	verbose_name = "Сертификат"
	verbose_name_plural = "Сертифицация"

	def __str__(self):
		return f"Сертификат №:{self.sbkts}"