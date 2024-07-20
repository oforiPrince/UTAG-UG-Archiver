import logging
import random
import string
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.hashers import make_password
from django.shortcuts import render
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect
from accounts.models import User
from dashboard.models import Announcement, Document
from utag_ug_archiver.utils.functions import process_bulk_admins, process_bulk_members

from utag_ug_archiver.utils.decorators import MustLogin
# Configure the logger
logger = logging.getLogger(__name__)

#For account management
class AdminListView(PermissionRequiredMixin, View):
    template_name = 'dashboard_pages/admins.html'
    permission_required = 'accounts.view_admin'
    @method_decorator(MustLogin)
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
                announcement_count = Announcement.objects.filter(status='PUBLISHED').exclude(target_groups__name='Members').count()
                new_announcements = Announcement.objects.filter(status='PUBLISHED').exclude(target_groups__name='Members').order_by('-created_at')[:3]
            elif request.user.groups.filter(name='Member').exists():
                announcement_count = Announcement.objects.filter(status='PUBLISHED').exclude(target_groups__name='Executives').count()
                new_announcements = Announcement.objects.filter(status='PUBLISHED').exclude(target_groups__name='Executives').order_by('-created_at')[:3]
        
        # Prepare context
        context = {
            'users': users,
            'total_documents': total_documents,
            'total_external_documents': total_external_documents,
            'new_announcements': new_announcements,
            'announcement_count': announcement_count,
            'has_add_permission': request.user.has_perm('accounts.add_admin'),
            'has_change_permission': request.user.has_perm('accounts.change_admin'),
            'has_delete_permission': request.user.has_perm('accounts.delete_admin'),
        }
        
        # Render the template
        return render(request, self.template_name, context)
    
class AdminCreateView(PermissionRequiredMixin, View):
    permission_required = 'accounts.add_admin'
    
    @method_decorator(MustLogin)
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
            raw_password = ''.join(random.choices(string.ascii_letters + string.digits, k=password_length))
        else:
            raw_password = request.POST.get('password1')

        member_exists = User.objects.filter(email=email).exists()
        if member_exists:
            messages.error(request, 'Admin already exists!')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        try:
            # Create user
            admin = User.objects.create(
                title=title,
                first_name=first_name,
                other_name=other_name,
                last_name=last_name,
                gender=gender,
                email=email,
                phone_number=phone_number,
                department=department,
                password=make_password(raw_password),
                created_by=request.user,
                created_from_dashboard=True,
            )
            
            # Add user to Admin group
            admin.groups.add(Group.objects.get(name='Admin'))
            
            # Save raw password to the instance temporarily
            admin.raw_password = raw_password

            messages.success(request, 'Admin created successfully!')
        except Exception as e:
            logger.error(f"Error creating admin: {e}")
            messages.error(request, 'Error creating admin. Please try again.')
        
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        
class UserUpdateView(PermissionRequiredMixin, View):
    permission_required = 'accounts.change_admin'
    @method_decorator(MustLogin)
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
    
        
class AdminDeleteView(PermissionRequiredMixin, View):
    permission_required = 'accounts.delete_admin'
    @method_decorator(MustLogin)
    def get(self, request, *args, **kwargs):
        admin_id = kwargs.get('admin_id')
        admin = User.objects.get(id=admin_id)
        admin.delete()
        messages.success(request, 'Admin deleted successfully!')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        
class MemberCreateView(PermissionRequiredMixin, View):
    permission_required = 'accounts.add_member'
    password = ""
    @method_decorator(MustLogin)
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
                created_by = request.user,
                created_from_dashboard = True,
            )
            admin.save()
            
            messages.success(request, 'Member created successfully!')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        
class MemberDeleteView(PermissionRequiredMixin, View):
    permission_required = 'accounts.delete_member'
    @method_decorator(MustLogin)
    def get(self, request, *args, **kwargs):
        member_id = kwargs.get('member_id')
        member = User.objects.get(id=member_id)
        member.delete()
        messages.success(request, 'Member deleted successfully!')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        
            

class UploadAdminData(PermissionRequiredMixin, View):
    permission_required = 'accounts.add_admin'
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
        
class UploadMemberData(PermissionRequiredMixin, View):
    permission_required = 'accounts.add_member'
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

class MemberListView(PermissionRequiredMixin, View):
    permission_required = 'accounts.view_member'
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
                announcement_count = Announcement.objects.filter(status='PUBLISHED').exclude(target_groups__name='Member').count()
                new_announcements = Announcement.objects.filter(status='PUBLISHED').exclude(target_groups__name='Member').order_by('-created_at')[:3]
            elif request.user.groups.filter(name='Member').exists():
                announcement_count = Announcement.objects.filter(status='PUBLISHED').exclude(target_groups__name='Executive').count()
                new_announcements = Announcement.objects.filter(status='PUBLISHED').exclude(target_groups__name='Executive').order_by('-created_at')[:3]
        print('has add permission')
        print(request.user.has_perm('accounts.add_member'))
        # Prepare context
        context = {
            'users': users,
            'total_documents': total_documents,
            'total_external_documents': total_external_documents,
            'new_announcements': new_announcements,
            'announcement_count': announcement_count,
            'has_add_permission': request.user.has_perm('accounts.add_member'),
            'has_change_permission': request.user.has_perm('accounts.change_member'),
            'has_delete_permission': request.user.has_perm('accounts.delete_member'),
        }
        
        # Render the template
        return render(request, self.template_name, context)