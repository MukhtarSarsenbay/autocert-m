from subuser.models import SubUser
from django.contrib.auth.models import User


from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie

from .models import Certificates
from .serializers import CertModelSerializer, ImageModelSerializer

from django.http import HttpResponse

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication, permissions

from rest_framework import status

from rest_framework.parsers import MultiPartParser, FormParser

from docxtpl import DocxTemplate
from docx import Document
from docx.shared import Inches

import requests

from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent

import os

from .utils import convert_to

from requests.auth import HTTPBasicAuth

import copy

from datetime import timedelta
from subuser.models import SubUser, Profile
from testlog.models import TestLog 
                                                                                                                                                           
from rest_framework import permissions, status 

headers = {
    'Content-Type': 'application/json',
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
}

month_to_string = {
	1: "января",
	2: "февраля",
	3: "марта",
	4: "апреля",
	5: "мая",
	6: "июня",
	7: "июля",
	8: "августа",
	9: "сентября",
	10: "октября",
	11: "ноября",
	12: "декабря"
}

def set_img(tag, path, document):
    for par in document.paragraphs:
        if tag in par.text:
            # Разбиваем параграф на части, заменяя тег
            text_before, text_after = par.text.split(tag, 1)
            par.text = text_before  # Оставляем текст перед тегом
            # Добавляем изображение
            run = par.add_run()
            run.add_picture(path, width=Inches(3))
            # Добавляем оставшийся текст
            par.add_run(text_after)
            break

def replace_all(obj, render, model):
	render.replace_pic("sign.png", copy.deepcopy(obj.creator.sign))
	# if obj.app1: model["[F1]"] = InlineImage(render, image_descriptor=obj.app1, width=Mm(20))
	# if obj.app2: model["[F2]"] = InlineImage(render, image_descriptor=obj.app2, width=Mm(20))
	# if obj.app3: model["[F3]"] = InlineImage(render, image_descriptor=obj.app3, width=Mm(20))
	# if obj.app4: model["[F4]"] = InlineImage(render, image_descriptor=obj.app4, width=Mm(20))
	# if obj.app5: model["[F5]"] = InlineImage(render, image_descriptor=obj.app5, width=Mm(20))
	# if obj.app6: model["[F6]"] = InlineImage(render, image_descriptor=obj.app6, width=Mm(20))
	# if obj.app7: model["[F7]"] = InlineImage(render, image_descriptor=obj.app7, width=Mm(20))
	# if obj.app8: model["[F8]"] = InlineImage(render, image_descriptor=obj.app8, width=Mm(20))
	# if obj.app9: model["[F9]"] = InlineImage(render, image_descriptor=obj.app9, width=Mm(20))
	# if obj.app10: model["[F10]"] = InlineImage(render, image_descriptor=obj.app10, width=Mm(20))

	return model

def certificates_callback_cert(request):
	if request.user.is_superuser:
		return Certificates.objects.all().count()
	else:
		if isinstance(request.user, User):
			susers = SubUser.objects.filter(creator=request.user)
			return Certificates.objects.filter(creator__in=susers).count()
		return Certificates.objects.filter(creator=request.user).count()



def _testlog_queryset_for_user(user):
	qs = TestLog.objects.all()
	if user.is_superuser:
		return qs
	if isinstance(user, SubUser):
		return qs.filter(creator=user)
	if isinstance(user, User):
		return qs.filter(creator__creator=user)
	return qs.none()


class getTestLogByVinView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def get(self, request):
		vin = (request.GET.get("vin") or "").strip().upper()
		if not vin:
			return Response({"error": "vin is required"}, status=status.HTTP_400_BAD_REQUEST)

		tl = (
			_testlog_queryset_for_user(request.user)
			.filter(vin_last4__iexact=vin)
			.order_by("-created_at")
			.first()
		)
		if not tl:
			return Response({"error": "testlog not found"}, status=status.HTTP_404_NOT_FOUND)

		# Map TestLog fields to Certificates form fields (id_<fieldname>).
		glass_vals = (tl.glass_trans_val or "").split(";")                                                                                                                                                                       
		glass_vals = [v.strip() for v in glass_vals]  
		fields = {
			"carYear": tl.car_year,
			"testTM": tl.tyre_mark_val,
			"testLTLG": glass_vals[0] if len(glass_vals) > 0 else "",
			"testLTWG": glass_vals[1] if len(glass_vals) > 1 else "",
			"testLTRG": glass_vals[2] if len(glass_vals) > 2 else "",
        	"carWT": tl.dimensions_track,
        	"testBWD": tl.brake_diff,
        	"testCBDR": tl.brake_diff_parking,
        	"testSPB": tl.brake_specific,
			"testCoMin": tl.co_idle_val,
			"testCoMax": tl.co_high_val,
			"testEN": tl.noise_db,
			"testTSP": tl.steer_play_val,
			"testTH": tl.tread_h_val,
			"test_depth": tl.tread_h_val or "",
			"testTemp": tl.temp_air,
			"testHum": tl.humidity,
			"testPress": tl.pressure,
			"carMarkRefPlL": tl.plate_height_down,
			"carMarkRefPlH": tl.plate_height_up,
			"testALN": tl.lowbeam_height_val,
			"test_noise": tl.noise_db,
			"carLength": tl.dimensions_length,
			"carWidth": tl.dimensions_width,
			"carHeight": tl.dimensions_height,
			"carBase": tl.dimensions_wheelbase,
			"testWheelFront": tl.dimensions_track,
			"testWheelBack": tl.dimensions_track,
                                                                                             
		}
		fields.update(
			{
				"plate_angle_long": tl.plate_angle_long,
				"plate_angle_vert": tl.plate_angle_vert,
				"brake_diff": tl.brake_diff,
				"lowbeam_height_val": tl.lowbeam_height_val,
				"fog_dist_val": tl.fog_dist_val,
				"fog_level_value": tl.fog_level_value,
				"brake_lamp_width_val": tl.brake_lamp_width_val,
				"brake_extra_h_val": tl.brake_extra_h_val,
				"brake_extra_shift_val": tl.brake_extra_shift_val,
				"rear_fog_h_val": tl.rear_fog_h_val,
			}
		)

		return Response(
			{
				"testlog_id": tl.id,
				"testlog_number": tl.test_number,
				"fields": fields,
			},
			status=status.HTTP_200_OK,
		)


class getCarView(APIView):
	permission_classes = []
	def get(self, request):
		searchString = request.GET.get("search","")

		res = requests.get(
        	f"https://techreg.gov.kz/Synergy/rest/api/registry/data_ext?registryCode=registry_certificate_safety_vehicle_structure&pageNumber=0&countInPart=15&fields=textbox_number&fields=reglink_application&fields=textbox_stamp&fields=date_registration&fields=textbox_vin&fields=textbox_applicant&fields=listbox_status&fields=listbox_category&fields=textbox_bin&fields=textbox_manufacturer&fields=reglink_mark&fields=textbox_email_organization&fields=textbox_year&fields=textbox_length&fields=textbox_width&fields=textbox_height&fields=textbox_engine_brand&fields=numericinput_number_of_engine_cylinders&fields=numericinput_engine_cylinder_displacement&fields=numericinput_engine_compression_ratio&fields=numericinput_engine_rotation_speed&fields=numericinput_maximum_power_1&fields=numericinput_engine_rotation_speed_2&fields=textarea_description_engine_location&fields=numericinput_maximum_power&fields=textarea_power_system_description&fields=textarea_ignition&fields=textarea_exhaust&fields=textarea_storage_device&fields=textarea_transmission&fields=textbox_mark_steering&fields=textbox_cp_type&fields=textbox_min&fields=textbox_min_2&fields=textbox_track_front_rear_wheels&fields=textarea_front_suspension&fields=textarea_back_suspension&fields=textbox_size_tires&fields=textbox_number_of_seats&fields=textbox_body_type&fields=textarea_frame_description&fields=listbox_type_body&fields=textbox_address_assembly_plant&fields=textbox_vehicle_layout_diagram&fields=listbox_type_body&fields=textbox_base&fields=textbox_track_front_rear_wheels&fields=textbox_br_work&fields=textbox_br_spare&fields=textbox_br_parking&searchString={searchString}",
        	verify=False,
        	headers=headers,
        	auth = HTTPBasicAuth("guest_user", "f5e8ae79b4bb414713532f82f0a82037"),
		)

		if res.status_code == 200:
			data = res.json()
			if len(data.get("result")) > 0:
				return Response(data.get("result")[0], status=status.HTTP_200_OK)
			
			return Response(None, status=status.HTTP_400_BAD_REQUEST)
		
		return Response(None, status=status.HTTP_400_BAD_REQUEST)

class getUserView(APIView):
	permission_classes = [permissions.IsAuthenticated]
	
	def post(self, request, format=None):
		username = (request.data.get("username") or "").strip()
		password = request.data.get("password") or ""
		if not username or not password:
			return Response(
				{"error": "Введите почту и пароль для входа в ЕКТРМ."},
				status=status.HTTP_400_BAD_REQUEST,
			)

		try:
			res = requests.get(
				"https://techreg.gov.kz/Synergy/rest/api/person/auth",
				verify=False,
				headers={"Accept": "application/json"},
				auth=HTTPBasicAuth(username, password),
				timeout=(5, 20),
			)
		except requests.RequestException:
			return Response(
				{"error": "ЕКТРМ сейчас недоступен. Повторите попытку позже."},
				status=status.HTTP_502_BAD_GATEWAY,
			)

		if res.status_code in (401, 403):
			return Response(
				{"error": "ЕКТРМ отклонил почту или пароль."},
				status=status.HTTP_401_UNAUTHORIZED,
			)
		if res.status_code != 200:
			return Response(
				{"error": f"ЕКТРМ вернул ошибку {res.status_code}."},
				status=status.HTTP_502_BAD_GATEWAY,
			)

		try:
			return Response(res.json(), status=status.HTTP_200_OK)
		except requests.exceptions.JSONDecodeError:
			return Response(
				{"error": "ЕКТРМ вернул некорректный ответ."},
				status=status.HTTP_502_BAD_GATEWAY,
			)


class setSignatureView(APIView):
	permission_classes = [permissions.IsAdminUser]

	parser_classes = (MultiPartParser, FormParser)

	def post(self, request, format=None):
		vin = request.data.get('vin')
		if vin is not None:
			cert = Certificates.objects.filter(carVin = str(vin))
			if len(cert) > 0:
				model = CertModelSerializer(cert[0]).data

				signature = request.data.get("signature")

				if len(signature) > 0:

					obj = Certificates.objects.get(id = model.get("id"))
					obj.signature = signature
					obj.save()
					# profile = Profile.objects.get(user=obj.creator.creator)
					# model["vendor"] = profile.vendor                                                                                                                                                                       
					# model["vendor_uid"] = profile.uid
					# model["vendor_address"] = profile.address                                                                                                                                                              
					# model["vendor_phone"] = profile.phone                                                                                                                                                                  
					# model["vendor_iik"] = profile.iik                                                                                                                                                                      
					# model["vendor_bik"] = profile.bik                                                                                                                                                                      
					# model["vendor_fil"] = profile.fil                                                                                                                                                                      
					# model["vendor_email"] = obj.creator.creator.email                                                                                                                                                      
					# model["vendor_frln"] = f"{obj.creator.creator.last_name} {obj.creator.creator.first_name}" 
					# last_num = Certificates.objects.filter().order_by("-conclusionNumber").values_list("conclusionNumber", flat=True).first()
					# obj.save(update_fields=["conclusionNumber"])
					# model["conclusion_number"] = obj.conclusionNumber
					#тут
					if not obj.conclusionNumber:
						last_num = Certificates.objects.filter(conclusionNumber__isnull=False).order_by("-conclusionNumber").values_list("conclusionNumber", flat=True).first()
						obj.conclusionNumber = (last_num or 0) + 1
						obj.save(update_fields=["conclusionNumber"])
					model["conclusion_number"] = obj.conclusionNumber
					

					model["CfirstName"] = obj.creator.first_name
					model["ClastName"] = obj.creator.last_name
					model["day"] = obj.certCreateDate.day
					model["month"] = month_to_string.get(obj.certCreateDate.month)
					model["year"] = obj.certCreateDate.year
					# model["minusDay"] = obj.certCreateDate.day if obj.certCreateDate.day > 1 else obj.certCreateDate.day - 1
					prev_day = obj.certCreateDate - timedelta(days=1)
					model["minusDay"] = prev_day.day

					if obj.actus:
						model["actus"] = obj.actus.number
						model["actusYear"] = obj.actus.createDate.year
						model["actusDevice"] = obj.actus.button.hwname
						model["actusICCID"] = obj.actus.button.iccid
						model["actusIMEI"] = obj.actus.button.imei

					model["testFuelType"] = obj.get_testFuelType_display()
					model["testLocation"] = obj.get_testLocation_display()
					model["carEco"] = obj.get_carEco_display()
					model["carVLD"] = obj.get_carVLD_display()

					decision = DocxTemplate(BASE_DIR / f"media/ref/decision.docx")
					decision.render(model)
					decision.save(BASE_DIR / f"media/decisions/Решение_{model.get('sbkts')}.docx")
					convert_to(BASE_DIR / f"media/decisions/Решение_{model.get('sbkts')}.docx")

					application = DocxTemplate(BASE_DIR / f"media/ref/application.docx")
					application.replace_pic("sigtest1.png", copy.deepcopy(obj.signature))
					application.render(model)
					application.save(BASE_DIR / f"media/applications/Заявка_{model.get('sbkts')}.docx")
					convert_to(BASE_DIR / f"media/applications/Заявка_{model.get('sbkts')}.docx")

					contract = DocxTemplate(BASE_DIR / f"media/ref/contract.docx")
					contract.replace_pic("sign.png", obj.signature)
					contract.render(model)
					contract.save(BASE_DIR / f"media/contracts/Договор_{model.get('sbkts')}.docx")
					convert_to(BASE_DIR / f"media/contracts/Договор_{model.get('sbkts')}.docx")

					logbook = DocxTemplate(BASE_DIR / f"media/ref/logbook.docx")
					logbook.replace_pic("sign.png", obj.signature)
					logbook.render(model)
					logbook.save(BASE_DIR / f"media/logbooks/Журнал_{model.get('sbkts')}.docx")
					convert_to(BASE_DIR / f"media/logbooks/Журнал_{model.get('sbkts')}.docx")
					
					#тут
					conclusion = DocxTemplate(BASE_DIR / f"media/ref/conclusion.docx")                                                                                                                                                                                                                                                        
					conclusion.replace_pic("sigtest1.png", copy.deepcopy(obj.signature))  
					conclusion.render(model)                                                                                                                                                      
					conclusion.save(BASE_DIR / f"media/conclusions/Заключение_{model.get('sbkts')}.docx")                                                                                         
					convert_to(BASE_DIR / f"media/conclusions/Заключение_{model.get('sbkts')}.docx") 

					journal_c00395 = DocxTemplate(BASE_DIR / "media/ref/journal_С-00395.docx")                                                                                    
					journal_c00395.render(model)                                                                                                                                  
					journal_c00395.save(BASE_DIR / f"media/journal_main/Журнал_Основной_{model.get('sbkts')}.docx")                                                               
					convert_to(BASE_DIR / f"media/journal_main/Журнал_Основной_{model.get('sbkts')}.docx")                                                                        
																																													
					protocol_c00395 = DocxTemplate(BASE_DIR / "media/ref/protocol_add_С-00395.docx")                                                                              
					protocol_c00395.render(model)
					protocol_c00395.save(BASE_DIR / f"media/protocol_main/Протокол_Основной_{model.get('sbkts')}.docx")                                                           
					convert_to(BASE_DIR / f"media/protocol_main/Протокол_Основной_{model.get('sbkts')}.docx") 

					if obj.carCategory in ["O1", "O2", "O3", "O4"]:
						experts = DocxTemplate(BASE_DIR / f"media/ref/tex_expert_p.docx")
						experts.replace_pic("sign.png", obj.creator.sign)
						experts.render(model)
						experts.save(BASE_DIR / f"media/experts/ТехСпец_{model.get('sbkts')}.docx")
						convert_to(BASE_DIR / f"media/experts/ТехСпец_{model.get('sbkts')}.docx")
					else:
						experts = DocxTemplate(BASE_DIR / f"media/ref/tex_expert.docx")
						experts.replace_pic("sign.png", obj.creator.sign)
						experts.render(model)
						experts.save(BASE_DIR / f"media/experts/ТехСпец_{model.get('sbkts')}.docx")
						convert_to(BASE_DIR / f"media/experts/ТехСпец_{model.get('sbkts')}.docx")

					
					if obj.carCategory in ["O1", "O2", "O3", "O4"]:
						protocol = DocxTemplate(BASE_DIR / f"media/ref/protocol_o.docx")
						protocol.replace_pic("sign.png", copy.deepcopy(obj.creator.sign))
						protocol.render(model)
						protocol.save(BASE_DIR / f"media/protocols/Протокол_{model.get('sbkts')}.docx")
						convert_to(BASE_DIR / f"media/protocols/Протокол_{model.get('sbkts')}.docx")
					else:
						if obj.testFuelType in ["b", "g", "d"]:
							protocol = DocxTemplate(BASE_DIR / f"media/ref/protocol_b.docx")
							protocol.replace_pic("sign.png", copy.deepcopy(obj.creator.sign))
							protocol.render(model)
							protocol.save(BASE_DIR / f"media/protocols/Протокол_{model.get('sbkts')}.docx")
							convert_to(BASE_DIR / f"media/protocols/Протокол_{model.get('sbkts')}.docx")
						elif obj.testFuelType == "e":
							protocol = DocxTemplate(BASE_DIR / f"media/ref/protocol_b.docx")
							protocol.replace_pic("sign.png", copy.deepcopy(obj.creator.sign))
							protocol.render(model)
							protocol.save(BASE_DIR / f"media/protocols/Протокол_{model.get('sbkts')}.docx")
							convert_to(BASE_DIR / f"media/protocols/Протокол_{model.get('sbkts')}.docx")
						else:
							pass
					
					def attach_testlog_fields(model, cert_obj):                                                                                                                                                                              
						vin = (cert_obj.carVin or "").strip().upper()                                                                                                                                                                        
						tl = (                                                                                                                                                                                                               
							TestLog.objects                                                                                                                                                                                                  
							.filter(vin_last4__iexact=vin, isClose=True)                                                                                                                                                                     
							.order_by("-created_at")                                                                                                                                                                                         
							.first()                                                                                                                                                                                                         
						)                                                                                                                                                                                                                    
																																																											
						names = [                                                                                                                                                                                                            
							"plate_angle_long", "plate_angle_vert", "brake_diff", "lowbeam_height_val",                                                                                                                                      
							"fog_dist_val", "fog_level_value", "brake_lamp_width_val",                                                                                                                                                       
							"brake_extra_h_val", "brake_extra_shift_val", "rear_fog_h_val",                                                                                                                                                  
						]                                                                                                                                                                                                                    
						for n in names:                                                                                                                                                                                                      
							model[n] = getattr(tl, n, "") if tl else ""   
						model["test_depth"] = (getattr(tl, "tread_h_val", "") if tl else "") or ""
					
					new_tpl = BASE_DIR / "media/ref/protocol_new.docx"                                                                                                                                                                       
					if new_tpl.exists():                                                                                                                                                                                                     
						protocol_new = DocxTemplate(new_tpl)                                                                                                                                                                                 
						protocol_new.replace_pic("sign.png", copy.deepcopy(obj.creator.sign))                                                                                                                                                
						attach_testlog_fields(model, obj)                                                                                                                                                                                    
						protocol_new.render(model)                                                                                                                                                                                           
																																																											
						out_docx = BASE_DIR / f"media/protocols_new/Протокол_новый_{model.get('sbkts')}.docx"                                                                                                                                
						out_docx.parent.mkdir(parents=True, exist_ok=True)  # <-- важно                                                                                                                                                      
																																																											
						protocol_new.save(out_docx)                                                                                                                                                                                          
						convert_to(out_docx) 
						

# 					if obj.testType:
# 						if obj.testFuelType == "b":
# 							protocol = DocxTemplate(BASE_DIR / f"media/ref/protocol_ezt_b.docx")
# 							#protocol.replace_pic("sigtest1.png", os.path.abspath("media/signs/"+obj.creator.username+".png"))
# 							protocol.render(model)
# 							protocol.save(BASE_DIR / f"media/protocols/Протокол_{model.get('sbkts')}.docx")
# 							convert_to(BASE_DIR / f"media/protocols/Протокол_{model.get('sbkts')}.docx")
# 						elif obj.testFuelType == "g":
# 							protocol = DocxTemplate(BASE_DIR / f"media/ref/protocol_ezt_g.docx")
# 							#protocol.replace_pic("sigtest1.png", os.path.abspath("media/signs/"+obj.creator.username+".png"))
# 							protocol.render(model)
# 							protocol.save(BASE_DIR / f"media/protocols/Протокол_{model.get('sbkts')}.docx")
# 							convert_to(BASE_DIR / f"media/protocols/Протокол_{model.get('sbkts')}.docx")
# 						elif obj.testFuelType == "d":
# 							protocol = DocxTemplate(BASE_DIR / f"media/ref/protocol_ezt_d.docx")
# 							#protocol.replace_pic("sigtest1.png", os.path.abspath("media/signs/"+obj.creator.username+".png"))
# 							protocol.render(model)
# 							protocol.save(BASE_DIR / f"media/protocols/Протокол_{model.get('sbkts')}.docx")
# 							convert_to(BASE_DIR / f"media/protocols/Протокол_{model.get('sbkts')}.docx")
# 						elif obj.testFuelType == "e":
# 							protocol = DocxTemplate(BASE_DIR / f"media/ref/protocol_ezt_e.docx")
# 							#protocol.replace_pic("sigtest1.png", os.path.abspath("media/signs/"+obj.creator.username+".png"))
# 							protocol.render(model)
# 							protocol.save(BASE_DIR / f"media/protocols/Протокол_{model.get('sbkts')}.docx")
# 							convert_to(BASE_DIR / f"media/protocols/Протокол_{model.get('sbkts')}.docx")
# 						else:
# 							pass
# 					else:
# 						if obj.carCategory in ["O1", "O2", "O3", "O4"]:
# 							protocol = DocxTemplate(BASE_DIR / f"media/ref/protocol_stm_o.docx")
# 							protocol.replace_pic("sign.png", copy.deepcopy(obj.creator.sign))
# 							protocol.render(model)
# 							protocol.save(BASE_DIR / f"media/protocols/Протокол_{model.get('sbkts')}.docx")

# 							# document = Document(BASE_DIR / f"media/protocols/Протокол_{model.get('sbkts')}.docx")
# 							# if obj.app1: set_img("[F1]", obj.app1, document)
# 							# if obj.app2: set_img("[F2]", obj.app2, document)
# 							# if obj.app3: set_img("[F3]", obj.app3, document)
# 							# if obj.app4: set_img("[F4]", obj.app4, document)
# 							# if obj.app5: set_img("[F5]", obj.app5, document)
# 							# if obj.app6: set_img("[F6]", obj.app6, document)
# 							# if obj.app7: set_img("[F7]", obj.app7, document)
# 							# if obj.app8: set_img("[F8]", obj.app8, document)
# 							# if obj.app9: set_img("[F9]", obj.app9, document)
# 							# if obj.app10: set_img("[F9]", obj.app10, document)
# 							# document.save(BASE_DIR / f"media/protocols/Протокол_{model.get('sbkts')}.docx")

# 							convert_to(BASE_DIR / f"media/protocols/Протокол_{model.get('sbkts')}.docx")

# 							obj = Certificates.objects.get(id = model.get("id"))
# 							obj.decision = f"decisions/Решение_{obj.sbkts}.pdf"
# 							obj.application = f"applications/Заявка_{obj.sbkts}.pdf"
# 							obj.contract = f"contracts/Договор_{obj.sbkts}.pdf"
# 							obj.protocol = f"protocols/Протокол_{obj.sbkts}.pdf"
# 							obj.expert = f"experts/ТехСпец_{obj.sbkts}.pdf"
# 							obj.isClose = True
# 							obj.save()

# 							return Response({"success": "ok"}, status=status.HTTP_201_CREATED)

# 						if obj.testFuelType == "b":
# 							protocol = DocxTemplate(BASE_DIR / f"media/ref/protocol_stm_b.docx")
# 							protocol.replace_pic("sign.png", copy.deepcopy(obj.creator.sign))
# 							protocol.render(model)
# 							protocol.save(BASE_DIR / f"media/protocols/Протокол_{model.get('sbkts')}.docx")

# 							# document = Document(BASE_DIR / f"media/protocols/Протокол_{model.get('sbkts')}.docx")
# 							# # if obj.app1: set_img("[F1]", obj.app1, document)
# 							# # if obj.app2: set_img("[F2]", obj.app2, document)
# 							# # if obj.app3: set_img("[F3]", obj.app3, document)
# 							# # if obj.app4: set_img("[F4]", obj.app4, document)
# 							# # if obj.app5: set_img("[F5]", obj.app5, document)
# 							# # if obj.app6: set_img("[F6]", obj.app6, document)
# 							# # if obj.app7: set_img("[F7]", obj.app7, document)
# 							# # if obj.app8: set_img("[F8]", obj.app8, document)
# 							# # if obj.app9: set_img("[F9]", obj.app9, document)
# 							# # if obj.app10: set_img("[F9]", obj.app10, document)
# 							# document.save(BASE_DIR / f"media/protocols/Протокол_{model.get('sbkts')}.docx")

# 							convert_to(BASE_DIR / f"media/protocols/Протокол_{model.get('sbkts')}.docx")
# 						elif obj.testFuelType == "g":
# 							protocol = DocxTemplate(BASE_DIR / f"media/ref/protocol_stm_g.docx")
# 							protocol.replace_pic("sign.png", copy.deepcopy(obj.creator.sign))
# 							protocol.render(model)
# 							protocol.save(BASE_DIR / f"media/protocols/Протокол_{model.get('sbkts')}.docx")

# 							# document = Document(BASE_DIR / f"media/protocols/Протокол_{model.get('sbkts')}.docx")
# 							# if obj.app1: set_img("[F1]", obj.app1, document)
# 							# if obj.app2: set_img("[F2]", obj.app2, document)
# 							# if obj.app3: set_img("[F3]", obj.app3, document)
# 							# if obj.app4: set_img("[F4]", obj.app4, document)
# 							# if obj.app5: set_img("[F5]", obj.app5, document)
# 							# if obj.app6: set_img("[F6]", obj.app6, document)
# 							# if obj.app7: set_img("[F7]", obj.app7, document)
# 							# if obj.app8: set_img("[F8]", obj.app8, document)
# 							# if obj.app9: set_img("[F9]", obj.app9, document)
# 							# if obj.app10: set_img("[F9]", obj.app10, document)
# 							# document.save(BASE_DIR / f"media/protocols/Протокол_{model.get('sbkts')}.docx")

# 							convert_to(BASE_DIR / f"media/protocols/Протокол_{model.get('sbkts')}.docx")
# 						elif obj.testFuelType == "d":
# 							protocol = DocxTemplate(BASE_DIR / f"media/ref/protocol_stm_d.docx")
# 							protocol.replace_pic("sign.png", copy.deepcopy(obj.creator.sign))
# 							protocol.render(model)
# 							protocol.save(BASE_DIR / f"media/protocols/Протокол_{model.get('sbkts')}.docx")

# 							# document = Document(BASE_DIR / f"media/protocols/Протокол_{model.get('sbkts')}.docx")
# 							# if obj.app1: set_img("[F1]", obj.app1, document)
# 							# if obj.app2: set_img("[F2]", obj.app2, document)
# 							# if obj.app3: set_img("[F3]", obj.app3, document)
# 							# if obj.app4: set_img("[F4]", obj.app4, document)
# 							# if obj.app5: set_img("[F5]", obj.app5, document)
# 							# if obj.app6: set_img("[F6]", obj.app6, document)
# 							# if obj.app7: set_img("[F7]", obj.app7, document)
# 							# if obj.app8: set_img("[F8]", obj.app8, document)
# 							# if obj.app9: set_img("[F9]", obj.app9, document)
# 							# if obj.app10: set_img("[F9]", obj.app10, document)
# 							# document.save(BASE_DIR / f"media/protocols/Протокол_{model.get('sbkts')}.docx")

# 							convert_to(BASE_DIR / f"media/protocols/Протокол_{model.get('sbkts')}.docx")
# 						elif obj.testFuelType == "e":
# 							protocol = DocxTemplate(BASE_DIR / f"media/ref/protocol_stm_e.docx")
# 							#protocol.replace_pic("sigtest1.png", os.path.abspath("media/signs/"+obj.creator.username+".png"))
# 							protocol.render(model)
# 							protocol.save(BASE_DIR / f"media/protocols/Протокол_{model.get('sbkts')}.docx")
# 							convert_to(BASE_DIR / f"media/protocols/Протокол_{model.get('sbkts')}.docx")
# 						else:
# 							pass


					obj = Certificates.objects.get(id = model.get("id"))
					obj.decision = f"decisions/Решение_{obj.sbkts}.pdf"
					obj.application = f"applications/Заявка_{obj.sbkts}.pdf"
					obj.contract = f"contracts/Договор_{obj.sbkts}.pdf"
					obj.protocol = f"protocols/Протокол_{obj.sbkts}.pdf"
					obj.protocol_new = f"protocols_new/Протокол_новый_{obj.sbkts}.pdf"
					obj.logbook = f"logbooks/Журнал_{obj.sbkts}.pdf"
					obj.expert = f"experts/ТехСпец_{obj.sbkts}.pdf"
					#тут
					obj.conclusion = f"conclusions/Заключение_{obj.sbkts}.pdf"
					obj.journal_c00395 = f"journal_main/Журнал_Основной_{obj.sbkts}.pdf"                                                                                         
					obj.protocol_c00395 = f"protocol_main/Протокол_Основной_{obj.sbkts}.pdf"
					obj.isClose = True
					obj.save()


					return Response({"success": "ok"}, status=status.HTTP_201_CREATED)

		return Response({"error": "bad request"}, status=status.HTTP_400_BAD_REQUEST)


@ensure_csrf_cookie
def signature(request):
	vin = request.GET.get('vin')

	if vin is not None:
		cert = Certificates.objects.filter(carVin = vin)
		if len(cert) > 0:
			model = CertModelSerializer(cert[0]).data
			return render(request, "cert/signature.html", model)
		else:
			return HttpResponse("bad request"+vin)
	
	return HttpResponse("params is null" + vin)

@ensure_csrf_cookie
def index_page(request):
	return render(request, "cert/new_page.html")
