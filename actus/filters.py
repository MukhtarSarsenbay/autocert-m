from django.contrib import admin
import datetime

class CreatedAtFilter(admin.SimpleListFilter):
    title = 'Создание'
    parameter_name = 'createDate'
    template = 'admin/input_filter.html'

    def lookups(self, request, model_admin):
        return [(0, 0),]

    def queryset(self, request, queryset):
        if self.value():
            created_at_date = self.value().split(' - ')
            created_at_start = datetime.datetime.strptime(created_at_date[0], "%m/%d/%Y")
            created_at_end = datetime.datetime.strptime(created_at_date[1], "%m/%d/%Y") + datetime.timedelta(days=1)
            return queryset.filter(createDate__range=[created_at_start, created_at_end])
        return queryset