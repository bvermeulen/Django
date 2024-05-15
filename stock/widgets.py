from django.forms import DateInput


class FengyuanChenDatePickerInput(DateInput):
    template_name = "finance/widgets/fengyuanchen_datepicker.html"
