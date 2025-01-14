
# Create your views here.
@login_required
def index(request):
    return render(request,'index.html',{'name':'index'})

def no_permission_view(request):
    return render(request, 'no_permission.html')

@login_required
@permission_required_with_redirect('manager.UploadPatientFile',login_url='/no-permission/')
def uploadpatientData(request):
    if request.method == 'POST':
            form = ExcelUploadForm(request.POST, request.FILES)      
            excel_file = request.FILES['my_file']
            df = pd.read_excel(excel_file)
            added_count = 0
            updated_count = 0

            
            for index, row in df.iterrows():
                # Check if the mobile number already exists in the database
                mobile_number = row['Mobile']
                existing_patient = Patient.objects.filter(mobile=mobile_number).first()

                if existing_patient:
                    # If a patient with the same mobile number exists, update the existing record
                    existing_patient.fullname = row['Name']
                    existing_patient.age = row['Age']
                    existing_patient.sufferedcase = row['Case']
                    existing_patient.city = row['City']
                    existing_patient.reservedBy = row['ReservedBy']
                    existing_patient.arrivedOn = row['ArrivedOn']
                    existing_patient.remarks = row['Remarks']
                    existing_patient.expectedDate = row['ArrivalDate']
                    existing_patient.save()
                    updated_count += 1
                else:
                    # If no patient with the same mobile number exists, create a new record
                    Patient.objects.create(
                        fullname=row['Name'],
                        mobile=row['Mobile'],
                        age=row['Age'],
                        sufferedcase=row['Case'],
                        city=row['City'],
                        reservedBy=row['ReservedBy'],
                        arrivedOn=row['ArrivedOn'],
                        remarks=row['Remarks'],
                        expectedDate=row['ArrivalDate']
                        # Map other columns accordingly
                    ) 
                    added_count += 1               
            message = f'Patient data uploaded successfully.<br>{added_count} patients were added.<br>{updated_count} patients were updated.'
            
            
            return render(request,"ConfirmMsg.html",{'message': message,'returnUrl':'upload','btnText':'Upload New File'}, status=200)
   
    return render(request, 'uploadPatientData.html', {'form': 'form'})



   


#This is a block of code
#This is a block of code
#This is a block of code








    


    

