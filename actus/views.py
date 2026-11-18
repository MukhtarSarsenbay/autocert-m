from django.shortcuts import render
from subuser.models import SubUser
from .models import *
from cert.models import Certificates
from django.contrib.auth.models import User
from django.conf import settings
from rest_framework import permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from .document_reader import DocumentReaderResponseError, detect_document_content_type, recognize_document


class RecognizeDocumentView(APIView):
    permission_classes = [permissions.IsAdminUser]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, kind):
        if kind not in {"id", "vin"}:
            return Response({"error": "Неизвестный тип документа"}, status=status.HTTP_404_NOT_FOUND)
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response({"error": "Файл не передан"}, status=status.HTTP_400_BAD_REQUEST)
        if uploaded_file.size > settings.DOCUMENT_READER_MAX_FILE_SIZE:
            size_mb = settings.DOCUMENT_READER_MAX_FILE_SIZE // (1024 * 1024)
            return Response({"error": f"Размер файла не должен превышать {size_mb} МБ"}, status=status.HTTP_400_BAD_REQUEST)
        if not detect_document_content_type(uploaded_file):
            return Response({"error": "Поддерживаются только PDF и JPG"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            payload = recognize_document(kind, uploaded_file)
        except DocumentReaderResponseError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        return Response(payload)

import json

from datetime import datetime, timedelta

month_to_string = {
	1: "январь",
	2: "февраль",
	3: "март",
	4: "апрель",
	5: "май",
	6: "июнь",
	7: "июль",
	8: "август",
	9: "сентябрь",
	10: "октябрь",
	11: "ноябрь",
	12: "декабрь"
}

week_to_day = {
	0: "вск",
	1: "пон",
	2: "втр",
	3: "срд",
	4: "чтв",
	5: "пят",
	6: "суб",
}

def get_month_intervals(year):
    month_intervals = []
    for month in range(1, 13):
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)
        month_intervals.append((start_date, end_date))
    return month_intervals

def get_daily_intervals():
    today = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    next_month = today.replace(day=28) + timedelta(days=4)  # Ensure we get into the next month
    end_of_month = next_month - timedelta(days=next_month.day)
    
    daily_intervals = []
    current_date = today
    while current_date <= end_of_month:
        start_of_day = current_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = current_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        daily_intervals.append((start_of_day, end_of_day))
        current_date += timedelta(days=1)
    return daily_intervals

def badge_callback_actus(request):
	if request.user.is_superuser:
		return Actus.objects.all().count()
	else:
		if isinstance(request.user, User):
			susers = SubUser.objects.filter(creator=request.user)
			return Actus.objects.filter(creator__in=susers).count()
		return Actus.objects.filter(creator=request.user).count()

def badge_callback_button(request):
	if request.user.is_superuser:
		return Button.objects.all().count()
	else:
		if isinstance(request.user, User):
			susers = SubUser.objects.filter(creator=request.user)
			return Button.objects.filter(user__in=susers).count()
		return Button.objects.filter(user=request.user).count()

def dashboard_callback(request, context):
    if not isinstance(request.user, User): return context

    users = SubUser.objects.filter(creator=request.user)

    if request.user.is_superuser:
        users = SubUser.objects.all()

    intervals = get_month_intervals(2025)
    intervals_month = get_daily_intervals()
    string_interval = [month_to_string.get(int(interval[0].strftime("%m"))) for interval in intervals]
    string_month_interval = [interval[0].strftime("%d") +", "+ week_to_day.get(int(interval[0].strftime("%w"))) for interval in intervals_month]

    datasets = [{
        "label": "Акт",
        "data": [Actus.objects.filter(createDate__gte=interval[0], createDate__lte=interval[1], creator__in=users).count() for interval in intervals],
    }]

    datasets_month = [{
        "label": "Акт",
        "data": [Actus.objects.filter(createDate__gte=interval[0], createDate__lte=interval[1], creator__in=users).count() for interval in intervals_month],
    }]

    userdatasets = []

    for user in users:
        userdatasets.append({
        	"label": f"{user.username}",
        	"data": [Actus.objects.filter(creator=user, createDate__gte=interval[0], createDate__lte=interval[1]).count() for interval in intervals],
        	"borderWidth": 1,
        })

#     companydatasets = []

#     for user in User.objects.all():
#         counts = []
#         for interval in intervals:
            
#             count += Actus.objects.filter(creator=user, createDate__gte=interval[0], createDate__lte=interval[1]).count()


#         userdatasets.append({
#         	"label": f"{user.username}",
#         	"data": counts,
#         	"borderWidth": 1,
#         })

    context.update({
    	'dashtitleyear': 'Статистика количестов актов за год',
    	'dashtitlemonth': 'Статистика количестов актов за месяц',
    	#'dashtitlecompany': 'Статистика количестов актов за год (по компаниям)',
    	'dashtitleuser': 'Статистика количестов актов за год (по пользователем)',
    
    	'count_actus': Actus.objects.filter(creator__in=users).count(),
    	'count_button': Button.objects.filter(user__in=users).count(),
    	'count_cert': Certificates.objects.filter(creator__in=users).count(),
    
    
    	'options': json.dumps({
            'responsive': True,
        	'maintainAspectRatio': False,
            'scales': {
                'yAxes': [{
                	'scaleLabel': {
        				'display': True,
      				 },
                	 'stacked': True,
                     'ticks': {
                         'beginAtZero': True
                     }
                 }]
             }
         }),
    
        'yeardata': json.dumps({
        	'labels': string_interval,
        	'datasets': datasets,
        }),
    
#     	'companydata': json.dumps({
#         	'labels': string_interval,
#         	'datasets': companydatasets,
#         }),
    	
        'monthdata': json.dumps({
        	'labels': string_month_interval,
        	'datasets': datasets_month,
        }),
    
    	'userdata': json.dumps({
        	'labels': string_interval,
        	'datasets': userdatasets,
        })
    })

    return context
