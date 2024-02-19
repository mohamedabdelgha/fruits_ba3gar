from django.db import models
from django.utils import timezone
from django.db.models import Sum
from decimal import Decimal
from django.contrib.auth.models import User

# ===================================================================================================
class Supplier(models.Model):
    name = models.CharField(max_length=100)
    place = models.CharField(max_length=100, default='غير محدد')
    date = models.DateField(default=timezone.now)
    opening_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    @property
    def balance(self):
        total_sale_price = sum(container.total_sale_price for container in self.container_set.all())
        total_pay = self.supplierpay_set.aggregate(total_pay=Sum('pay'))['total_pay'] or 0

        return total_sale_price + self.opening_balance - total_pay

    @property
    def num_of_containers(self):
        return self.container_set.count()

    def __str__(self):
        return f"{self.name}"
# ===================================================================================================
class Seller(models.Model):
    name = models.CharField(max_length=100)
    place = models.CharField(max_length=100, default='غير محدد')
    date = models.DateField(default=timezone.now)
    seller_opening_balance = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    total_money = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    on_him = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    # total_dept = models.DecimalField(max_digits=15, decimal_places=2,default =0)
    
    @property
    def on_him(self):
        payments = Payment.objects.filter(seller=self)
        total_paid = sum((payment.paid_money + payment.forgive or 0) for payment in payments)
        return self.total_money + self.seller_opening_balance - total_paid

    @property
    def total_money(self):
        return sum(sale.total_sell_price for sale in self.sale_set.all()) or 0
    

    def __str__(self):
        return self.name
# ===================================================================================================
class Item(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    date = models.DateField(default=timezone.now)

    def __str__(self):
        return self.name
# ===================================================================================================
class Container(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, null=True)
    date = models.DateField()
    type = models.CharField(max_length=100, default='عمولة')
    num_sold_items = models.PositiveIntegerField(blank=True, null=True)
    num_not_sold_items = models.PositiveIntegerField(blank=True, null=True)
    total_con_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, editable=False)
    con_weight = models.PositiveBigIntegerField(editable=False, null=True)

    commission = models.PositiveIntegerField(blank=True, null=True, default=0)
    carry = models.PositiveIntegerField(blank=True, null=True, default=0)
    tool_rent = models.PositiveIntegerField(blank=True, null=True, default=0)

    @property
    def main_commission(self):
        if self.commission is not None:
            commission_decimal = Decimal(self.commission)
            return (commission_decimal / 100) * self.total_sale_price
        return 0

    @property
    def bill_commission(self):
        if self.commission is not None:
            return (Decimal(self.commission) / 100) * self.total_bill_price
        return 0

    @property
    def total_remaining_count(self):
        return self.main_total_count - self.total_sold_count

    @property
    def total_sold_count(self):
        return self.sale_set.aggregate(total_sold_count=Sum('count'))['total_sold_count'] or 0

    @property
    def total_sale_price(self):
        return self.sale_set.aggregate(total_sale_price=Sum('total_sell_price'))['total_sale_price'] or 0

    @property
    def total_sale_weight(self):
        return self.sale_set.aggregate(total_sale_weight=Sum('weight'))['total_sale_weight'] or 0

    @property
    def weight_difference(self):
        return self.total_sale_weight - self.con_weight

    @property
    def price_difference(self):
        return self.total_sale_price - self.total_con_price

    @property
    def total_con_price(self):
        return sum(item.total_item_price for item in self.containeritem_set.all()) or 0

    @property
    def con_weight(self):
        return self.containeritem_set.aggregate(total_weight=Sum('item_weight'))['total_weight'] or 0

    @property
    def main_total_count(self):
        return self.containeritem_set.aggregate(total_count=Sum('count'))['total_count'] or 0

    @property
    def num_of_items(self):
        return self.containeritem_set.count()

    @property
    def total_bill_price(self):
        return self.containerbill_set.aggregate(total_bill_price=Sum('total_bill_row'))['total_bill_price'] or 0

    @property
    def total_bill_weight(self):
        return self.containerbill_set.aggregate(total_bill_weight=Sum('weight'))['total_bill_weight'] or 0

    @property
    def total_con_expenses(self):
        return self.containerexpense_set.aggregate(total_con_expenses=Sum('expense'))['total_con_expenses'] or 0

    @property
    def win(self):
        return float(self.main_commission + self.carry + self.tool_rent)

    @property
    def bill_win(self):
        return float(self.bill_commission + self.carry + self.tool_rent)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Container {self.id} - {self.date}"
# ===================================================================================================
class ContainerItem(models.Model):  
    container = models.ForeignKey(Container, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    count = models.PositiveIntegerField()
    tool = models.CharField(max_length=100, default="صناديق")
    price = models.DecimalField(max_digits=5, decimal_places=2, null=False)
    item_weight = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_item_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, editable=False)
    remaining_count = models.PositiveIntegerField(editable=False, null=True)

    
    @property
    def total_item_price(self):
        if self.item_weight and self.price:
            return self.item_weight * self.price
        return 0

    def save(self, *args, **kwargs):
        if self.remaining_count is None:
            self.remaining_count = self.count

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.item.name}"
# ===================================================================================================
class Sale(models.Model):
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE, null=True)
    container = models.ForeignKey(Container, on_delete=models.CASCADE)  
    container_item = models.ForeignKey(ContainerItem, on_delete=models.CASCADE, null=True)
    count = models.PositiveIntegerField()
    weight = models.DecimalField(max_digits=10, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total_sell_price = models.DecimalField(max_digits=15, decimal_places=2, editable=False)
    tool = models.CharField(max_length=100)
    date = models.DateField(default=timezone.now)
    meal = models.DecimalField(max_digits=15, decimal_places=2, editable=False, null=True)
    dept = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        try:
            count = int(self.count)

            container_item = self.container_item
            if container_item:
                container_item.remaining_count = max(0, container_item.remaining_count - count)
                container_item.save()

            price = float(self.price)
            weight = float(self.weight)
            dept = float(self.dept)
            self.total_sell_price = price * weight + dept

            # Calculate meal for the same day
            same_day_sales = Sale.objects.filter(date=self.date).aggregate(total_meal=Sum('total_sell_price'))['total_meal']
            self.meal = same_day_sales or self.total_sell_price

        except (TypeError, ValueError):
            # Handle the case where 'count', 'price', or 'weight' is not a valid numeric type
            self.total_sell_price = 0
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Sale {self.id} {self.container_item} by {self.seller}"
# ===================================================================================================
class Payment(models.Model):
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE)
    date = models.DateTimeField(default=timezone.now)
    paid_money = models.DecimalField(max_digits=15, decimal_places=2)
    forgive = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    rest = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    notes = models.CharField(max_length=120, blank=True, null=True )
    total_paid = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    temp_rest = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, editable=False)
    
    def save(self, *args, **kwargs):
        # Set temp_rest to the current value of rest before saving
        self.temp_rest = self.rest
        super().save(*args, **kwargs)

    @property
    def total_paid(self):
        return sum(
            (payment.paid_money + payment.forgive or 0)
            for payment in Payment.objects.filter(seller=self.seller)
        )

    @property
    def rest(self):
        return self.seller.total_money - self.total_paid

    def __str__(self):
        return f"{self.id} - {self.date}"

# ===================================================================================================
class Lose(models.Model):
    amount = models.PositiveIntegerField()
    date = models.DateField(default=timezone.now)
    lose_type = models.CharField(max_length=100, default="غير معروف")

# ===================================================================================================
class ContainerExpense(models.Model):
    container = models.ForeignKey(Container, on_delete=models.CASCADE)
    expense = models.DecimalField(max_digits=10, decimal_places=2)
    expense_type = models.CharField(max_length=100, default="غير معروف")
    expense_notes = models.CharField(max_length=100)

    def __str__(self):
        return f"Expense for Container {self.container.id} - {self.expense_type}"
# ===================================================================================================
class ContainerBill(models.Model):
    container = models.ForeignKey(Container, on_delete=models.CASCADE)
    container_item = models.ForeignKey(ContainerItem, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    weight = models.DecimalField(max_digits=10, decimal_places=2)
    count = models.PositiveIntegerField()
    total_bill_row = models.DecimalField(max_digits=15, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        try:
            price = float(self.price)
            weight = float(self.weight)

            self.total_bill_row = price * weight
        except (ValueError, TypeError):
            self.total_bill_row = 0

        super().save(*args, **kwargs)
    def __str__(self):
        return f"ContainerBill {self.id} for Container {self.container.id}"
# ===================================================================================================
class SupplierPay(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    pay = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Payment to {self.supplier} - {self.date}"    
# ===================================================================================================
class RecentAction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action_type = models.CharField(max_length=100,blank=True, null=True)  
    action_sort = models.CharField(max_length=100,blank=True, null=True)  
    model_affected = models.CharField(max_length=100,blank=True, null=True)  
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.action_type} - {self.model_affected}"
# ===================================================================================================
class Worker(models.Model):
    name = models.CharField(max_length=255)
    job = models.CharField(max_length=255)
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)

    @property
    def total_loan(self):
        return self.loan_set.aggregate(total_loan=models.Sum('amount'))['total_loan'] or 0

    @property
    def rest_salary(self):
        return self.salary - self.total_loan

    def __str__(self):
        return f"Worker {self.name}"
# ===================================================================================================
class Loan(models.Model):
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)
    def __str__(self):
        return f"Loan {self.amount} for {self.worker.name}"
