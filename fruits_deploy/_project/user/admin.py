from django.contrib import admin
from .models import Supplier, Seller, Container, Item, ContainerItem, Sale,Payment, Lose, ContainerExpense, ContainerBill, SupplierPay, RecentAction, Worker, Loan
from django.contrib.auth.models import Group

admin.site.site_header = 'Tiger tech'
admin.site.site_title = 'إدارة موقع تايجر'
admin.site.index_title = 'الإدارة'


admin.site.unregister(Group)



















admin.site.register(Container)
admin.site.register(Supplier)
admin.site.register(Seller)
admin.site.register(Item)
admin.site.register(ContainerItem)
admin.site.register(Sale)
admin.site.register(Payment)
admin.site.register(Lose)
admin.site.register(ContainerExpense)
admin.site.register(ContainerBill)
admin.site.register(SupplierPay)
admin.site.register(RecentAction)
admin.site.register(Worker)
admin.site.register(Loan)