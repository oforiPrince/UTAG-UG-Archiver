import random
import string
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from django.contrib.auth.hashers import make_password
from django.shortcuts import render
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.http import HttpResponseRedirect
from accounts.models import User
from dashboard.models import Announcement, Document
from utag_ug_archiver.utils.functions import process_bulk_admins, process_bulk_members

from utag_ug_archiver.utils.decorators import MustLogin

#For account management
class AdminListView(View):
    template_name = 'dashboard_pages/admins.html'

    def get(self, request):
        # Fetch users
        users = User.objects.filter(groups__name='Admin').order_by('first_name')
        
        # Fetch document counts
        total_documents = Document.objects.filter(category='internal').count()
        total_external_documents = Document.objects.filter(category='external').count()
        
        # Initialize variables
        new_announcements = []
        announcement_count = 0
        
        # Determine the user's role and fetch relevant data
        if request.user.groups.filter(name='Admin').exists():
            new_announcements = Announcement.objects.filter(status='PUBLISHED').order_by('-created_at')[:3]
            announcement_count = Announcement.objects.filter(status='PUBLISHED').count()
        elif request.user.has_perm('view_announcement'):
            if request.user.groups.filter(name='Executive').exists():
                announcement_count = Announcement.objects.filter(status='PUBLISHED').exclude(target_group='MEMBERS').count()
                new_announcements = Announcement.objects.filter(status='PUBLISHED').exclude(target_group='MEMBERS').order_by('-created_at')[:3]
            elif request.user.groups.filter(name='Member').exists():
                announcement_count = Announcement.objects.filter(status='PUBLISHED').exclude(target_group='EXECUTIVES').count()
                new_announcements = Announcement.objects.filter(status='PUBLISHED').exclude(target_group='EXECUTIVES').order_by('-created_at')[:3]
        
        # Prepare context
        context = {
            'users': users,
            'total_documents': total_documents,
            'total_external_documents': total_external_documents,
            'new_announcements': new_announcements,
            'announcement_count': announcement_count,
        }
        
        # Render the template
        return render(request, self.template_name, context)
    
class AdminCreateView(View):
    password = ""
    def post(self, request):
        title = request.POST.get('title')
        first_name = request.POST.get('first_name')
        other_name = request.POST.get('other_name')
        last_name = request.POST.get('last_name')
        gender = request.POST.get('gender')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        department = request.POST.get('department')
        if request.POST.get('password_choice') == 'auto':
            password_length = 10
            self.password = ''.join(random.choices(string.ascii_letters + string.digits, k=password_length))
        else:
            password = request.POST.get('password1')
            self.password = password
        member_exists = User.objects.filter(email=email).exists()
        if member_exists:
            messages.error(request, 'Admin already exists!')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            admin = User.objects.create(
                title = title,
                first_name = first_name,
                other_name = other_name,
                last_name = last_name,
                gender = gender,
                email = email,
                phone_number = phone_number,
                department = department,
                password = make_password(self.password),
                is_admin = True,
            )
            admin.save()
            
            # Send email to admin with password
            email_subject = 'Account Created'
            from_email = settings.EMAIL_HOST_USER
            to = email
            email_body = render_to_string('emails/account_credentials.html', {'first_name': first_name,'last_name': last_name,'email':email, 'password': self.password})
            email = EmailMessage(
                email_subject,
                email_body,
                from_email,
                [to]
            )
            email.content_subtype = "html"
            email.send()
            
            messages.success(request, 'Admin created successfully!')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        
class UserUpdateView(View):
    def post(self,request):
        id = request.POST.get('user_id')
        title = request.POST.get('title')
        first_name = request.POST.get('first_name')
        other_name = request.POST.get('other_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        is_active = request.POST.get('is_active')
        gender = request.POST.get('gender')
        phone_number = request.POST.get('phone_number')
        department = request.POST.get('department')
        
        user = User.objects.get(id=id)
        if user.email != email:
            user.email = email
        if user.first_name != first_name:
            user.first_name = first_name
            
        if user.other_name != other_name:
            user.other_name = other_name
            
        if user.last_name != last_name:
            user.last_name = last_name
            
        if user.title != title:
            user.title = title
        
        if user.gender != gender:
            user.gender = gender
            
        if user.phone_number != phone_number:
            user.phone_number = phone_number
            
        if user.department != department:
            user.department = department
            
        if user.is_active != is_active:
            user.is_active = is_active
            
        user.save()
        messages.success(request, 'Admin updated successfully!')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        
        
        
class AdminDeleteView(View):
    def get(self, request, *args, **kwargs):
        admin_id = kwargs.get('admin_id')
        admin = User.objects.get(id=admin_id)
        admin.delete()
        messages.success(request, 'Admin deleted successfully!')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        
class MemberCreateView(View):
    password = ""
    def post(self, request):
        title = request.POST.get('title')
        first_name = request.POST.get('first_name')
        other_name = request.POST.get('other_name')
        last_name = request.POST.get('last_name')
        gender = request.POST.get('gender')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        department = request.POST.get('department')
        if request.POST.get('password_choice') == 'auto':
            password_length = 10
            self.password = ''.join(random.choices(string.ascii_letters + string.digits, k=password_length))
        else:
            password = request.POST.get('password1')
            self.password = password
        member_exists = User.objects.filter(email=email).exists()
        if member_exists:
            messages.error(request, 'Member already exists!')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            admin = User.objects.create(
                title = title,
                first_name = first_name,
                other_name = other_name,
                last_name = last_name,
                gender = gender,
                email = email,
                phone_number = phone_number,
                department = department,
                password = make_password(self.password),
                is_member = True,
            )
            admin.save()
            
            # Send email to admin with password
            email_subject = 'Account Created'
            from_email = settings.EMAIL_HOST_USER
            to = email
            email_body = render_to_string('emails/account_credentials.html', {'first_name': first_name,'last_name': last_name,'email':email, 'password': self.password})
            email = EmailMessage(
                email_subject,
                email_body,
                from_email,
                [to]
            )
            email.content_subtype = "html"
            email.send()
            
            messages.success(request, 'Member created successfully!')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        
class MemberDeleteView(View):
    def get(self, request, *args, **kwargs):
        member_id = kwargs.get('member_id')
        member = User.objects.get(id=member_id)
        member.delete()
        messages.success(request, 'Member deleted successfully!')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        
            

class UploadAdminData(View):
    @method_decorator(MustLogin)
    def post(self, request, *args, **kwargs):
        excel_file = request.FILES.get('excel')
        csv_file = request.FILES.get('csv')

        if excel_file:
            return process_bulk_admins(request, excel_file)
        elif csv_file:
            return process_bulk_admins(request, csv_file)
        else:
            messages.error(request, 'No file uploaded.')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        
class UploadMemberData(View):
    @method_decorator(MustLogin)
    def post(self, request, *args, **kwargs):
        excel_file = request.FILES.get('excel')
        csv_file = request.FILES.get('csv')

        if excel_file:
            return process_bulk_members(request, excel_file)
        elif csv_file:
            return process_bulk_members(request, csv_file)
        else:
            messages.error(request, 'No file uploaded.')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

class MemberListView(View):
    template_name = 'dashboard_pages/members.html'
    @method_decorator(MustLogin)
    def get(self, request):
        # Fetch users
        users = User.objects.filter(groups__name='Member').order_by('first_name')
        
        # Fetch document counts
        total_documents = Document.objects.filter(category='internal').count()
        total_external_documents = Document.objects.filter(category='external').count()
        
        # Initialize variables
        new_announcements = []
        announcement_count = 0
        
        # Determine the user's role and fetch relevant data
        if request.user.groups.filter(name='Admin').exists():
            new_announcements = Announcement.objects.filter(status='PUBLISHED').order_by('-created_at')[:3]
            announcement_count = Announcement.objects.filter(status='PUBLISHED').count()
        elif request.user.has_perm('view_announcement'):
            if request.user.groups.filter(name='Executive').exists():
                announcement_count = Announcement.objects.filter(status='PUBLISHED').exclude(target_group='MEMBERS').count()
                new_announcements = Announcement.objects.filter(status='PUBLISHED').exclude(target_group='MEMBERS').order_by('-created_at')[:3]
            elif request.user.groups.filter(name='Member').exists():
                announcement_count = Announcement.objects.filter(status='PUBLISHED').exclude(target_group='EXECUTIVES').count()
                new_announcements = Announcement.objects.filter(status='PUBLISHED').exclude(target_group='EXECUTIVES').order_by('-created_at')[:3]
        
        # Prepare context
        context = {
            'users': users,
            'total_documents': total_documents,
            'total_external_documents': total_external_documents,
            'new_announcements': new_announcements,
            'announcement_count': announcement_count,
        }
        
        # Render the template
        return render(request, self.template_name, context)