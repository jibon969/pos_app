
# # Payment model to handle different payment methods for each sale
# class Payment(models.Model):
#     PAYMENT_METHOD_CHOICES = (
#         ('CASH', 'Cash'),
#         ('CARD', 'Card'), 
#         ('MOBILE', 'Mobile Payment'),
#     )

#     sale = models.ForeignKey(Sale, related_name='payments', on_delete=models.CASCADE)
#     payment_method = models.CharField(choices=PAYMENT_METHOD_CHOICES, max_length=10)
#     amount = models.DecimalField(max_digits=10, decimal_places=2)

#     def __str__(self):
#         return f"Payment Method: {self.payment_method} | Amount: {self.amount}"
