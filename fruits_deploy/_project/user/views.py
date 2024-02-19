from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Supplier, Seller, Container, Item, ContainerItem, Sale, Payment, Lose, ContainerExpense, ContainerBill, SupplierPay, RecentAction, User, Worker, Loan
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum
from datetime import datetime,timedelta
from django.db.models import F
import pytz
from django.core.exceptions import ValidationError
from decimal import Decimal, InvalidOperation, DecimalException
from django.forms.models import model_to_dict
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

#====================================================================================================================
def login_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username = username, password = password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.warning(request, 'هناك خطأ في اسم المستخدم او كلمة المرور')

    return render(request, 'login.html')
#====================================================================================================================
def logout_user(request):
    logout(request)
    return render(request, 'logout.html')
#====================================================================================================================
@login_required(login_url="login")
def home(request):
    return render(request, 'home.html')
#====================================================================================================================
#====================================================================================================================
#==================================================CONTAINER=========================================================
#====================================================================================================================
#====================================================================================================================
@login_required(login_url="login")
def add_container(request):
    supplier_name = request.session.get('supplier_name', '')

    if request.method == "POST":
        if 'add_container' in request.POST:
            supplier_name = request.POST.get('supplier')
            date_str = request.POST.get('date')
            type = request.POST.get('type')

            try:
                supplier = Supplier.objects.get(name=supplier_name)
            except Supplier.DoesNotExist:
                messages.warning(request, f'العميل  ({supplier_name}) غير موجود هل تريد إضافته؟')

                request.session['supplier_name'] = supplier_name

                return redirect('addcontainer')

            if not date_str:
                egypt_tz = pytz.timezone('Africa/Cairo')
                date = timezone.now().astimezone(egypt_tz).date()
            else:
                try:
                    date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    messages.error(request, 'تاريخ غير صالح. يجب أن يكون الشكل YYYY-MM-DD', extra_tags='warning')

                    
                    request.session['supplier_name'] = supplier_name

                    return redirect('addcontainer')

            new_container = Container.objects.create(supplier=supplier, date=date, type=type)

            RecentAction.objects.create(
                user=request.user,
                action_sort = 'نقلة',
                action_type='اضافة نقلة جديدة',
                model_affected=f'نقلة رقم {new_container.id} باسم العميل :{new_container.supplier.name}',
            )

            messages.success(request, "تم إضافة نقلة جديدة بنجاح")

            
            request.session.pop('supplier_name', None)

            return redirect('addcontainer')

        elif 'add_supplier' in request.POST:
            supplier_name = request.POST.get('new_supplier')
            supplier_name.strip()
            new_supplier = Supplier.objects.create(name=supplier_name, place='-', date=timezone.now().astimezone(pytz.timezone('Africa/Cairo')).date(), opening_balance=0)
            RecentAction.objects.create(
                user=request.user,
                action_sort = 'عملاء',
            action_type='إضافة عميل جديد',
            model_affected=f'اضافة عميل باسم ({new_supplier.name}) برصيد افتتاحي قدره ({new_supplier.opening_balance} جنيه)',
            )

            messages.success(request, f"تم إضافة العميل {new_supplier.name}")

            
            request.session.pop('supplier_name', None)

            return redirect('addcontainer')

    container_list = Container.objects.all().order_by('-date', 'id')
    paginator = Paginator(container_list, 20)  

    page = request.GET.get('page')
    try:
        containers = paginator.page(page)
    except PageNotAnInteger:
        containers = paginator.page(1)
    except EmptyPage:
        containers = paginator.page(paginator.num_pages)

    context = {
        'containers': containers,
        'supplys': Supplier.objects.all(),
        'supplier_name': supplier_name,  
    }
    return render(request, 'add.html', context)
#====================================================================================================================
def container_update(request, id):
    container = None 

    if 'containerUpdate' in request.POST:
        supplier = request.POST['supplier']
        date_str = request.POST['date']
        type = request.POST['type']

        supplier = supplier.strip()
        type = type.strip()

        try:
            supplier = Supplier.objects.get(name=supplier)
        except Supplier.DoesNotExist:
            messages.error(request, 'العميل غير موجود')
            return redirect('addcontainer')

        try:
            if date_str: 
                date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            elif not supplier:
                messages.error(request,"اسم العميل غير موجود")
                return redirect('addcontainer')
            else:
                egypt_tz = pytz.timezone('Africa/Cairo')
                date = timezone.now().astimezone(egypt_tz).date()


            edit = Container.objects.get(id=id)
            edit.supplier = supplier
            edit.date = date
            edit.type = type
            edit.save()
            messages.success(request, 'تم تعديل بيانات النقلة بنجاح', extra_tags='success')
            return redirect("addcontainer")
        except ValueError:
            messages.error(request, 'تاريخ غير صالح. يجب أن يكون الشكل YYYY-MM-DD', extra_tags='warning')
            return redirect('addcontainer')
        except Container.DoesNotExist:
            messages.error(request, 'حدث خطأ، العميل غير موجود', extra_tags='error')
            return redirect("addcontainer")

    else:  # Initial rendering
        try:
            container = Container.objects.get(id=id)  # Retrieve object
        except Container.DoesNotExist:
            messages.error(request, 'حدث خطأ، العميل غير موجود', extra_tags='error')
            return redirect("addcontainer")
#====================================================================================================================
def container_delete(request, id):
    container_to_delete = get_object_or_404(Container, id=id)

    if 'containerDelete' in request.POST:
        RecentAction.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action_type='حذف نقلة',
            action_sort = 'نقلة',
            model_affected=f'تم حذف نقلة رقم {container_to_delete.id} باسم العميل {container_to_delete.supplier.name}',
        )
        container_to_delete.delete()
        messages.success(request, "تم حذف النقلة بنجاح")
        return redirect("addcontainer")
#====================================================================================================================
@login_required(login_url="login")
def container_details(request, id):
    container = get_object_or_404(Container, pk=id)
    expenses = ContainerExpense.objects.filter(container=container)
    container_bills = ContainerBill.objects.filter(container=container)
    container_items = ContainerItem.objects.filter(container=container)
    sales = Sale.objects.filter(container=container)

    total_of_nakla = sum(bill.total_bill_row for bill in container_bills)
    total_bill_price = sum(bill.total_bill_row for bill in container_bills)

    context = {
        'container': container,
        'expenses': expenses,
        'container_bills': container_bills,
        'container_items': container_items,
        'total_of_nakla': total_of_nakla,
        'total_bill_price': total_bill_price,
        'sales' : sales,
    }

    if request.method == "POST":
        if 'profits_submit' in request.POST:
            commission = request.POST['commission']
            carry = request.POST['carry']
            tool_rent = request.POST['tool_rent']

            commission = 0 if not commission else commission
            carry = 0 if not carry else carry
            tool_rent = 0 if not tool_rent else tool_rent

            edit = Container.objects.get(id=id)
            edit.commission = float(commission)
            edit.carry = carry
            edit.tool_rent = tool_rent
            edit.save()

            RecentAction.objects.create(
                user=request.user if request.user.is_authenticated else None,
                action_type='اضافة خصومات للنقلة ',
                action_sort = 'نقلة',
                model_affected=f'تم اضافة خصومات للنقلة رقم ({edit.id}) بعمولة ({edit.commission}) و مشال ({edit.carry}) و ايجار عدة ({edit.tool_rent})',
            )

            messages.success(request, 'تم اضافة خصومات النقلة بنجاح', extra_tags='success')

        elif 'loses_submit' in request.POST:
            expense_amount = request.POST['expense']
            expense_type = request.POST['expense_type']
            expense_notes = request.POST['expense_notes']

            if not expense_amount:
                messages.error(request, 'يجب ادخال المبلغ لاضافة المصروف', extra_tags='error')
            else:
                new_expense = ContainerExpense.objects.create(
                    container=container,
                    expense=expense_amount,
                    expense_type=expense_type,
                    expense_notes=expense_notes,
                )

                RecentAction.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action_type='اضافة مصروفات للنقلة ',
                    action_sort = 'نقلة',
                    model_affected=f'اضافة مصروفات للنقلة رقم ({container.id}) بقيمة ({new_expense.expense} جنيه)',
                )

                messages.success(request, 'تمت اضافة المصروف بنجاح', extra_tags='success')

        elif 'add_bill_submit' in request.POST:
            count = request.POST['count']
            weight = request.POST['weight']
            price = request.POST['price']
            container_item_id = request.POST['container_item']

            if not (count and weight and price and container_item_id):
                messages.error(request, 'برجاء ادخال كافة البيانات', extra_tags='error')
            else:
                container_item = get_object_or_404(ContainerItem, pk=container_item_id)

                new_bill = ContainerBill.objects.create(
                    container=container,
                    container_item=container_item,
                    count=count,
                    weight=weight,
                    price=price,
                )

                RecentAction.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action_type='اضافة خانة فاتورة',
                    action_sort = 'نقلة',
                    model_affected=f'اضافة خانة فاتورة للنقلة رقم ({container.id}) بقيمة تساوي ({new_bill.total_bill_row})',
                )

                messages.success(request, 'تم ادخال خانة فاتورة نقلة', extra_tags='success')

        return redirect("condetails", id=id)

    return render(request, 'cardetails.html', context)
#====================================================================================================================
def container_bill_update(request, id):
    container_bill = get_object_or_404(ContainerBill, id=id)
    container_items = ContainerItem.objects.all()
    old_container_bill_data = None

    if request.method == 'POST':
        count = request.POST.get('count')
        weight = request.POST.get('weight')
        price = request.POST.get('price')
        container_item_id = request.POST.get('container_item')

        if not (count and weight and price and container_item_id):
            pass

        old_container_bill_data = ContainerBill.objects.filter(id=id).values().first()

        container_item = get_object_or_404(ContainerItem, pk=container_item_id)
        old_count = old_container_bill_data['count']
        old_weight = old_container_bill_data['weight']
        old_price = old_container_bill_data['price']
        old_container_item_id = old_container_bill_data['container_item_id']

        changes = []
        if count != old_count:
            changes.append(f'العدد من {old_count} إلى {count}')
        if weight != old_weight:
            changes.append(f'الوزن من {old_weight} إلى {weight}')
        if price != old_price:
            changes.append(f'السعر من {old_price} إلى {price}')
        if container_item_id != old_container_item_id:
            changes.append(f'الصنف من {old_container_item_id} إلى {container_item_id}')

        container_bill.count = count
        container_bill.weight = weight
        container_bill.price = price
        container_bill.container_item = container_item
        container_bill.save()
        messages.success(request,"تم تعديل خانة فاتورة النقلة")

        model_affected = f'تعديل فاتورة نقلة رقم ({container_bill.id}): {", ".join(changes)}'
        RecentAction.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action_type='تعديل فاتورة نقلة',
            action_sort = 'نقلة',
            model_affected=model_affected,
        )

        return redirect('condetails', id=container_bill.container.id)

    context = {
        'container_bill': container_bill,
        'container_items': container_items,
        'old_container_bill_data': old_container_bill_data,
    }
    return render(request, 'containerbillupdate.html', context)
#====================================================================================================================
def container_bill_delete(request, id):
    container_bill = get_object_or_404(ContainerBill, id=id)

    if 'billDelete' in request.POST:
        container_id = container_bill.container.id
        total_bill_row = container_bill.total_bill_row

        RecentAction.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action_type='حذف خانة فاتورة',
            action_sort = 'نقلة',
            model_affected=f'حذف خانة فاتورة بقيمة ({total_bill_row} جنيها) للنقلة رقم ({container_id})',
        )

        container_bill.delete()
        messages.success(request,"تم حذف خانة فاتورة")
        return redirect("condetails", id=container_id)

    return render(request, 'containerbilldelete.html')
#====================================================================================================================
def container_expenses_delete(request, id):
    container_expenses_delete = get_object_or_404(ContainerExpense, id=id)

    if 'expenseDelete' in request.POST:
        container_id = container_expenses_delete.container.id
        expense_value = container_expenses_delete.expense

        RecentAction.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action_type='حذف مصروف نقلة',
            action_sort = 'نقلة',
            model_affected=f'حذف مصروف نقلة بقيمة ({expense_value} جنيها) للنقلة رقم ({container_id})',
        )

        container_expenses_delete.delete()
        messages.success(request,"تم حذف المصروف")
        return redirect("condetails", id=container_id)

    return render(request, 'containerexpensesdelete.html')
#====================================================================================================================
def container_items(request, id):
    container = get_object_or_404(Container, pk=id)
    items = Item.objects.all()
    context = {
        'container': container,
        'items': items
    }
    if request.method == 'POST':
        form_data = request.POST

        try:
            item_name = form_data['item_name']
            count = float(form_data['count'])
            tool = form_data['tool']
            price = float(form_data['price'])
            weight = form_data['weight']

            item_name = item_name.strip()

            if not price:
                raise ValueError("الرجاء إدخال السعر")
            
            if not weight:
                weight = 0

            if not count:
                raise ValueError("الرجاء إدخال العدد")

            item = Item.objects.filter(name=item_name).first()

            if not item:
                raise Item.DoesNotExist
        except ValueError as e:
            messages.error(request, str(e))
        except Item.DoesNotExist:
            messages.warning(request, f"الصنف {item_name} غير موجود برجاء إضافته")
        else:
            existing_item = ContainerItem.objects.filter(
                container=container,
                item__name=item_name,
            ).first()

            if existing_item:
                messages.warning(request, f"الصنف ({item_name}) موجود بالفعل في النقلة ")
            else:
                ContainerItem.objects.create(
                    container=container,
                    item=item,
                    count=count,
                    tool=tool,
                    price=price,
                    item_weight=weight
                )
                messages.success(request, "تم إضافة الصنف بنجاح")
                return redirect('containeritems', id)

    return render(request, 'containerItems.html', context)
#====================================================================================================================
def container_items_update(request, id):
    container_item = get_object_or_404(ContainerItem, id=id)
    items = Item.objects.all()

    # Capture the old data before updating
    old_data = model_to_dict(container_item)

    if request.method == "POST":
        item_name = request.POST.get('item_name')
        count = request.POST.get('count')
        tool = request.POST.get('tool')
        price = request.POST.get('price')
        weight = request.POST.get('weight')

        item_name = item_name.strip()

        if not item_name or not count or not tool or not price:
            messages.warning(request, "تأكد من أن جميع الخانات ممتلئة ببيانات صحيحة")
            return redirect("containeritems", id=container_item.container.id)
        if not weight:
            weight = 0

        try:
            new_item = Item.objects.get(name=item_name)
        except Item.DoesNotExist:
            messages.warning(request, "اسم الصنف غير موجود")
            return redirect("containeritems", id=container_item.container.id)

        try:
            total_sales_count = Sale.objects.filter(container_item=container_item).aggregate(total_count=Sum('count'))['total_count'] or 0
            if float(count) >= total_sales_count:
                remaining_count = float(count) - total_sales_count
            else:
                messages.warning(request, "العدد الجديد أقل من الذي تم بيعه في الترحيلات")
                return redirect("containeritems", id=container_item.container.id)


            container_item.item = new_item
            container_item.count = count
            container_item.tool = tool
            container_item.price = price
            container_item.item_weight = weight
            container_item.remaining_count = remaining_count
            container_item.save()

            # Capture the new data after updating
            new_data = model_to_dict(container_item)

            # Calculate changes
            changes = []
            for field in old_data.keys():
                if old_data[field] != new_data[field]:
                    field_label = {
                        'count': 'العدد',
                        'tool': 'العدة',
                        'price': 'السعر',
                        'item_weight': 'الوزن',
                        'item': f'الصنف من {Item.objects.get(id=old_data["item"]).name} إلى {Item.objects.get(id=new_data["item"]).name}',
                    }.get(field, field)
                    changes.append(f'{field_label} من {old_data[field]} إلى {new_data[field]}')

            # Log the action in RecentAction model
            RecentAction.objects.create(
                user=request.user if request.user.is_authenticated else None,
                action_type='تعديل صنف نقلة',
                action_sort = 'نقلة',
                model_affected=f'تم تعديل صنف النقلة {container_item.container.id} {Item.objects.get(id=old_data["item"]).name}: {", ".join(changes)}',
            )

            messages.success(request, 'تم تحديث بيانات الصنف بنجاح', extra_tags='success')
            return redirect("containeritems", id=container_item.container.id)

        except ValueError:
            messages.warning(request, 'تأكد من ان جميع البيانات صحيحة', extra_tags='warning')
            return redirect("containeritems", id=container_item.container.id)

#====================================================================================================================
def containeritem_delete(request, id):
    container_item_delete = get_object_or_404(ContainerItem, id=id)

    if 'containerItemDelete' in request.POST:
        # if Sale.objects.filter(container_item=container_item_delete).exists():
        #     messages.error(request, "هذا الصنف تم ادراجه في عملية بيع ,الحذف قد يسبب مشاكل تقنية")
        #     return redirect("containeritems", id=container_item_delete.container.id)
        # else:
        container_item_delete.delete()
        messages.success(request,"تم حذف الصنف من النقلة ")
        return redirect("containeritems", id=container_item_delete.container.id)
        
    elif 'containerItemDelete2' in request.POST:
        if Sale.objects.filter(container_item=container_item_delete).exists():
            messages.error(request, "هذا الصنف تم ادراجه في عملية بيع ,الحذف قد يسبب مشاكل تقنية")
            return redirect("condetails", id=container_item_delete.container.id)
        else:
            container_item_delete.delete()
            messages.success(request,"تم حذف الصنف من النقلة ")
            return redirect("condetails", id=container_item_delete.container.id)

    return render(request, 'containeritemdelete.html', {'container': container_item_delete.container})
#====================================================================================================================
@login_required(login_url="login")
def today_containers(request):
    egypt_tz = pytz.timezone('Africa/Cairo')
    todays_date = timezone.now().astimezone(egypt_tz).date() 
    containers = Container.objects.filter(date=todays_date) 
    context = {'container': containers} 

    return render(request, 'today.html', context)
#====================================================================================================================
@login_required(login_url="login")
def remain_containers(request):
    all_containers = Container.objects.all()
    remain_containers = [container for container in all_containers if container.total_remaining_count > 0]

    context = {
        'containers': remain_containers,
    }
    return render(request, 'remain.html', context)
#====================================================================================================================
@login_required(login_url="login")
def finished_containers(request):
    all_containers = Container.objects.all()
    finished_containers = [container for container in all_containers if container.total_remaining_count == 0]
    
    context = {
        'containers': finished_containers,
    }
    return render(request, 'finished.html', context)
#====================================================================================================================
@login_required(login_url="login")
def sell_container(request, id):
    seller_name = request.session.get('seller_name', '')
    items = Item.objects.all()
    container = get_object_or_404(Container, pk=id)
    sales = Sale.objects.filter(container=container).order_by('-date')
    sellers = Seller.objects.all()


    if request.method == "POST":
        if 'add_sale' in request.POST:
            seller_name = request.POST.get('seller')
            weight = request.POST.get('weight')
            count = request.POST.get('count')
            price = request.POST.get('price')
            tool = request.POST.get('tool')
            container_item_name = request.POST.get('container_item')
            date_str = request.POST.get('date')
            dept = request.POST.get('dept')

            if not dept:
                dept = 0

            try:
                seller = Seller.objects.get(name=seller_name)
            except Seller.DoesNotExist:
                messages.warning(request, f"اسم البائع ({seller_name}) غير موجود هل تريد إضافته")

                request.session['seller_name'] = seller_name

                return redirect('sellcon', id=id)

            try:
                container_item = ContainerItem.objects.get(container=container, item__name=container_item_name)

                if int(count) > container_item.remaining_count:
                    messages.error(request,
                                f"الكمية المدخلة {count} أكبر من الكمية المتبقية في الصنف و التي هي : {container_item.remaining_count}")
                    return redirect('sellcon', id=id)
            except ContainerItem.DoesNotExist:
                messages.error(request, "اسم الصنف غير موجود")
                return redirect('sellcon', id=id)

            if not date_str:
                egypt_tz = pytz.timezone('Africa/Cairo')
                date = timezone.now().astimezone(egypt_tz).date()
            else:
                try:
                    date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    messages.error(request, 'تاريخ غير صالح. يجب أن يكون الشكل YYYY-MM-DD', extra_tags='warning')
                    return redirect('sellcon', pk=id)

            new_sale = Sale.objects.create(
                seller=seller,
                container=container,
                date=date,
                weight=weight,
                count=count,
                price=price,
                container_item=container_item,
                tool=tool,
                dept=float(dept) * float(count)
            )

            RecentAction.objects.create(
                user=request.user if request.user.is_authenticated else None,
                action_type='عملية بيع',
                action_sort = 'بيع',
                model_affected=f'تم اضافة عملية بيع في النقلة رقم ({new_sale.container.id}) للبائع ({new_sale.seller.name}) من الصنف ({new_sale.container_item.item.name}) و بإجمالي سعر ({new_sale.total_sell_price} جنيه)',
            )

            messages.success(request, "تمت إضافة عملية بيع بنجاح")

            # Remove the stored seller_name from the session
            request.session.pop('seller_name', None)

            return redirect('sellcon', id=id)
        
        elif 'add_seller' in request.POST:
            seller_name = request.POST.get('new_seller')
            new_seller = Seller.objects.create(name=seller_name, place="-", seller_opening_balance=0)
            
            RecentAction.objects.create(
            user=request.user,
            action_type='إضافة بائع جديد',
            action_sort = 'بائعين',
            model_affected=f'اضافة عميل باسم ({new_seller.name}) برصيد افتتاحي قدره ({new_seller.seller_opening_balance} جنيه)',
            )

            messages.success(request, f"تم إضافة البائع {new_seller.name}")
            
            request.session.pop('seller_name', None)

            return redirect('sellcon', id=id)
    
    context = {
        'container': container,
        'sales': sales,
        'sellers': sellers,
        "items": items,
    }

    return render(request, 'sellcar.html', context)
#====================================================================================================================
def sale_delete(request, id):
    sale_to_delete = get_object_or_404(Sale, id=id)
    container_id = sale_to_delete.container.id 
    seller_id = sale_to_delete.seller.id 
    

    if 'deleteSale' in request.POST:
        RecentAction.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action_type='حذف عملية بيع',
            action_sort = 'بيع',
            model_affected=f'حذف عملية بيع في النقلة رقم ({sale_to_delete.container.id}) و التي كانت بإجمالي سعر ({sale_to_delete.total_sell_price}) من الصنف ({sale_to_delete.container_item.item.name})',
        )
        container_item = sale_to_delete.container_item

        if container_item:
            container_item.remaining_count = F('remaining_count') + sale_to_delete.count
            container_item.save()

        sale_to_delete.delete()
        messages.success(request,'تم حذف عملية بيع')
        return redirect("sellcon", id=container_id) 
    
    elif 'deleteSale2' in request.POST:
        RecentAction.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action_type='حذف عملية بيع',
            action_sort = 'بيع',
            model_affected=f'حذف عملية بيع في النقلة رقم ({sale_to_delete.container.id}) و التي كانت بإجمالي سعر ({sale_to_delete.total_sell_price}) من الصنف ({sale_to_delete.container_item.item.name})',
        )
        container_item = sale_to_delete.container_item

        if container_item:
            container_item.remaining_count = F('remaining_count') + sale_to_delete.count
            container_item.save()

        sale_to_delete.delete()
        messages.success(request,'تم حذف عملية بيع')
        return redirect("condetails", id=container_id) 
    
    elif 'deleteSale3' in request.POST:
        RecentAction.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action_type='حذف عملية بيع',
            action_sort = 'بيع',
            model_affected=f'حذف عملية بيع في النقلة رقم ({sale_to_delete.container.id}) و التي كانت بإجمالي سعر ({sale_to_delete.total_sell_price}) من الصنف ({sale_to_delete.container_item.item.name})',
        )
        container_item = sale_to_delete.container_item

        if container_item:
            container_item.remaining_count = F('remaining_count') + sale_to_delete.count
            container_item.save()

        sale_to_delete.delete()
        messages.success(request,'تم حذف عملية بيع')
        return redirect("sellerpage", id=seller_id) 
    
    

    context = {
        'sale': sale_to_delete,  
    }
    return render(request, "sellcar.html", context)
#====================================================================================================================
def sale_update(request, id):
    sale = get_object_or_404(Sale, id=id)
    container_id = sale.container.id
    sellers = Seller.objects.all()
    if request.method == 'POST':

        sale_to_delete = get_object_or_404(Sale, id=id)
        container_id = sale_to_delete.container.id  
        container_item = sale_to_delete.container_item

        if container_item:
            container_item.remaining_count = F('remaining_count') + sale_to_delete.count
            container_item.save()

        sale_to_delete.delete()


        container = sale.container
        sellers = Seller.objects.all()

        seller_name = request.POST.get('seller')
        weight = request.POST.get('weight')
        count = request.POST.get('count')
        price = request.POST.get('price')
        tool = request.POST.get('tool')
        container_item_name = request.POST.get('container_item')
        date_str = request.POST.get('date')
        dept = request.POST.get('dept')

        seller_name = seller_name.strip()
        container_item_name = container_item_name.strip()

        if not dept:
            dept = 0

        try:
            seller = Seller.objects.get(name=seller_name)
        except Seller.DoesNotExist:
            messages.warning(request, "اسم البائع غير موجود")
            return redirect('sellcon', id=container_id)

        try:
            container_item = ContainerItem.objects.get(container=container, item__name=container_item_name)

            if int(count) > container_item.remaining_count:
                messages.error(request,
                                f"الكمية المدخلة ({count}) أكبر من الكمية المتبقية في الصنف و التي هي : ({container_item.remaining_count})")
                return redirect('sellcon', id=container_id)
        except ContainerItem.DoesNotExist:
            messages.warning(request, "اسم الصنف غير موجود")
            return redirect('sellcon', id=container_id)

        if not date_str:
            egypt_tz = pytz.timezone('Africa/Cairo')
            date = timezone.now().astimezone(egypt_tz).date()
        else:
            try:
                date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                messages.warning(request, 'تاريخ غير صالح. يجب أن يكون الشكل YYYY-MM-DD', extra_tags='warning')
                return redirect('sellcon', pk=container_id)

        new_sale = Sale.objects.create(
            seller=seller,
            container=container,
            date=date,
            weight=weight,
            count=count,
            price=price,
            container_item=container_item,
            tool=tool,
            dept=float(dept) * float(count)
        )

        RecentAction.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action_type='عملية بيع مضافة بعد التعديل',
            action_sort = 'بيع',
            model_affected=f'تم اضافة عملية بيع بعد التعديل في النقلة رقم ({new_sale.container.id}) للبائع ({new_sale.seller.name}) من الصنف ({new_sale.container_item.item.name}) و بإجمالي سعر ({new_sale.total_sell_price} جنيه)',
        )

        messages.success(request, "تمت تعديل عملية بيع بنجاح")
        return redirect('sellcon', id=container_id)

    context = {
        'sale': sale,
        'sellers':sellers
    }

    return render(request, 'saleupdate.html', context)
#====================================================================================================================
def seller_sale_update(request, id):
    sale = get_object_or_404(Sale, id=id)
    seller_id = sale.seller.id
    sellers = Seller.objects.all()
    if request.method == 'POST':

        sale_delete(request, id)

        container = sale.container
        sellers = Seller.objects.all()

        seller_name = request.POST.get('seller')
        weight = request.POST.get('weight')
        count = request.POST.get('count')
        price = request.POST.get('price')
        tool = request.POST.get('tool')
        container_item_name = request.POST.get('container_item')
        date_str = request.POST.get('date')
        dept = request.POST.get('dept')

        seller_name = seller_name.strip()
        container_item_name = container_item_name.strip()

        if not dept:
            dept = 0

        try:
            seller = Seller.objects.get(name=seller_name)
        except Seller.DoesNotExist:
            messages.warning(request, "اسم البائع غير موجود")
            return redirect('sellerpage', id=seller_id)

        try:
            container_item = ContainerItem.objects.get(container=container, item__name=container_item_name)

            if int(count) > container_item.remaining_count:
                messages.error(request,
                                f"الكمية المدخلة ({count}) أكبر من الكمية المتبقية في الصنف و التي هي : ({container_item.remaining_count})")
                return redirect('sellerpage', id=seller_id)
        except ContainerItem.DoesNotExist:
            messages.warning(request, "اسم الصنف غير موجود")
            return redirect('sellerpage', id=seller_id)

        if not date_str:
            egypt_tz = pytz.timezone('Africa/Cairo')
            date = timezone.now().astimezone(egypt_tz).date()
        else:
            try:
                date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                messages.warning(request, 'تاريخ غير صالح. يجب أن يكون الشكل YYYY-MM-DD', extra_tags='warning')
                return redirect('sellerpage', pk=seller_id)

        new_sale = Sale.objects.create(
            seller=seller,
            container=container,
            date=date,
            weight=weight,
            count=count,
            price=price,
            container_item=container_item,
            tool=tool,
            dept=float(dept) * float(count)
        )

        RecentAction.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action_type='عملية بيع مضافة بعد التعديل',
            action_sort = 'بيع',
            model_affected=f'تم اضافة عملية بيع بعد التعديل في النقلة رقم ({new_sale.container.id}) للبائع ({new_sale.seller.name}) من الصنف ({new_sale.container_item.item.name}) و بإجمالي سعر ({new_sale.total_sell_price} جنيه)',
        )

        messages.success(request, "تمت تعديل عملية بيع بنجاح")
        return redirect('sellerpage', id=seller_id)

    context = {
        'sale': sale,
        'sellers':sellers
    }

    return render(request, 'sellersaleupdate.html', context)
#====================================================================================================================
#==============================================calculations=========================================================
#====================================================================================================================
#====================================================================================================================
@login_required(login_url="login")
def loses(request):
    loses = Lose.objects.all()
    context = {'loses': loses}

    if request.method == 'POST':
        amount = request.POST.get('amount')
        lose_type = request.POST.get('lose_type')
        date = request.POST.get('date')

        if float(amount) < 0:
            messages.error(request, "قيمة المصروف أقل من صفر")
            return redirect('loses')

        egypt_tz = pytz.timezone('Africa/Cairo')
        lose_instance = Lose(
            amount=float(amount),
            lose_type=lose_type,
            date=date if date else timezone.now().astimezone(egypt_tz).date(),
        )
        lose_instance.save()
        RecentAction.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action_type='اضافة مصروف',
            action_sort = 'مصروف',
            model_affected=f'تم اضافة مصروف قدره ({lose_instance.amount} جنيها)',
        )

        messages.success(request,"تم اضافة مصروف")
        return redirect('loses')

    return render(request, 'loses.html', context)
#====================================================================================================================
def loses_delete(request, id):
    loses_delete = get_object_or_404(Lose, id=id )
    if request.method == "POST":
        RecentAction.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action_type='حذف مصروف',
            action_sort = 'مصروف',
            model_affected=f'حذف مصروف كانت قيمته ({loses_delete.amount} جنيها)',
        )
        loses_delete.delete()
        messages.success(request,"تم حذف المصروف")
        return redirect("loses")
#====================================================================================================================
@login_required(login_url="login")
def profits(request):
    payments = Payment.objects.all()
    sel = Seller.objects.all()
    context = {
        'payments': payments,
        'sels': sel,
    }

    if request.method == "POST":
        seller_name = request.POST.get('seller')
        paid_money = request.POST.get('paid')
        forgive = request.POST.get('forgive')
        date_str = request.POST.get('date')

        if not seller_name:
            messages.warning(request, 'يجب إدخال اسم البائع')
            return redirect("profits")

        if not forgive:
            forgive = 0

        try:
            seller = Seller.objects.get(name=seller_name)
        except Seller.DoesNotExist:
            messages.warning(request, "اسم البائع غير موجود")
            return redirect("profits")

        if not paid_money:
            messages.warning(request, 'برجاء إدخال المبلغ')
            return redirect("profits")

        egypt_tz = pytz.timezone('Africa/Cairo')

        if not date_str:
            date = timezone.now().astimezone(egypt_tz).date()
        else:
            try:
                date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                messages.warning(request, 'تاريخ غير صالح. يجب أن يكون الشكل YYYY-MM-DD', extra_tags='warning')
                return redirect("profits")

        payment = Payment(
            seller=seller,
            paid_money=paid_money,
            forgive=forgive,
            date=date,
        )
        payment.save()
        payment.temp_rest = payment.rest
        payment.save()
        RecentAction.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action_type='عملية تحصيل او دفع',
            action_sort = 'تحصيل',
            model_affected=f'اضافة عملية تحصيل باسم البائع ({payment.seller.name}) و قدره ({payment.paid_money} جنيها) و قيمة سماح ({payment.forgive})',
        )

        messages.success(request, 'تم إضافة عملية دفع جديدة بنجاح', extra_tags='success')
        return redirect("profits")

    return render(request, 'profits.html', context)
#====================================================================================================================
def profits_update(request, id):
    payment = get_object_or_404(Payment, id=id)
    old_payment_data = None

    if request.method == "POST":
        paid_money = request.POST['paid_money']
        forgive = request.POST['forgive']
        date_str = request.POST['date']

        try:
            if date_str:
                date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            elif not paid_money:
                messages.error(request, "ادخل المبلغ")
                return redirect('profits')
            elif not forgive:
                messages.error(request, "اذا كانت قيمة السماح تساوي صفر , يرجى ادخال قيمة 0")
                return redirect('profits')
            else:
                old_payment_data = Payment.objects.filter(id=id).values().first()

                egypt_tz = pytz.timezone('Africa/Cairo')
                date = timezone.now().astimezone(egypt_tz).date()

            edit = Payment.objects.get(id=id)
            old_paid_money = old_payment_data['paid_money']
            old_forgive = old_payment_data['forgive']

            changes = []
            if paid_money != old_paid_money:
                changes.append(f'المبلغ المدفوع من {old_paid_money} جنيه إلى {paid_money} جنيه')
            if forgive != old_forgive:
                changes.append(f'قيمة السماح من {old_forgive or 0} جنيه إلى {forgive} جنيه')

            edit.paid_money = paid_money
            edit.forgive = forgive
            edit.date = date
            edit.save()
            edit.temp_rest = edit.rest
            edit.save()

            seller_name = payment.seller.name
            model_affected = f'تعديل عملية تحصيل رقم ({edit.id}) للبائع ({seller_name}): {", ".join(changes)}'
            RecentAction.objects.create(
                user=request.user if request.user.is_authenticated else None,
                action_sort = 'تحصيل',
                action_type='تعديل تحصيل او دفع',
                model_affected=model_affected,
            )

            messages.success(request, "تم تعديل عملية البيع بنجاح")
            return redirect("profits")
        except ValueError:
            messages.warning(request, 'تاريخ غير صالح. يجب أن يكون الشكل YYYY-MM-DD', extra_tags='warning')
            return redirect('profitsupdate', id=id)

    context = {'payment': payment, 'old_payment_data': old_payment_data}
    return render(request, 'profits.html', context)
#====================================================================================================================
def profits_delete(request, id):
    profits_delete = get_object_or_404(Payment, id=id )
    seller_id = profits_delete.seller.id

    if "deleteProfit2" in request.POST:
        RecentAction.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action_type='حذف عملية دفع',
            action_sort = 'تحصيل',
            model_affected=f'تم حذف عملية الدفع للعميل {profits_delete.seller.name} رقم ({profits_delete.id}) و التي كانت قيمتها ({profits_delete.paid_money})',
        )
        profits_delete.delete()
        messages.success(request,"تم حذف عملية تحصيل")
        return redirect("profits")
    
    elif "deleteProfit" in request.POST:
        RecentAction.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action_type='حذف عملية دفع',
            action_sort = 'تحصيل',
            model_affected=f'تم حذف عملية الدفع للعميل {profits_delete.seller.name} رقم ({profits_delete.id}) و التي كانت قيمتها ({profits_delete.paid_money})',
        )
        profits_delete.delete()
        messages.success(request,"تم حذف عملية تحصيل")
        return redirect("sellerpage", id= seller_id)

#====================================================================================================================
@login_required(login_url="login")
def day_money(request):
    if request.method == 'POST':
        date_str = request.POST.get('date')
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()

        egypt_tz = pytz.timezone('Africa/Cairo')
        selected_date = egypt_tz.localize(datetime.combine(selected_date, datetime.min.time())).date()

        total_payments = Payment.objects.filter(date__date=selected_date).aggregate(Sum('paid_money'))['paid_money__sum']
        total_payments = total_payments or 0  

        total_loses = Lose.objects.filter(date=selected_date).aggregate(Sum('amount'))['amount__sum']
        total_loses = total_loses or 0  

        remaining_amount = total_payments - total_loses

        return render(request, 'daymoney.html', {
            'total_payments': total_payments,
            'total_loses': total_loses,
            'remaining_amount': remaining_amount,
        })

    return render(request, 'daymoney.html', {'total_payments': None})
#====================================================================================================================
@login_required(login_url="login")
def wins(request):

    if request.method == 'POST':
        date_str = request.POST.get('date')
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()

        egypt_tz = pytz.timezone('Africa/Cairo')
        selected_date = egypt_tz.localize(datetime.combine(selected_date, datetime.min.time())).date()

        containers = Container.objects.filter(date=selected_date)
        loses = Lose.objects.filter(date = selected_date)
        forgives = Payment.objects.filter(date = selected_date)
        
        total_commission = sum(container.main_commission for container in containers)
        total_commission = total_commission or 0  

        total_loses = Lose.objects.filter(date=selected_date).aggregate(Sum('amount'))['amount__sum']
        total_loses = total_loses or 0  

        total_forgive = Payment.objects.filter(date=selected_date).aggregate(Sum('forgive'))['forgive__sum']
        total_forgive = total_forgive or 0  

        total_expenses = sum(container.total_con_expenses for container in containers)
        total_expenses = total_expenses or 0

        win = total_commission - (total_loses + total_forgive + total_expenses)

        return render(request, 'wins.html', {
            'total_commission': total_commission,
            'total_loses': total_loses,
            'total_forgive': total_forgive,
            'total_expenses': total_expenses,
            'win': win,
            'containers':containers,
            'forgives':forgives,
            'loses':loses,
            'selected_date' : selected_date
        })
    return render(request, 'wins.html', {'total_commission': None})
#====================================================================================================================
def month_money(request):
    if request.method == 'POST':
        month_str = request.POST.get('date')  
        selected_month = datetime.strptime(month_str, '%Y-%m').date()

        first_day = selected_month.replace(day=1)
        last_day = (selected_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        egypt_tz = pytz.timezone('Africa/Cairo')

        first_day = egypt_tz.localize(datetime.combine(first_day, datetime.min.time())).date()
        last_day = egypt_tz.localize(datetime.combine(last_day, datetime.max.time())).date()

        total_payments = Payment.objects.filter(date__range=(first_day, last_day)).aggregate(Sum('paid_money'))['paid_money__sum']
        total_payments = total_payments or 0  

        total_loses = Lose.objects.filter(date__range=(first_day, last_day)).aggregate(Sum('amount'))['amount__sum']
        total_loses = total_loses or 0  

        remaining_amount = total_payments - total_loses

        return render(request, 'monthmoney.html', {
            'total_payments': total_payments,
            'total_loses': total_loses,
            'remaining_amount': remaining_amount,
        })

    return render(request, 'monthmoney.html', {'total_payments': None})
#====================================================================================================================
#==================================================ITEMS=============================================================
#====================================================================================================================
#====================================================================================================================
@login_required(login_url="login")
def add_items(request):
    if 'addItem' in request.POST:
        name = request.POST.get('name')
        date_str = request.POST.get('date')

        if not name:
            messages.warning(request, 'يجب إدخال اسم الصنف')
            return redirect('items')

        elif not date_str:
            egypt_tz = pytz.timezone('Africa/Cairo')
            date = timezone.now().astimezone(egypt_tz).date()
        else:
            try:
                date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                messages.warning(request, 'تاريخ غير صالح. يجب أن يكون الشكل YYYY-MM-DD', extra_tags='warning')
                return redirect('items')

        existing_item = Item.objects.filter(name=name).first()

        if existing_item:
            messages.warning(request, f"الصنف '{name}' موجود بالفعل في قاعدة البيانات")
        else:
            # Create a new Item instance
            new_item = Item.objects.create(name=name, date=date)

            # Log the action in RecentAction model
            RecentAction.objects.create(
                user=request.user if request.user.is_authenticated else None,
                action_type='إضافة صنف جديد',
                action_sort = 'صنف',
                model_affected=f'إضافة صنف ({new_item.name})',
            )

            messages.success(request, "تم إضافة صنف جديد بنجاح")
            return redirect('items')

    items = Item.objects.all()
    context = {'items': items}

    return render(request, "kinds.html", context)
#====================================================================================================================
def item_update(request, id):
    old_item_data = None

    if 'updateItem' in request.POST:
        name = request.POST.get('name')
        date_str = request.POST.get('date')

        try:
            if date_str:
                date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            elif not name:
                messages.error(request, "اسم الصنف غير موجود")
                return redirect('itemupdate', id=id)
            else:
                old_item_data = Item.objects.filter(id=id).values().first()

                # Check if the updated name already exists in the database (excluding the current item)
                if Item.objects.filter(name=name).exclude(id=id).exists():
                    messages.warning(request, f'اسم الصنف ({name}) موجود بالفعل في قاعدة البيانات')
                    return redirect('itemupdate', id=id)

                egypt_tz = pytz.timezone('Africa/Cairo')
                date = timezone.now().astimezone(egypt_tz).date()

            edit = Item.objects.get(id=id)
            old_name = old_item_data['name']

            changes = []
            if name != old_name:
                changes.append(f'اسم الصنف من {old_name} إلى {name}')

            edit.name = name
            edit.date = date
            edit.save()

            RecentAction.objects.create(
                user=request.user if request.user.is_authenticated else None,
                action_type='تعديل صنف',
                action_sort = 'صنف',
                model_affected=f'تم تعديل بيانات الصنف: {", ".join(changes)}',
            )

            messages.success(request, 'تم تعديل بيانات الصنف بنجاح', extra_tags='success')
            return redirect("items")
        except ValueError:
            messages.warning(request, 'تاريخ غير صالح. يجب أن يكون الشكل YYYY-MM-DD', extra_tags='warning')
            return redirect('itemupdate', id=id)
        except Item.DoesNotExist:
            messages.error(request, 'حدث خطأ، الصنف غير موجود', extra_tags='error')
            return redirect("itemupdate", id=id)

    else:
        try:
            old_item_data = Item.objects.filter(id=id).values().first()
            item = Item.objects.get(id=id)
        except Item.DoesNotExist:
            messages.error(request, 'حدث خطأ، الصنف غير موجود', extra_tags='error')
            return redirect("itemupdate", id=id)

    context = {"item": item, "id": id, "old_item_data": old_item_data}

#====================================================================================================================
def item_delete(request,id):
    item_delete = get_object_or_404(Item, id=id )
    if request.method == "POST":
        RecentAction.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action_type='حذف صنف',
            action_sort = 'صنف',
            model_affected=f'تم حذف الصنف ({item_delete.name})',
        )
        item_delete.delete()
        messages.success(request,"تم حذف الصنف")
        return redirect("items")

#====================================================================================================================
#====================================================================================================================
#===========================================SELLER & SUPPLIER=========================================================================
#====================================================================================================================
#====================================================================================================================
@login_required(login_url="login")
def seller_accounts(request):
    seller = Seller.objects.all()
    context = {'seller': seller}

    if 'addSeller' in request.POST:
        name = request.POST.get('name')
        place = request.POST.get('place', 'غير محدد')  
        date_str = request.POST.get('date')
        seller_opening_balance = request.POST.get('seller_opening_balance')

        name = name.strip()
        place = place.strip()

        if not name:
            messages.warning(request, 'يجب إدخال اسم البائع')
            return redirect('selleraccounts')
        if not place:
            place = "-"
        if not seller_opening_balance:
            seller_opening_balance = 0

        if Seller.objects.filter(name=name).exists():
            messages.warning(request, f'اسم البائع ({name}) موجود بالفعل في قاعدة البيانات')
            return redirect('selleraccounts')

        if not date_str:
            egypt_tz = pytz.timezone('Africa/Cairo')
            date = timezone.now().astimezone(egypt_tz).date()
        else:
            try:
                date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                messages.warning(request, 'تاريخ غير صالح. يجب أن يكون الشكل YYYY-MM-DD', extra_tags='warning')
                return redirect('selleraccounts')

        new_seller = Seller.objects.create(name=name, place=place, date=date, seller_opening_balance=seller_opening_balance)
        RecentAction.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action_type='إضافة بائع جديد',
            action_sort = 'بائع',
            model_affected=f'تم إضافة بائع جديد باسم ({new_seller.name}) برصيد افتتاحي قدره ({new_seller.seller_opening_balance} جنيها)',
        )

        messages.success(request, 'تم إضافة بائع جديد بنجاح', extra_tags='success')
        return redirect('selleraccounts')

    return render(request, 'sellersaccounts.html', context)
#====================================================================================================================
@login_required(login_url="login")
def seller_page(request, id):
    seller = get_object_or_404(Seller, id=id)
    payments = Payment.objects.filter(seller=seller).order_by('-date')
    sales = Sale.objects.filter(seller=seller).order_by('-date')
    sales_by_date = Sale.objects.filter(seller=seller).values('date').annotate(
        total_meal=Sum('total_sell_price')
    )
    context = {
        'seller': seller,
        'payments': payments,
        'sales': sales,
        'sales_by_date': sales_by_date, 
    }

    if request.method == "POST":
        if 'profits' in request.POST:
            seller_name = request.POST.get('seller')  
            paid_money = request.POST.get('paid')
            forgive = request.POST.get('forgive')
            date_str = request.POST.get('date')

            if not seller_name:
                messages.warning(request, 'يجب إدخال اسم البائع')
                return redirect('sellerpage', id=id)

            if not forgive:
                forgive = 0

            try:
                seller = Seller.objects.get(name=seller_name)
            except Seller.DoesNotExist:
                messages.warning(request, "اسم البائع غير موجود")
                return redirect('sellerpage', id=id)

            if not paid_money:
                messages.warning(request, 'برجاء إدخال المبلغ')
                return redirect('sellerpage', id=id)

            if not date_str:
                egypt_tz = pytz.timezone('Africa/Cairo')
                date = timezone.now().astimezone(egypt_tz).date()
            else:
                try:
                    date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    messages.warning(request, 'تاريخ غير صالح. يجب أن يكون الشكل YYYY-MM-DD', extra_tags='warning')
                    return redirect('sellerpage', pk=id)
                
            payment = Payment(
                seller=seller,
                paid_money=paid_money,
                forgive=forgive,
                date=date,
            )
            payment.save()

            # Update temp_rest to the new value of rest after saving
            payment.temp_rest = payment.rest
            payment.save()

            RecentAction.objects.create(
                user=request.user if request.user.is_authenticated else None,
                action_type='عملية تحصيل او دفع',
                action_sort = 'تحصيل',
                model_affected=f'اضافة عملية تحصيل باسم البائع ({payment.seller.name}) و قدره ({payment.paid_money} جنيها)',
            )
            messages.success(request, 'تم إضافة عملية دفع جديدة بنجاح', extra_tags='success')
            return redirect('sellerpage', id=id)
        
        elif 'dept' in request.POST:
            dept_str = request.POST['dept']
            sale_id = request.POST['sale_id']  
            sale = get_object_or_404(Sale, id=sale_id)  

            try:
                dept_decimal = Decimal(dept_str.replace(",", "."))
            except InvalidOperation:
                try:
                    dept_decimal = float(dept_str)
                except ValueError:
                    messages.error(request, 'قيمة الرهن يجب أن تكون رقمًا عشريًا صالحًا')
                    return redirect('sellerpage', id=id)
            except:
                sale.dept = dept_decimal
                sale.save()
                messages.success(request, 'تم تعديل الرهن')
            


    return render(request, 'sellerpage.html', context)
#====================================================================================================================
def dept_update(request, id):
    sale = get_object_or_404(Sale, id=id)

    if request.method == "POST":
        dept_str = request.POST['dept']
        old_dept_str = sale.dept  # Store the old dept value before updating

        sale.dept = dept_str
        sale.save()

        RecentAction.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action_type='تعديل رهن',
            action_sort = 'بائع',
            model_affected=f'تم تعديل قيمة الرهن من ({old_dept_str}) إلى ({dept_str}) لعملية البيع رقم ({sale.id}) للبائع ({sale.seller.name})',
        )

        messages.success(request, 'تم تعديل الرهن بنجاح')
        return redirect('sellerpage', id=sale.seller.id)

    return render(request, 'deptupdate.html', {'id': id, 'sale': sale})
#====================================================================================================================
def seller_update(request, id):
    old_seller_data = None

    if 'updateSeller' in request.POST:
        name = request.POST['name']
        place = request.POST['place']
        date_str = request.POST['date']
        seller_opening_balance = request.POST['seller_opening_balance']

        name = name.strip()
        place = place.strip()

        try:
            if date_str:
                date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            elif not name:
                messages.error(request, "اسم البائع غير موجود")
                return redirect('sellerupdate', id=id)
            elif not seller_opening_balance:
                messages.error(request, "إذا كان الرصيد الافتتاحي يساوي صفر , يرجى إدخال صفر")
                return redirect('sellerupdate', id=id)
            elif not place:
                messages.error(request, "يرجى إدخال المنطقة")
                return redirect('sellerupdate', id=id)
            else:
                old_seller_data = Seller.objects.filter(id=id).values().first()

                # Check if the updated name already exists in the database (excluding the current seller)
                if Seller.objects.filter(name=name).exclude(id=id).exists():
                    messages.warning(request, f'اسم البائع ({name}) موجود بالفعل في قاعدة البيانات')
                    return redirect('sellerupdate', id=id)

                egypt_tz = pytz.timezone('Africa/Cairo')
                date = timezone.now().astimezone(egypt_tz).date()

            edit = Seller.objects.get(id=id)
            old_name = old_seller_data['name']
            old_opening_balance = old_seller_data['seller_opening_balance']

            changes = []
            if name != old_name:
                changes.append(f'اسم البائع من {old_name} إلى {name}')
            if str(seller_opening_balance) != str(old_opening_balance):
                changes.append(f'رصيد الافتتاح من {old_opening_balance} إلى {seller_opening_balance}')

            edit.name = name
            edit.place = place
            edit.seller_opening_balance = seller_opening_balance
            edit.date = date
            edit.save()

            RecentAction.objects.create(
                user=request.user if request.user.is_authenticated else None,
                action_type='تعديل بائع',
                action_sort = 'بائع',
                model_affected=f'تم تعديل بيانات البائع: {", ".join(changes)}',
            )

            messages.success(request, 'تم تعديل بيانات البائع بنجاح', extra_tags='success')
            return redirect("selleraccounts")
        except ValueError:
            messages.warning(request, 'تاريخ غير صالح. يجب أن يكون الشكل YYYY-MM-DD', extra_tags='warning')
            return redirect('sellerupdate', id=id)
        except Seller.DoesNotExist:
            messages.error(request, 'حدث خطأ، البائع غير موجود', extra_tags='error')
            return redirect("selleraccounts")

    else: 
        try:
            old_seller_data = Seller.objects.filter(id=id).values().first()
            seller = Seller.objects.get(id=id)  
        except Seller.DoesNotExist:
            messages.error(request, 'حدث خطأ، البائع غير موجود', extra_tags='error')
            return redirect("selleraccounts")

    context = {"seller": seller, "id": id, "old_seller_data": old_seller_data}
    return render(request, 'sellerupdate.html', context)
#====================================================================================================================
def seller_delete(request, id):
    seller_to_delete = get_object_or_404(Seller, id=id)

    if 'deleteSeller' in request.POST:
        RecentAction.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action_type='حذف بائع',
            action_sort = 'بائع',
            model_affected=f'تم حذف البائع ({seller_to_delete.name})',
        )
        seller_to_delete.delete()
        messages.success(request, "تم حذف البائع بنجاح")
        return redirect("selleraccounts")

    return render(request, "sellerdelete.html")
#====================================================================================================================
@login_required(login_url="login")
def seller_sort(request):
    seller = Seller.objects.all()
    context = {'seller':seller}
    return render(request, 'sellersort.html', context)
#====================================================================================================================
@login_required(login_url="login")
def suppliers_accounts(request):
    sup = Supplier.objects.all()
    context = {'sup': sup}

    if request.method == "POST":
        name = request.POST.get('name')
        place = request.POST.get('place', 'غير محدد')  
        date_str = request.POST.get('date')
        opening_balance = request.POST.get('opening_balance')

        name = name.strip()
        place = place.strip()

        if not name:
            messages.warning(request, 'يجب إدخال اسم العميل')
            return redirect('suppliersaccounts')
        if not place:
            place = "-"
        if not opening_balance:
            opening_balance = 0

        if Supplier.objects.filter(name=name).exists():
            messages.warning(request, f'اسم العميل ({name}) موجود بالفعل في قاعدة البيانات')
            return redirect('suppliersaccounts')

        if not date_str:
            egypt_tz = pytz.timezone('Africa/Cairo')
            date = timezone.now().astimezone(egypt_tz).date()
        else:
            try:
                date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                messages.warning(request, 'تاريخ غير صالح. يجب أن يكون الشكل YYYY-MM-DD', extra_tags='warning')
                return redirect('suppliersaccounts')

        new_supplier = Supplier.objects.create(name=name, place=place, date=date, opening_balance=opening_balance)

        RecentAction.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action_type='إضافة عميل جديد',
            action_sort = 'عميل',
            model_affected=f'اضافة عميل باسم ({new_supplier.name}) برصيد افتتاحي قدره ({new_supplier.opening_balance} جنيه)',
        )

        messages.success(request, 'تم إضافة عميل جديد بنجاح', extra_tags='success')
        return redirect('suppliersaccounts')

    return render(request, 'suppliersaccounts.html', context)
#====================================================================================================================\
@login_required(login_url="login")
def supplier_sort(request):
    sup = Supplier.objects.all()
    context = {'sup': sup}
    return render(request,'suppliersort.html',context)
#====================================================================================================================
@login_required(login_url="login")
def supplier_page(request, id):
    sup = get_object_or_404(Supplier, id=id)
    containers = sup.container_set.all()
    context = {'sup': sup, 'containers': containers}
    return render(request, 'supplierpage2.html', context)
#====================================================================================================================
@login_required(login_url="login")
def supplier_update(request, id):
    old_supplier_data = None

    if request.method == "POST":
        name = request.POST['name']
        place = request.POST['place']
        opening_balance = request.POST['opening_balance']
        date_str = request.POST['date']

        name = name.strip()
        place = place.strip()

        try:
            if date_str:
                date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            elif not opening_balance:
                messages.error(request, "إذا كان الرصيد الافتتاحي يساوي صفر فيرجى إدخال صفر")
                return redirect('supplierupdate', id=id)
            elif not name:
                messages.error(request, "اسم العميل غير موجود")
                return redirect('supplierupdate', id=id)
            elif not place:
                messages.error(request, "يرجى إدخال المنطقة")
                return redirect('supplierupdate', id=id)
            else:
                old_supplier_data = Supplier.objects.filter(id=id).values().first()

                # Check if the updated name already exists in the database (excluding the current supplier)
                if Supplier.objects.filter(name=name).exclude(id=id).exists():
                    messages.warning(request, f'اسم العميل ({name}) موجود بالفعل في قاعدة البيانات')
                    return redirect('supplierupdate', id=id)

                egypt_tz = pytz.timezone('Africa/Cairo')
                date = timezone.now().astimezone(egypt_tz).date()

            edit = Supplier.objects.get(id=id)
            old_name = old_supplier_data['name']
            old_opening_balance = old_supplier_data['opening_balance']

            changes = []
            if name != old_name:
                changes.append(f'اسم العميل من {old_name} إلى {name}')
            if opening_balance != str(old_opening_balance):
                changes.append(f'رصيد الافتتاح من {old_opening_balance} إلى {opening_balance}')

            edit.name = name
            edit.place = place
            edit.opening_balance = opening_balance
            edit.date = date
            edit.save()

            RecentAction.objects.create(
                user=request.user if request.user.is_authenticated else None,
                action_type='تعديل عميل',
                action_sort = 'عميل',
                model_affected=f'تم تعديل بيانات العميل: {", ".join(changes)}',
            )

            messages.success(request, 'تم تعديل بيانات العميل بنجاح', extra_tags='success')
            return redirect("suppliersaccounts")
        except ValueError:
            messages.warning(request, 'تاريخ غير صالح. يجب أن يكون الشكل YYYY-MM-DD', extra_tags='warning')
            return redirect('supplierupdate', id=id)
        except Supplier.DoesNotExist:
            messages.error(request, 'حدث خطأ، العميل غير موجود', extra_tags='error')
            return redirect("suppliersaccounts")

    else: 
        try:
            old_supplier_data = Supplier.objects.filter(id=id).values().first()
            sup = get_object_or_404(Supplier, id=id)
        except Supplier.DoesNotExist:
            messages.error(request, 'حدث خطأ، العميل غير موجود', extra_tags='error')
            return redirect("suppliersaccounts")

    context = {"sup": sup, "id": id, "old_supplier_data": old_supplier_data}
    return render(request, 'supplierupdate.html', context)
#====================================================================================================================
def supplier_delete(request, id):
    supplier_to_delete = get_object_or_404(Supplier, id=id)
   

    if request.method == "POST":
        RecentAction.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action_type='حذف عميل',
            action_sort = 'عميل',
            model_affected=f'تم حذف العميل ({supplier_to_delete.name})',
        )
        supplier_to_delete.delete()
        messages.success(request, "تم حذف العميل بنجاح")
        return redirect("suppliersaccounts")

    return render(request, 'suppliersdelete.html')
#====================================================================================================================
@login_required(login_url="login")
def supplier_profits(request):
    sup = Supplier.objects.all()
    pay = SupplierPay.objects.all()
    context = {
        'sup': sup,
        'pay': pay,
    }

    if request.method == "POST":
        supplier_name = request.POST.get('supplier')
        pay_amount = request.POST.get('pay')  
        date_str = request.POST.get('date')
    
        supplier_name = supplier_name.strip()

        if not supplier_name:
            messages.warning(request, 'يجب إدخال اسم العميل')
            return redirect('supplierprofits')
        if not pay_amount:
            messages.warning(request, 'برجاء إدخال المبلغ')
            return redirect('supplierprofits')
        if not date_str:
            egypt_tz = pytz.timezone('Africa/Cairo')
            date = timezone.now().astimezone(egypt_tz).date()
        else:
            try:
                date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                messages.warning(request, 'تاريخ غير صالح. يجب أن يكون الشكل YYYY-MM-DD', extra_tags='warning')
                return redirect('supplierprofits')

        try:
            supplier = Supplier.objects.get(name=supplier_name)
        except Supplier.DoesNotExist:
            messages.warning(request, 'اسم العميل غير موجود')
            return redirect('supplierprofits')

        new_supplier_pay = SupplierPay.objects.create(supplier=supplier, pay=pay_amount, date=date)

        RecentAction.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action_type='صرف نقدية لعميل ',
            action_sort = 'عميل',
            model_affected=f'تسجيل صرف نقدية للعميل ({new_supplier_pay.supplier.name}) بمقدار ({new_supplier_pay.pay} جنيه)',
        )

        messages.success(request, 'تم إضافة صرف نقدية بنجاح', extra_tags='success')
        return redirect('supplierprofits')

    return render(request, 'supplierprofits.html', context)
#====================================================================================================================
def supplier_profits_delete(request, id):
    supplier_profit_to_delete = get_object_or_404(SupplierPay, id=id)

    if request.method == "POST":
        RecentAction.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action_type='حذف صرف نقدية',
            action_sort = 'عميل',
            model_affected=f'حذف صرف النقدية للعميل ({supplier_profit_to_delete.supplier.name}) و كان مبلغ قدره ({supplier_profit_to_delete.pay} جنيه ) ',
    )
        supplier_profit_to_delete.delete()
        messages.success(request, "تم حذف صرف النقدية بنجاح")
        return redirect("supplierprofits")

#====================================================================================================================
@login_required(login_url="login")
def admin_page(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        firstname = request.POST.get('firstname')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'اسم المستخدم موجود بالفعل')
            return redirect('reports')

        User.objects.create_user(username=username, password=password, first_name=firstname)
        messages.success(request, 'تم تسجيل مستخدم جديد بنجاح')
        return redirect('reports')  
    recent_actions = RecentAction.objects.all().order_by('-timestamp')
    context = {
        'recent_actions': recent_actions,
        'users' : User.objects.all()
    }
    return render(request, 'reports.html', context)
#====================================================================================================================
def user_delete(request, id):
    user_to_delete = get_object_or_404(User, id=id)
    if request.method == "POST":
        user_to_delete.delete()
        messages.success(request, "تم حذف المستخدم بنجاح")
        return redirect("reports")

    return render(request, 'userdelete.html')
#====================================================================================================================
def worker(request):
    workers = Worker.objects.all()
    loans = Loan.objects.all()

    if "addWorker" in request.POST:
        name = request.POST.get('name')
        job = request.POST.get('job')
        salary = request.POST.get('salary')

        if Worker.objects.filter(name=name).exists():
            messages.error(request, f'اسم الموظف ({name}) موجود بالفعل في قاعدة البيانات')
            return redirect('workers')
        
        else:
            Worker.objects.create(name=name, job=job, salary=salary)
            messages.success(request,"تم إضافة موظف جديد")
            return redirect('workers')
        
    elif "addLoan" in request.POST:
        worker_id = request.POST.get('worker')
        amount = request.POST.get('amount')
        date_str = request.POST.get('date')
        
        if not date_str:
            egypt_tz = pytz.timezone('Africa/Cairo')
            date = timezone.now().astimezone(egypt_tz).date()
        else:
            try:
                date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                messages.warning(request, 'تاريخ غير صالح. يجب أن يكون الشكل YYYY-MM-DD', extra_tags='warning')
                return redirect('workers')

        worker = Worker.objects.get(pk=int(worker_id))

        Loan.objects.create(worker=worker, amount=amount, date=date)
        messages.success(request,"تم اضافة سلفة")
        return redirect('workers')
    
    # elif "deleteLoan" in request.POST:
    #     loan_to_delete = get_object_or_404(Loan, id=id )
    #     loan_to_delete.delete()
    #     messages.success(request, "تم حذف السلفة")
    #     return redirect('workers')

    elif "deleteAllLoans" in request.POST:
        loans.delete()
        messages.success(request, "تم حذف جميع السلف")
        return redirect('workers')
        
    context={
        'workers':workers,
        'loans' :loans, 
        }
    return render(request,'workers.html', context)
#====================================================================================================================
def loan_delete(request, id):
    loan_to_delete = get_object_or_404(Loan, id=id)
    if request.method == "POST":
        loan_to_delete.delete()
        messages.success(request, "تم حذف السلفة بنجاح")
        return redirect("workers")
    return render(request)
#====================================================================================================================
def worker_delete(request, id):
    worker_to_delete = get_object_or_404(Worker, id=id)
    if request.method == "POST":
        worker_to_delete.delete()
        messages.success(request, "تم حذف الموظف بنجاح")
        return redirect("workers")
    return render(request)
#====================================================================================================================