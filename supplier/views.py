from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from .models import (RfqSupplierHeader,RfqSupplierDetail,
                    QuotationHeaderSupplier, QuotationDetailSupplier,
                    PoHeaderSupplier, PoDetailSupplier,
                    DcHeaderSupplier, DcDetailSupplier,
                    Company_info)
from customer.models import (DcHeaderCustomer, PoHeaderCustomer, QuotationHeaderCustomer, RfqCustomerHeader)
from inventory.models import Add_products
from transaction.models import ChartOfAccount
from django.core import serializers
from django.forms.models import model_to_dict
import json
import datetime
from django.db import IntegrityError
from django.conf import settings
from django.views.generic import View
from .utils import render_to_pdf
from django.template.loader import get_template
from django.db import connection
import xlwt
from django.contrib.auth.models import User

def home(request):
    today = datetime.date.today()
    cursor = connection.cursor()
    cursor.execute('''select rfq_no , date, account_id_id
                    from customer_rfqcustomerheader
                    where customer_rfqcustomerheader.show_notification = 1 and customer_rfqcustomerheader.follow_up = %s
                    union
                    select quotation_no, date, account_id_id
                    from customer_quotationheadercustomer
                    where customer_quotationheadercustomer.show_notification = 1 and customer_quotationheadercustomer.follow_up = %s
                    union
                    select po_no, date, account_id_id
                    from customer_poheadercustomer
                    where customer_poheadercustomer.show_notification = 1 and customer_poheadercustomer.follow_up = %s
                    union
                    select dc_no, date, account_id_id
                    from customer_dcheadercustomer
                    where customer_dcheadercustomer.show_notification = 1 and customer_dcheadercustomer.follow_up = %s
                    ''',[today,today,today,today])
    customer_row = cursor.fetchall()
    total_notification = len(customer_row)

    supplier_row = cursor.execute('''select rfq_no , date, account_id_id
                                from supplier_rfqsupplierheader
                                where supplier_rfqsupplierheader.show_notification = 1 and supplier_rfqsupplierheader.follow_up = %s
                                union
                                select quotation_no, date, account_id_id
                                from supplier_quotationheadersupplier
                                where supplier_quotationheadersupplier.show_notification = 1 and supplier_quotationheadersupplier.follow_up = %s
                                union
                                select po_no, date, account_id_id
                                from supplier_poheadersupplier
                                where supplier_poheadersupplier.show_notification = 1 and supplier_poheadersupplier.follow_up = %s
                                union
                                select dc_no, date, account_id_id
                                from supplier_dcheadersupplier
                                where supplier_dcheadersupplier.show_notification = 1 and supplier_dcheadersupplier.follow_up = %s
                                ''',[today,today,today,today])
    supplier_row = supplier_row.fetchall()
    total_notification_supplier = len(supplier_row)
    return render(request,'supplier/index.html',{'total_notification':total_notification,'total_notification_supplier':total_notification_supplier ,'customer_row':customer_row, 'supplier_row':supplier_row})

def rfq_supplier(request):
    all_rfq = RfqSupplierHeader.objects.all()
    return render(request, 'supplier/rfq_supplier.html',{'all_rfq':all_rfq})

def new_rfq_supplier(request):
    get_last_rfq_no = RfqSupplierHeader.objects.last()
    all_item_code = Add_products.objects.all()
    if get_last_rfq_no:
        get_last_rfq_no = get_last_rfq_no.rfq_no
        get_last_rfq_no = get_last_rfq_no[-3:]
        num = int(get_last_rfq_no)
        num = num + 1
        get_last_rfq_no = 'RFQ/SP/' + str(num)
    else:
        get_last_rfq_no = 'RFQ/SP/101'
    all_accounts = ChartOfAccount.objects.all()
    item_code = request.POST.get('item_code',False)
    if item_code:
        data = Add_products.objects.filter(product_code = item_code)
        for value in data:
            print(value.product_code)
        row = serializers.serialize('json',data)
        return HttpResponse(json.dumps({'row':row}))
    if request.method == 'POST':
        supplier = request.POST.get('supplier',False)
        attn = request.POST.get('attn',False)
        follow_up = request.POST.get('follow_up',False)
        footer_remarks = request.POST.get('footer_remarks',False)
        items = json.loads(request.POST.get('items'))
        try:
            account_id = ChartOfAccount.objects.get(account_title = supplier)
        except ChartOfAccount.DoesNotExist:
            return JsonResponse({"result":"No Account Found "+supplier+""})
        if follow_up:
            follow_up = follow_up
        else:
            follow_up = '2010-10-06'
        date = datetime.date.today()
        rfq_header = RfqSupplierHeader(rfq_no = get_last_rfq_no, date = date , attn = attn, follow_up = follow_up, footer_remarks = footer_remarks ,account_id = account_id)
        rfq_header.save()
        header_id = RfqSupplierHeader.objects.get(rfq_no=get_last_rfq_no)
        for value in items:
            rfq_detail = RfqSupplierDetail(item_code = value["item_code"], item_name = value["item_name"], item_description = value["item_description"],
                                            quantity = value["quantity"], unit = value["unit"], rfq_id = header_id)
            rfq_detail.save()
        return JsonResponse({"result": "success"})
    return render(request,'supplier/new_rfq_supplier.html',{'get_last_rfq_no':get_last_rfq_no, 'all_item_code':all_item_code, 'all_accounts':all_accounts})


def edit_rfq_supplier(request,pk):
    rfq_header = RfqSupplierHeader.objects.filter(id = pk).first()
    rfq_detail = RfqSupplierDetail.objects.filter(rfq_id = pk).all()
    all_item_code = list(Add_products.objects.values('product_code'))
    all_accounts = ChartOfAccount.objects.all()
    try:
        item_code = request.POST.get('item_code',False)
        print(item_code)
        if item_code:
            data = Add_products.objects.filter(product_code = item_code)
            item_code_exist = RfqSupplierDetail.objects.filter(item_code = item_code, rfq_id = pk).first()
            if item_code_exist:
                return HttpResponse(json.dumps({'message':"Item Already Exist"}))
            row = serializers.serialize('json',data)
            return HttpResponse(json.dumps({'row':row}))
        if request.method == 'POST':
            rfq_detail.delete()
            edit_rfq_supplier_name = request.POST.get('edit_rfq_supplier_name',False)
            edit_rfq_attn = request.POST.get('edit_rfq_attn',False)
            edit_rfq_follow_up = request.POST.get('edit_rfq_follow_up',False)
            edit_footer_remarks = request.POST.get('edit_footer_remarks',False)
            try:
                account_id = ChartOfAccount.objects.get(account_title = edit_rfq_supplier_name)
            except ChartOfAccount.DoesNotExist:
                return JsonResponse({"result":"No Account Found "+edit_rfq_supplier_name+""})
            if edit_rfq_follow_up:
                edit_rfq_follow_up = edit_rfq_follow_up
            else:
                edit_rfq_follow_up = '2010-10-06'
            rfq_header.attn = edit_rfq_attn
            rfq_header.follow_up = edit_rfq_follow_up
            rfq_header.account_id = account_id
            rfq_header.footer_remarks = edit_footer_remarks
            rfq_header.save();
            header_id = RfqSupplierHeader.objects.get(id = pk)
            items = json.loads(request.POST.get('items'))
            for value in items:
                rfq_detail_update = RfqSupplierDetail(item_code = value["item_code"], item_name = value["item_name"], item_description = value["item_description"], quantity = value["quantity"], unit = value["unit"], rfq_id = header_id)
                rfq_detail_update.save()
            return JsonResponse({"result":"success"})
    except IntegrityError:
        print("Data Already Exist")
    return render(request,'supplier/edit_rfq_supplier.html',{'rfq_header':rfq_header,'pk':pk,'rfq_detail':rfq_detail, 'all_item_code':all_item_code, 'all_accounts':all_accounts})


def quotation_supplier(request):
    all_quotation = QuotationHeaderSupplier.objects.all()
    return render(request, 'supplier/quotation_supplier.html',{'all_quotation':all_quotation})


def new_quotation_supplier(request):
    get_last_quotation_no = QuotationHeaderSupplier.objects.last()
    all_item_code = Add_products.objects.all()
    all_accounts = ChartOfAccount.objects.all()
    if get_last_quotation_no:
        get_last_quotation_no = get_last_quotation_no.quotation_no
        get_last_quotation_no = get_last_quotation_no[-3:]
        num = int(get_last_quotation_no)
        num = num + 1
        get_last_quotation_no = 'QU/SP/' + str(num)
    else:
        get_last_quotation_no = 'QU/SP/101'
    item_code_quotation = request.POST.get('item_code_quotation',False)
    if item_code_quotation:
        data = Add_products.objects.filter(product_code = item_code_quotation)
        for value in data:
            print(value.product_code)
        row = serializers.serialize('json',data)
        return HttpResponse(json.dumps({'row':row}))
    if request.method == 'POST':
        supplier = request.POST.get('supplier',False)
        attn = request.POST.get('attn',False)
        prcbasis = request.POST.get('prcbasis',False)
        leadtime = request.POST.get('leadtime',False)
        validity = request.POST.get('validity',False)
        payment = request.POST.get('payment',False)
        remarks = request.POST.get('remarks',False)
        currency = request.POST.get('currency',False)
        exchange_rate = request.POST.get('exchange_rate',False)
        follow_up = request.POST.get('follow_up',False)
        footer_remarks = request.POST.get('footer_remarks',False)
        if follow_up:
            follow_up = follow_up
        else:
            follow_up = '2010-10-06'
        try:
            account_id = ChartOfAccount.objects.get(account_title = supplier)
        except ChartOfAccount.DoesNotExist:
            return JsonResponse({"result":"No Account Found "+supplier+""})
        date = datetime.date.today()
        quotation_header = QuotationHeaderSupplier(quotation_no = get_last_quotation_no, date = date, attn = attn, prc_basis = prcbasis,
                                                leadtime = leadtime, validity = validity, payment = payment, remarks = remarks, currency = currency,
                                                exchange_rate = exchange_rate, follow_up = follow_up, show_notification = True, footer_remarks = footer_remarks, account_id = account_id)
        quotation_header.save()
        items = json.loads(request.POST.get('items'))
        header_id = QuotationHeaderSupplier.objects.get(quotation_no = get_last_quotation_no)
        for value in items:
            quotation_detail = QuotationDetailSupplier(item_code = value["item_code"], item_name = value["item_name"], item_description = value["item_description"],
                                            quantity = value["quantity"], unit = value["unit"], unit_price = value["unit_price"], remarks = value["remarks"], quotation_id = header_id)
            quotation_detail.save()
        return JsonResponse({'result':'success'})
    return render(request, 'supplier/new_quotation_supplier.html',{'all_item_code':all_item_code,'get_last_quotation_no':get_last_quotation_no,'all_accounts':all_accounts})


def edit_quotation_supplier(request,pk):
    quotation_header = QuotationHeaderSupplier.objects.filter(id = pk).first()
    quotation_detail = QuotationDetailSupplier.objects.filter(quotation_id = pk).all()
    all_accounts = ChartOfAccount.objects.all()
    print(quotation_detail)
    all_item_code = list(Add_products.objects.values('product_code'))
    item_code = request.POST.get('item_code',False)
    if item_code:
        data = Add_products.objects.filter(product_code = item_code)
        item_code_exist = QuotationDetailSupplier.objects.filter(item_code = item_code, quotation_id = pk).first()
        if item_code_exist:
            return HttpResponse(json.dumps({'message':"Item Already Exist"}))
        row = serializers.serialize('json',data)
        return HttpResponse(json.dumps({'row':row}))
    if request.method == 'POST':
        quotation_detail.delete()
        edit_supplier = request.POST.get('supplier',False)
        edit_quotation_attn = request.POST.get('attn',False)
        edit_quotation_prcbasis = request.POST.get('prcbasis',False)
        edit_quotation_leadtime = request.POST.get('leadtime',False)
        edit_quotation_validity = request.POST.get('validity',False)
        edit_quotation_payment = request.POST.get('payment',False)
        edit_quotation_remarks = request.POST.get('remarks',False)
        edit_quotation_currency_rate = request.POST.get('currency',False)
        edit_quotation_exchange_rate = request.POST.get('exchange_rate',False)
        edit_quotation_follow_up = request.POST.get('follow_up',False)
        edit_footer_remarks = request.POST.get('edit_footer_remarks',False)


        try:
            account_id = ChartOfAccount.objects.get(account_title = edit_supplier)
        except ChartOfAccount.DoesNotExist:
            return JsonResponse({"result":"No Account Found "+edit_supplier+""})

        quotation_header.attn = edit_quotation_attn
        quotation_header.prc_basis = edit_quotation_prcbasis
        quotation_header.leadtime = edit_quotation_leadtime
        quotation_header.validity = edit_quotation_validity
        quotation_header.payment = edit_quotation_payment
        quotation_header.remarks = edit_quotation_remarks
        quotation_header.currency = edit_quotation_currency_rate
        quotation_header.exchange_rate = edit_quotation_exchange_rate
        quotation_header.account_id = account_id
        quotation_header.follow_up = edit_quotation_follow_up
        quotation_header.footer_remarks = edit_footer_remarks
        quotation_header.save();

        header_id = QuotationHeaderSupplier.objects.get(id = pk)
        items = json.loads(request.POST.get('items'))
        print(items)
        for value in items:
            quotation_detail_update = QuotationDetailSupplier(item_code = value["item_code"], item_name = value["item_name"], item_description = value["item_description"], quantity = value["quantity"], unit = value["unit"], unit_price = value["unit_price"], remarks = value["remarks"], quotation_id = header_id)
            quotation_detail_update.save()
        return JsonResponse({"result":"success"})
    return render(request,'supplier/edit_quotation_supplier.html',{'quotation_header':quotation_header,'pk':pk,'quotation_detail':quotation_detail, 'all_item_code':all_item_code, 'all_accounts':all_accounts})


def print_quotation_supplier(request,pk):
    lines = 0
    total_amount = 0
    company_info = Company_info.objects.all()
    image = Company_info.objects.filter(company_name = "Hamza Enterprise").first()
    header = QuotationHeaderSupplier.objects.filter(id = pk).first()
    detail = QuotationDetailSupplier.objects.filter(quotation_id = pk).all()
    for value in detail:
        lines = lines + len(value.item_description.split('\n'))
        amount = float(value.unit_price * value.quantity)
        total_amount = total_amount + amount
    print(total_amount)
    lines = lines + len(detail) + len(detail)
    total_lines = 36 - lines
    pdf = render_to_pdf('supplier/quotation_supplier_pdf.html', {'company_info':company_info,'image':image,'header':header, 'detail':detail,'total_lines':total_lines,'total_amount':total_amount})
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = "Quotation_Supplier_%s.pdf" %("123")
        content = "inline; filename='%s'" %(filename)
        response['Content-Disposition'] = content
        return response
    return HttpResponse("Not found")


def quotation_export_supplier(request):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="QuotationSupplier.xls"'

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Users')

    # Sheet header, first row
    row_num = 0

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    columns = ['Quotation No', 'Date','Attn' ,'Prc Basis', 'Lead Time', 'Validity', 'Payment', 'Remarks', 'Curreny', 'Exchange Rate', 'Follow Up', 'Footer Remarks']


    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)

    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()

    rows = QuotationHeaderSupplier.objects.all().values_list('quotation_no', 'date', 'attn', 'prc_basis', 'leadtime', 'validity', 'payment', 'remarks', 'currency', 'exchange_rate', 'follow_up', 'footer_remarks')
    for row in rows:
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)

    wb.save(response)
    return response

def purchase_order_supplier(request):
    all_po = PoHeaderSupplier.objects.all()
    return render(request, 'supplier/purchase_order_supplier.html',{'all_po':all_po})


def new_purchase_order_supplier(request):
    get_last_po_no = PoHeaderSupplier.objects.last()
    all_item_code = Add_products.objects.all
    all_accounts = ChartOfAccount.objects.all()
    if get_last_po_no:
        get_last_po_no = get_last_po_no.po_no
        get_last_po_no = get_last_po_no[-3:]
        num = int(get_last_po_no)
        num = num + 1
        get_last_po_no = 'PO/SP/' + str(num)
    else:
        get_last_po_no = 'PO/SP/101'
    item_code_po = request.POST.get('item_code_po',False)
    if item_code_po:
        data = Add_products.objects.filter(product_code = item_code_po)
        for value in data:
            print(value.product_code)
        row = serializers.serialize('json',data)
        return HttpResponse(json.dumps({'row':row}))
    if request.method == 'POST':
        supplier = request.POST.get('supplier',False)
        attn = request.POST.get('attn',False)
        prcbasis = request.POST.get('prcbasis',False)
        leadtime = request.POST.get('leadtime',False)
        validity = request.POST.get('validity',False)
        payment = request.POST.get('payment',False)
        remarks = request.POST.get('remarks',False)
        currency = request.POST.get('currency',False)
        exchange_rate = request.POST.get('exchange_rate',False)
        follow_up = request.POST.get('follow_up',False)
        footer_remarks = request.POST.get('footer_remarks',False)
        try:
            account_id = ChartOfAccount.objects.get(account_title = supplier)
        except ChartOfAccount.DoesNotExist:
            return JsonResponse({"result":"No Account Found "+supplier+""})
        date = datetime.date.today()
        po_header = PoHeaderSupplier(po_no = get_last_po_no, date = date, attn = attn, prc_basis = prcbasis,
                                                leadtime = leadtime, validity = validity, payment = payment, remarks = remarks, currency = currency,
                                                exchange_rate = exchange_rate, follow_up = follow_up, show_notification = True, footer_remarks = footer_remarks ,account_id = account_id)
        po_header.save()
        items = json.loads(request.POST.get('items'))
        header_id = PoHeaderSupplier.objects.get(po_no = get_last_po_no)
        for value in items:
            po_detail = PoDetailSupplier(item_code = value["item_code"], item_name = value["item_name"], item_description = value["item_description"],
                                            quantity = value["quantity"], unit = value["unit"], unit_price = value["unit_price"], remarks = value["remarks"], quotation_no = "to be define" ,po_id = header_id)
            po_detail.save()
        return JsonResponse({'result':'success'})
    return render(request, 'supplier/new_purchase_order_supplier.html',{'all_item_code':all_item_code,'get_last_po_no':get_last_po_no, 'all_accounts': all_accounts})


def edit_purchase_order_supplier(request,pk):
    po_header = PoHeaderSupplier.objects.filter(id = pk).first()
    po_detail = PoDetailSupplier.objects.filter(po_id = pk).all()
    all_item_code = list(Add_products.objects.values('product_code'))
    all_accounts = ChartOfAccount.objects.all()
    item_code = request.POST.get('item_code')
    if item_code:
        data = Add_products.objects.filter(product_code = item_code)
        item_code_exist = PoDetailSupplier.objects.filter(item_code = item_code, po_id = pk).first()
        if item_code_exist:
            return HttpResponse(json.dumps({'message':"Item Already Exist"}))
        row = serializers.serialize('json',data)
        return HttpResponse(json.dumps({'row':row}))
    if request.method == 'POST':
        po_detail.delete()
        edit_po_supplier = request.POST.get('supplier',False)
        edit_po_attn = request.POST.get('attn',False)
        edit_po_prcbasis = request.POST.get('prcbasis',False)
        edit_po_leadtime = request.POST.get('leadtime',False)
        edit_po_validity = request.POST.get('validity',False)
        edit_po_payment = request.POST.get('payment',False)
        edit_po_remarks = request.POST.get('remarks',False)
        edit_po_currency_rate = request.POST.get('currency',False)
        edit_po_exchange_rate = request.POST.get('exchange_rate',False)
        edit_po_follow_up = request.POST.get('follow_up',False)
        edit_footer_remarks = request.POST.get('edit_footer_remarks',False)

        try:
            account_id = ChartOfAccount.objects.get(account_title = edit_po_supplier)
        except ChartOfAccount.DoesNotExist:
            return JsonResponse({"result":"No Account Found "+edit_po_supplier+""})

        po_header.attn = edit_po_attn
        po_header.prc_basis = edit_po_prcbasis
        po_header.leadtime = edit_po_leadtime
        po_header.validity = edit_po_validity
        po_header.payment = edit_po_payment
        po_header.remarks = edit_po_remarks
        po_header.currency = edit_po_currency_rate
        po_header.exchange_rate = edit_po_exchange_rate
        po_header.footer_remarks = edit_footer_remarks
        po_header.follow_up = edit_po_follow_up
        po_header.account_id = account_id
        po_header.save();

        header_id = PoHeaderSupplier.objects.get(id = pk)
        items = json.loads(request.POST.get('items'))
        for value in items:
            po_detail_update = PoDetailSupplier(item_code = value["item_code"], item_name = value["item_name"], item_description = value["item_description"], quantity = value["quantity"], unit = value["unit"], unit_price = value["unit_price"], remarks = value["remarks"], po_id = header_id)
            po_detail_update.save()
        return JsonResponse({"result":"success"})
    return render(request,'supplier/edit_purchase_order_supplier.html',{'po_header':po_header,'pk':pk,'po_detail':po_detail, 'all_item_code':all_item_code, 'all_accounts':all_accounts})

def print_po_supplier(request,pk):
    lines = 0
    total_amount = 0
    company_info = Company_info.objects.all()
    image = Company_info.objects.filter(id = 1).first()
    print(image.company_logo)
    header = PoHeaderSupplier.objects.filter(id = pk).first()
    print(header)
    detail = PoDetailSupplier.objects.filter(po_id = pk).all()
    for value in detail:
        lines = lines + len(value.item_description.split('\n'))
        amount = float(value.unit_price * value.quantity)
        total_amount = total_amount + amount
    print(total_amount)
    lines = lines + len(detail) + len(detail)
    total_lines = 40 - lines
    pdf = render_to_pdf('supplier/po_supplier_pdf.html', {'company_info':company_info,'image':image,'header':header, 'detail':detail,'total_lines':total_lines,'total_amount':total_amount})
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = "Po_Supplier_%s.pdf" %(header.po_no)
        content = "inline; filename='%s'" %(filename)
        response['Content-Disposition'] = content
        return response
    return HttpResponse("Not found")


def delivery_challan_supplier(request):
    all_dc = DcHeaderSupplier.objects.all()
    return render(request, 'supplier/delivery_challan_supplier.html',{'all_dc':all_dc})


def new_delivery_challan_supplier(request):
    all_item_code = Add_products.objects.all()
    get_last_dc_no = DcHeaderSupplier.objects.last()
    all_accounts = ChartOfAccount.objects.all()
    if get_last_dc_no:
        get_last_dc_no = get_last_dc_no.dc_no
        get_last_dc_no = get_last_dc_no[-3:]
        num = int(get_last_dc_no)
        num = num + 1
        get_last_dc_no = 'DC/SP/' + str(num)
    else:
        get_last_dc_no = 'DC/SP/101'
    item_code_dc = request.POST.get('item_code_dc',False)
    if item_code_dc:
        item_code_dc = item_code_dc[:12]
        data = Add_products.objects.filter(product_code = item_code_dc)
        for value in data:
            print(value.product_code)
        row = serializers.serialize('json',data)
        return HttpResponse(json.dumps({'row':row}))
    if request.method == 'POST':
        dc_supplier = request.POST.get('supplier')
        footer_remarks = request.POST.get('footer_remarks')
        follow_up = request.POST.get('follow_up')
        try:
            account_id = ChartOfAccount.objects.get(account_title = dc_supplier)
        except ChartOfAccount.DoesNotExist:
            return JsonResponse({"result":"No Account Found "+dc_supplier+""})
        date = datetime.date.today()
        dc_header = DcHeaderSupplier(dc_no = get_last_dc_no, date = date, footer_remarks = footer_remarks, follow_up = follow_up ,account_id = account_id)
        dc_header.save()
        items = json.loads(request.POST.get('items'))
        header_id = DcHeaderSupplier.objects.get(dc_no = get_last_dc_no)
        for value in items:
            dc_detail = DcDetailSupplier(item_code = value["item_code"], item_name = value["item_name"], item_description = value["item_description"],
                                            quantity = value["quantity"],accepted_quantity = 0, returned_quantity = 0,  unit = value["unit"], unit_price = value["unit_price"], remarks = value["remarks"], po_no = "to be define" ,dc_id = header_id)
            dc_detail.save()
        return JsonResponse({'result':'success'})
    return render(request, 'supplier/new_delivery_challan_supplier.html',{'all_item_code':all_item_code,'get_last_dc_no':get_last_dc_no,'all_accounts':all_accounts})


def edit_delivery_challan_supplier(request,pk):
    dc_header = DcHeaderSupplier.objects.filter(id = pk).first()
    dc_detail = DcDetailSupplier.objects.filter(dc_id = pk).all()
    all_accounts = ChartOfAccount.objects.all()
    all_item_code = list(Add_products.objects.values('product_code'))
    item_code = request.POST.get('item_code')
    if item_code:
        data = Add_products.objects.filter(product_code = item_code)
        item_code_exist = DcDetailSupplier.objects.filter(item_code = item_code, dc_id = pk).first()
        if item_code_exist:
            return HttpResponse(json.dumps({'message':"Item Already Exist"}))
        row = serializers.serialize('json',data)
        return HttpResponse(json.dumps({'row':row}))
    if request.method == 'POST':
        dc_detail.delete()
        dc_supplier = request.POST.get('supplier')
        follow_up = request.POST.get('follow_up')
        edit_footer_remarks = request.POST.get('edit_footer_remarks')
        try:
            account_id = ChartOfAccount.objects.get(account_title = dc_supplier)
        except ChartOfAccount.DoesNotExist:
            return JsonResponse({"result":"No Account Found "+dc_supplier+""})
        print(edit_footer_remarks)
        dc_header.account_id = account_id
        dc_header.follow_up = follow_up
        dc_header.footer_remarks = edit_footer_remarks
        dc_header.save()
        header_id = DcHeaderSupplier.objects.get(id = pk)
        items = json.loads(request.POST.get('items'))
        for value in items:
            dc_detail_update = DcDetailSupplier(item_code = value["item_code"], item_name = value["item_name"], item_description = value["item_description"], quantity = value["quantity"],accepted_quantity = 0, returned_quantity = 0, unit = value["unit"], unit_price = value["unit_price"], remarks = value["remarks"], dc_id = header_id)
            dc_detail_update.save()
        return JsonResponse({"result":"success"})
    return render(request,'supplier/edit_delivery_challan_supplier.html',{'dc_header':dc_header,'pk':pk,'dc_detail':dc_detail, 'all_item_code':all_item_code, 'all_accounts':all_accounts})


def print_dc_supplier(request,pk):
    lines = 0
    company_info = Company_info.objects.all()
    image = Company_info.objects.filter(company_name = "Hamza Enterprise").first()
    header = DcHeaderSupplier.objects.filter(id = pk).first()
    detail = DcDetailSupplier.objects.filter(dc_id = pk).all()
    for value in detail:
        lines = lines + len(value.item_description.split('\n'))
    lines = lines + len(detail) + len(detail)
    total_lines = 40 - lines
    pdf = render_to_pdf('supplier/dc_supplier_pdf.html', {'company_info':company_info,'image':image,'header':header, 'detail':detail,'total_lines':total_lines})
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = "Po_Supplier_%s.pdf" %(header.dc_no)
        content = "inline; filename='%s'" %(filename)
        response['Content-Disposition'] = content
        return response
    return HttpResponse("Not found")



def mrn_supplier(request):
    all_dc = DcHeaderSupplier.objects.all()
    return render(request, 'supplier/mrn_supplier.html',{'all_dc':all_dc})


def edit_mrn_supplier(request,pk):
    dc_header = DcHeaderSupplier.objects.filter(id=pk).first()
    dc_detail = DcDetailSupplier.objects.filter(dc_id=pk).all()
    if request.method == 'POST':
        follow_up = request.POST.get('follow_up', False)
        dc_header.follow_up = follow_up
        dc_header.save()
        items = json.loads(request.POST.get('items'))
        for i,value in enumerate(dc_detail):
            value.accepted_quantity = items[i]["accepted_quantity"]
            value.save()
        return JsonResponse({"result":"success"})
    return render(request, 'supplier/edit_mrn_supplier.html',{'dc_header':dc_header,'dc_detail':dc_detail,'pk':pk})


def show_notification(request):
    eventId = request.POST.get('eventId', False)
    if eventId:
        if eventId[:2] == "DC":
            account_info = DcHeaderCustomer.objects.filter(dc_no = eventId).first()
            tran_no = account_info.dc_no
            account_title = account_info.account_id.account_title
            return JsonResponse({'account_title':account_title, 'tran_no': tran_no})
        elif eventId[:2] == "PO":
            account_info = PoHeaderCustomer.objects.filter(po_no = eventId).first()
            tran_no = account_info.po_no
            account_title = account_info.account_id.account_title
            return JsonResponse({'account_title':account_title, 'tran_no': tran_no})
        elif eventId[:2] == "QU":
            account_info = QuotationHeaderCustomer.objects.filter(quotation_no = eventId).first()
            tran_no = account_info.quotation_no
            account_title = account_info.account_id.account_title
            return JsonResponse({'account_title':account_title, 'tran_no': tran_no})
        elif eventId[:2] == "RF":
            account_info = RfqCustomerHeader.objects.filter(rfq_no = eventId).first()
            tran_no = account_info.rfq_no
            account_title = account_info.account_id.account_title
            return JsonResponse({'account_title':account_title, 'tran_no': tran_no})
    return render(request, 'supplier/index.html')

def update_notification_customer(request):
    if request.method == "POST":
        postpone_customer = request.POST.get("postpone_customer",False)
        turn_off = request.POST.get("turn_off",False)
        if turn_off:
            turn_off = turn_off
        else:
            turn_off = 1
        if postpone_customer:
            postpone_customer = postpone_customer
        else:
            postpone_customer = datetime.date.today()
        print(postpone_customer)
        tran_no = request.POST.get("tran_no", False)
        if tran_no[:2] == "DC":
            update_dc = DcHeaderCustomer.objects.filter(dc_no = tran_no).first()
            update_dc.follow_up = postpone_customer
            update_dc.show_notification = turn_off
            update_dc.save()
            return redirect('home')
        elif tran_no[:2] == "PO":
            update_po = PoHeaderCustomer.objects.filter(po_no = tran_no).first()
            update_po.follow_up = postpone_customer
            update_po.show_notification = turn_off
            update_po.save()
            return redirect('home')
        elif tran_no[:2] == "QU":
            update_qu = QuotationHeaderCustomer.objects.filter(quotation_no = tran_no).first()
            update_qu.follow_up = postpone_customer
            update_qu.show_notification = turn_off
            update_qu.save()
            return redirect('home')
        elif tran_no[:2] == "RF":
            update_rfq = RfqCustomerHeader.objects.filter(rfq_no = tran_no).first()
            update_rfq.follow_up = postpone_customer
            update_rfq.show_notification = turn_off
            update_rfq.save()
            return redirect('home')
    return redirect('home')


def show_notification_supplier(request):
    eventId = request.POST.get('eventId', False)
    if eventId:
        if eventId[:2] == "DC":
            account_info = DcHeaderSupplier.objects.filter(dc_no = eventId).first()
            tran_no = account_info.dc_no
            account_title = account_info.account_id.account_title
            return JsonResponse({'account_title':account_title, 'tran_no': tran_no})
        elif eventId[:2] == "PO":
            account_info = PoHeaderSupplier.objects.filter(po_no = eventId).first()
            tran_no = account_info.po_no
            account_title = account_info.account_id.account_title
            return JsonResponse({'account_title':account_title, 'tran_no': tran_no})
        elif eventId[:2] == "QU":
            account_info = QuotationHeaderSupplier.objects.filter(quotation_no = eventId).first()
            tran_no = account_info.quotation_no
            account_title = account_info.account_id.account_title
            return JsonResponse({'account_title':account_title, 'tran_no': tran_no})
        elif eventId[:2] == "RF":
            account_info = RfqSupplierHeader.objects.filter(rfq_no = eventId).first()
            tran_no = account_info.rfq_no
            account_title = account_info.account_id.account_title
            return JsonResponse({'account_title':account_title, 'tran_no': tran_no})
    return render(request, 'supplier/index.html')

def update_notification_supplier(request):
    if request.method == "POST":
        postpone_supplier = request.POST.get("postpone_supplier",False)
        turn_off = request.POST.get("turn_off",False)
        if turn_off:
            turn_off = turn_off
        else:
            turn_off = 1
        if postpone_supplier:
            postpone_supplier = postpone_supplier
        else:
            postpone_supplier = datetime.date.today()
        print(postpone_supplier)
        tran_no = request.POST.get("tran_no", False)
        print(tran_no)
        if tran_no[:2] == "DC":
            update_dc = DcHeaderSupplier.objects.filter(dc_no = tran_no).first()
            update_dc.follow_up = postpone_supplier
            update_dc.show_notification = turn_off
            update_dc.save()
            return redirect('home')
        elif tran_no[:2] == "PO":
            update_po = PoHeaderSupplier.objects.filter(po_no = tran_no).first()
            update_po.follow_up = postpone_supplier
            update_po.show_notification = turn_off
            update_po.save()
            return redirect('home')
        elif tran_no[:2] == "QU":
            update_qu = QuotationHeaderSupplier.objects.filter(quotation_no = tran_no).first()
            update_qu.follow_up = postpone_supplier
            update_qu.show_notification = turn_off
            update_qu.save()
            return redirect('home')
        elif tran_no[:2] == "RF":
            update_rfq = RfqSupplierHeader.objects.filter(rfq_no = tran_no).first()
            update_rfq.follow_up = postpone_supplier
            update_rfq.show_notification = turn_off
            update_rfq.save()
            return redirect('home')
    return redirect('home')


def journal_voucher(request):
    account_title = request.POST.get('account_title', False)
    print(account_title)
    return render('transaction/journal_voucher.html')
